"""Load and compile CSL policies for runtime enforcement.

Integration: `pre_tool_call` hook calls `check_tool_call(tool_name, args)`.
Returns (allowed, message, policy_name). Message is empty if allowed.
"""

from __future__ import annotations

import logging
import os
import threading
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Policy paths
SKILL_POLICIES_DIR = Path(__file__).parent.parent / "policies"
USER_POLICIES_DIR = Path.home() / ".hermes" / "policies"

# Blocked path patterns checked by runtime (not CSL)
BLOCKED_PREFIXES = {".wrangler", ".next", "dist", "out", "node_modules", "dist.zip"}
BLOCKED_FILES = {"secrets.json", "credentials.json"}
BLOCKED_EXTENSIONS = {".map", ".pem", ".key"}


def _is_blocked_path(path: str) -> bool:
    """Check if a path matches blocked artifact patterns."""
    p = Path(path)
    if p.name in BLOCKED_FILES:
        return True
    if any(path.endswith(ext) for ext in BLOCKED_EXTENSIONS):
        return True
    for prefix in BLOCKED_PREFIXES:
        if f"{prefix}/" in path or path == prefix or path.startswith(f"{prefix}"):
            return True
    return False


def _parse_git_command(command: str) -> tuple[str | None, list[str]]:
    """Parse a terminal command for git operations."""
    cmd_lower = command.lower()
    if "git add " in command or cmd_lower.startswith("git add "):
        action = "git_add"
    elif "git commit " in command or cmd_lower.startswith("git commit "):
        action = "git_commit"
    elif "git push" in command:
        action = "git_push"
    elif "git " in command:
        action = "terminal"
    else:
        return None, []

    paths = []
    tokens = command.split()
    in_subcommand = False
    skip_next = False
    for tok in tokens:
        if tok == "git":
            in_subcommand = True
            continue
        if tok in ("add", "commit", "push", "clone", "fetch", "pull", "checkout", "branch", "status", "diff", "log"):
            in_subcommand = True
            continue
        if in_subcommand and not tok.startswith("-"):
            if tok in ("-m", "-M", "-a", "--all", "-am", "--message"):
                skip_next = True
                continue
            if skip_next:
                skip_next = False
                continue
            if "github.com" in tok or "://" in tok:
                continue
            clean = tok.strip("'").strip('"')
            if clean:
                paths.append(clean)
    return action, paths


class PolicyEngine:
    """Manages loaded CSL guards with hot reload support."""

    def __init__(self):
        self._guards: dict[str, Any] = {}
        self._lock = threading.RLock()
        self._staging_state = "UNKNOWN"  # CLEAN, DIRTY, UNKNOWN
        self._staging_checked = "FALSE"   # TRUE after git status/diff run
        self._pending_git_actions: list[str] = []  # track uncommitted git actions
        self.reload()

    def reload(self) -> dict[str, bool]:
        """Hot-reload all policies. Returns {policy_name: loaded_ok}."""
        from chimera_core import load_guard as _csl_load_guard
        with self._lock:
            results = {}
            for policy_path in _resolve_policies():
                name = policy_path.stem
                try:
                    guard = _csl_load_guard(str(policy_path))
                    self._guards[name] = guard
                    results[name] = True
                    logger.info("Loaded policy: %s", name)
                except Exception as e:
                    results[name] = False
                    logger.error("Failed to load %s: %s", policy_path, e)
            return results

    def check(self, tool_name: str, args: dict[str, Any]) -> tuple[bool, str, str]:
        """Check a tool call against all loaded policies.

        Returns: (allowed, message, triggered_policy)
        - allowed: False if any policy blocks
        - message: block message if not allowed
        - triggered_policy: name of blocking policy
        """
        with self._lock:
            context = self._build_context(tool_name, args)
            if not context:
                return True, "", ""

            for policy_name, guard in self._guards.items():
                try:
                    result = guard.verify(context)
                    if not result.allowed:
                        rule_ids = []
                        if result.triggered_rule_ids:
                            try:
                                rule_ids = list(result.triggered_rule_ids)
                            except Exception:
                                pass
                        msg = "[CSL " + policy_name + "] Blocked: " + ", ".join(rule_ids or ["rule violation"])
                        return False, msg, policy_name
                except Exception as e:
                    # ChimeraError raised on violation when raise_on_block=True
                    err_str = str(e)
                    if "Violation" in err_str:
                        # Extract rule name from: Violation 'rule_name': ...
                        import re
                        m = re.search(r"Violation '([^']+)'", err_str)
                        rule_name = m.group(1) if m else "rule violation"
                        msg = "[CSL " + policy_name + "] Blocked: " + rule_name
                        return False, msg, policy_name
                    # Other error - log and continue
                    logger.debug("Policy %s error: %s", policy_name, e)

            return True, "", ""

    def _build_context(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Build CSL verification context from tool call."""
        context: dict[str, Any] = {}

        if tool_name == "terminal":
            command = args.get("command", "")
            action, paths = _parse_git_command(command)
            if not action:
                return {}

            context["action"] = action

            if action in ("git_add", "git_commit"):
                blocked = any(_is_blocked_path(p) for p in paths)
                self._staging_state = "DIRTY" if blocked else "CLEAN"
                context["staging_state"] = self._staging_state
            elif action == "git_push":
                context["staging_checked"] = self._staging_checked
            else:
                context["staging_checked"] = self._staging_checked

            if "git status" in command or "git diff" in command or "git log" in command:
                self._staging_checked = "TRUE"

        elif tool_name == "cronjob":
            action_arg = args.get("action", "create")
            context["tool"] = "cronjob"
            context["action"] = action_arg
            context["has_prompt"] = "TRUE" if args.get("prompt") else "FALSE"
            context["has_repeat_on_create"] = "TRUE" if args.get("repeat") and action_arg == "create" else "FALSE"
            context["delivery_set"] = "TRUE" if args.get("deliver") else "FALSE"

        elif tool_name == "delegate_task":
            context["tool"] = "delegate_task"
            scope = args.get("goal") or args.get("context")
            context["has_scope"] = "TRUE" if scope else "FALSE"

        elif tool_name == "skill_manage":
            context["tool"] = "skill_manage"
            context["action"] = args.get("action", "create")
            context["has_name"] = args.get("_has_name", "FALSE")
            context["has_description"] = args.get("_has_description", "FALSE")

        elif tool_name in ("write_file", "patch"):
            path = args.get("file_path", args.get("path", ""))
            if _is_blocked_path(path):
                self._staging_state = "DIRTY"
            context["staging_state"] = self._staging_state

        return context

    def list_policies(self) -> list[dict]:
        """Return loaded policy names."""
        with self._lock:
            return [{"name": name} for name in self._guards.keys()]


def _resolve_policies() -> list[Path]:
    """Return ordered list of policy files (user overrides skill defaults)."""
    policies = []
    if SKILL_POLICIES_DIR.exists():
        policies.extend(sorted(SKILL_POLICIES_DIR.glob("*.csl")))
    if USER_POLICIES_DIR.exists():
        for p in sorted(USER_POLICIES_DIR.glob("*.csl")):
            policies = [x for x in policies if x.name != p.name]
            policies.append(p)
    return policies


_engine: PolicyEngine | None = None


def get_engine() -> PolicyEngine:
    global _engine
    if _engine is None:
        _engine = PolicyEngine()
    return _engine


def check_tool_call(tool_name: str, args: dict[str, Any]) -> tuple[bool, str, str]:
    """Shorthand for get_engine().check(). Called by pre_tool_call hook."""
    return get_engine().check(tool_name, args)
