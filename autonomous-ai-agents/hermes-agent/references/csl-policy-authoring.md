# CSL Policy Authoring — Patterns & Pitfalls

## Package

- `pip install csl-core` → imports as `from chimera_core import load_guard`
- CLI: `.venv/bin/python3 -m chimera_core.cli verify <file.csl>`
- Python: `from chimera_core import load_guard; guard = load_guard('policy.csl')`

## Verified Working Policy Template

```csl
CONFIG {
  ENFORCEMENT_MODE: BLOCK
}

DOMAIN safety {
  ACTION push_git CHECKS git_staging_state {
    WHEN staging_check == "clean" MUST BE TRUE
  }
}

DOMAIN agent-behavior {
  ACTION cronjob_create {
    WHEN cronjob_prompt_set == TRUE
      MUST BE TRUE
    WHEN cronjob_has_repeat == TRUE
      MUST BE FALSE
  }
}
```

## CSL Syntax Rules

- **Constraint format**: `WHEN <condition> <operator> <value>` — all on ONE line
- **MUST BE / MUST NOT BE** — uppercase, no contractions, no regex
- **Variables are strings** unless explicitly typed (string literals in constraints must be quoted: `"clean"`)
- **One constraint per WHEN clause** — chain multiple conditions by stacking WHEN blocks with the same CHECKS action
- **No CONSTANTS block** — inline string literals, or set variables at context-building time in Python
- **ENFORCEMENT_MODE values**: `BLOCK`, `WARN`, `LOG` — NOT `ADVISORY`
- **Each domain is independent** — cross-domain reasoning requires Python-level state machine (CSL has no shared state between domains)

## Common Errors

### "domain has no attribute"
```
DOMAIN myguard {
  ACTION my_action CHECKS my_context {
    WHEN x > 0 MUST BE TRUE   // ← ERROR: "myguard has no attribute 'x'"
  }
}
```
**Fix**: The variable must exist in the `CHECKS <context>` struct, not just in the constraint. The context struct is what you build in Python via `_build_context()`.

### "Only one constraint per WHEN clause"
```
WHEN repo == "allowed" MUST BE TRUE
WHEN path_is_blocked == "true" MUST BE TRUE
```
**Fix**: Separate into multiple WHEN clauses, or chain as separate ACTION entries:
```
ACTION git_add CHECKS git_add_context {
  WHEN repo == "allowed" MUST BE TRUE
}
ACTION git_add CHECKS blocked_path_context {
  WHEN path_is_blocked == "true" MUST BE TRUE
}
```

### Variables not evaluated (guard returns allow on blocked input)
- The Z3 constraint solver may not evaluate all domains depending on how `guard.verify()` is called
- Always test with `guard.verify(context)` and print `result.allowed` and `result.reasons`
- If a domain evaluates but others don't, check the context struct has all required fields

## Python Integration Pattern

```python
from chimera_core import load_guard

class PolicyEngine:
    def __init__(self):
        self._guard = load_guard('policies/safety.csl')
        self._staging_state = "unknown"  # track externally

    def check_tool_call(self, tool_name, args):
        ctx = self._build_context(tool_name, args)
        result = self._guard.verify(ctx)
        if result.allowed:
            return (True, None, None)
        return (False, result.reasons[0], self._policy_name)

    def _build_context(self, tool_name, args):
        ctx = {"tool_name": tool_name, "args": args}
        if tool_name == "terminal":
            cmd = args.get("command", "")
            if cmd.startswith("git push"):
                ctx["staging_check"] = self._staging_state
                ctx["staging_check_reason"] = f"pre-push check: {self._staging_state}"
        return ctx
```

## Verifying All Policies

```bash
cd /home/thomas/Desktop/hermes-agent
.venv/bin/python3 -m chimera_core.cli verify skills/csl-policy/policies/safety.csl
.venv/bin/python3 -m chimera_core.cli verify skills/csl-policy/policies/agent-behavior.csl
.venv/bin/python3 -m chimera_core.cli verify skills/csl-policy/policies/workflow.csl
```

All must exit 0.

## Runtime Testing

```python
import sys
sys.path.insert(0, 'skills/csl-policy/scripts')
from load_guard import get_engine

engine = get_engine()
allowed, msg, policy = engine.check_tool_call("terminal", {"command": "git add .wrangler/"})
print(f"allowed={allowed} msg={msg} policy={policy}")

# Reset staging for push test
engine._staging_check_done = False
allowed, msg, policy = engine.check_tool_call("terminal", {"command": "git push"})
print(f"allowed={allowed} msg={msg} policy={policy}")
```

## Where CSL Policies Live

- Shipped with skill: `skills/csl-policy/policies/*.csl`
- User overrides: `~/.hermes/policies/*.csl`
- Load order: user overrides win (hot-reloadable via `engine.reload()`)
