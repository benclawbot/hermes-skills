#!/usr/bin/env python3
"""
Probe an LLM tool-call harness repair layer for failure modes.

Usage:
    # Default 44-case probe against Hermes' _repair_tool_call_arguments
    python scripts/probe_repair_layer.py

    # Probe a custom function (any codebase)
    python scripts/probe_repair_layer.py --module my_agent.repair

    # Custom cases from a JSON file
    python scripts/probe_repair_layer.py --cases my_cases.json

The probe prints ✓ / ✗ for each case plus a tier-1 finding summary
at the end. Tier 1 = "the result is silently corrupted" or "the
result will crash downstream dispatch". Tier 2 = "data is lost but
session stays alive". Tier 3 = "the result is wrong but the last-
resort {} fallback already saves the session".

A real audit is done when every finding has a tier and Tier 1 cases
are either fixed or explicitly deferred with a written reason.

Module path note (2026-06-03): as of mid-2026, the repair function
lives in `agent.message_sanitization`, not `run_agent`. Older checkouts
may still expose it via `run_agent`; pass `--module run_agent` if so.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from dataclasses import dataclass, field


# ── Default 44-case probe grid ────────────────────────────────────────────
# Each case: (description, raw_input, tier, expected_outcome)
#   tier 1: silent corruption or hard provider rejection
#   tier 2: data loss without telemetry
#   tier 3: result is wrong but last-resort {} keeps session alive
#
# "expected_outcome" is a loose check — the probe accepts ANY valid
# JSON parse unless the tier says we expect a specific shape.
#
# Cases 1-16: Pass 2 audit (modes #1-#8: outer-envelope + numeric precision)
# Cases 17-32: Pass 3 audit (modes #9-#15: text-noise extraction + sentinels)
# Cases 33-44: Pass 4 audit (modes #16-#17: concatenated payloads + trailing garbage)

DEFAULT_CASES: list[tuple[str, str, int, str]] = [
    # ── Pass 2: outer-envelope + numeric-precision failures ────────────
    # Outer-envelope failures
    ("1. top-level array wrapping",            '[{"a": 1}]',                                       1, "dict"),
    ("2. result envelope wrapping",            '{"result": {"a": 1}}',                             1, "dict"),
    ("3. JSONP wrapper",                       'callback({"a": 1})',                                3, "any"),
    # Invalid JSON literals
    ("4. NaN literal",                         '{"x": NaN}',                                        1, "no NaN"),
    ("5. positive Infinity literal",           '{"x": Infinity}',                                   1, "no Infinity"),
    # Python-style JSON
    ("6. single-quote (Python style)",         "{'a': 1}",                                          3, "any"),
    ("7. Python True/False",                   '{"x": True, "y": False}',                           3, "any"),
    # Missing quotes / structure
    ("8. unquoted string value",               '{"a": hello}',                                      3, "any"),
    ("9. JSON5 comment",                       '{"a": 1, /* x */ "b": 2}',                         2, "any"),
    # Other
    ("10. duplicate keys (Python last-wins)",  '{"a": 1, "a": 2}',                                  3, "any"),
    ("11. truncated enum value mid-string",    '{"color": "re',                                     2, "any"),
    ("12. JS-style unquoted key",              '{a: 1, b: 2}',                                      3, "any"),
    ("13. hex numeric",                        '{"x": 0xFF}',                                       3, "any"),
    ("14. trailing semicolon",                 '{"a": 1};',                                         3, "any"),
    ("15. multi top-level objects",            '{"a": 1}{\"b\": 2}',                                  1, "any"),
    ("15a. concatenated split (3 objects)",     '{"a": 1}{\"b\": 2}{\"c\": 3}',                            1, "any"),
    ("15b. concatenated split (whitespace)",   '{"a": 1}  \n\t  {\"b\": 2}',                             1, "any"),
    ("15c. partial tail (don't split)",        '{"a": 1}{\"b\":',                                      2, "any"),
    ("16. mixed-quote in string",              '{"msg": "he said \'hi\'"}',                         3, "any"),

    # ── Pass 4: concatenated payloads + trailing garbage (modes #16, #17) ────
    ("33. trailing garbage after valid JSON",  '{"a": 1}garbage',                                    1, "any"),
    ("34. trailing quoted string",             '{"a": 1}"excess"',                                   1, "any"),
    ("35. trailing boolean/null",              '{"a": 1} true',                                      1, "any"),
    ("36. U+2028 line separator",              '{"a": 1}\u2028{"b": 2}',                             1, "any"),
    ("37. BOM at start",                       '\ufeff{"a": 1}',                                      1, "any"),
    ("38. BOM at end",                         '{"a": 1}\ufeff',                                      1, "any"),
    ("39. paragraph separator U+2029 + text",   '{"a": 1}\u2029trailing',                             1, "any"),
    ("40. leading non-breaking space",         '\u00a0{"a": 1}',                                     1, "any"),
    ("41. preamble text",                      'Here is the JSON: {"a": 1}',                         1, "any"),
    ("42. postscript text",                    '{"a": 1} Hope this helps!',                          1, "any"),
    ("43. nested object extraction",           'noise {"outer": {"inner": 42}}',                      1, "any"),
    ("44. partial dict (don't extract)",       '{"a":',                                              2, "any"),

    # ── Pass 3: text-noise extraction + string-sentinel coercion ───────
    # Reasoning block leak (modes #9)
    ("17. reasoning block leak (full)",        '<think>Let me think...\nThe user wants write_file.\n</think>\n{"path": "/tmp/x"}',  1, "any"),
    ("18. reasoning block compact",            '<think>reasoning here</think>{"a": 1}',            1, "any"),
    # Markdown code-fence wrapping (mode #10)
    ("19. markdown code fence (with lang)",    '```json\n{"path": "/tmp/x"}\n```',                   1, "any"),
    ("20. markdown code fence (no lang)",      '```\n{"a": 1}\n```',                                 1, "any"),
    # Preamble / postscript (mode #11)
    ("21. preamble text",                      'Here is the JSON:\n{"a": 1}\nHope this helps!',   1, "any"),
    ("22. preamble + postscript",              'Sure, here you go: {"a": 1} Done!',                 1, "any"),
    ("23. worst case (all four stacked)",      '<think>think</think>\nSure, here: {"a": 1} Done!',  1, "any"),
    # tool_call envelope (mode #12)
    ("24. tool_call envelope with newlines",   '<tool_call>\n{"name": "end_call", "arguments": {}}\n</tool_call>',  2, "any"),
    ("25. tool_call envelope compact",         '<tool_call>{"a": 1}</tool_call>',                   2, "any"),
    # Extraction correctness
    ("26. nested object extraction",           'preamble {"outer": {"inner": "value"}} postamble', 1, "any"),
    ("27. array extraction",                   'arr [{"a": 1}, {"b": 2}] end',                      1, "any"),
    ("28. string containing closing brace",    '{"a": 1, "b": "string with } in it"}',             1, "any"),
    # False-positive regression protection
    ("29. unquoted-word false positive",       'the user said "use {curly} braces" {"actual": 1}',  1, "any"),
    # Pure-noise fallback
    ("30. no JSON at all",                     "no json here, just text",                           3, "any"),
    # Regression: clean JSON must pass through unchanged
    ("31. already-valid JSON unchanged",       '{"a": 1, "b": 2}',                                  1, "any"),
    # Extract + structural repair composed
    ("32. extract then repair trailing comma", '<think>hmm</think>\n```json\n{"a": 1,}\n```',       1, "any"),
]


@dataclass
class ProbeResult:
    description: str
    raw: str
    tier: int
    result: str
    outcome: str  # "ok" | "tier1_fail" | "tier2_fail" | "tier3_fail" | "unparseable"
    notes: str = ""


@dataclass
class ProbeReport:
    results: list[ProbeResult] = field(default_factory=list)

    def tier1_failures(self) -> list[ProbeResult]:
        return [r for r in self.results if r.outcome == "tier1_fail"]

    def tier2_failures(self) -> list[ProbeResult]:
        return [r for r in self.results if r.outcome == "tier2_fail"]

    def print(self) -> None:
        print()
        print("─" * 78)
        for r in self.results:
            status = {
                "ok": "✓",
                "tier1_fail": "✗T1",
                "tier2_fail": "✗T2",
                "tier3_fail": "·  ",
                "unparseable": "?  ",
            }.get(r.outcome, "?  ")
            print(f"  {status} [{r.tier}] {r.description:45s} → {r.result!r}")
            if r.notes:
                print(f"        {r.notes}")
        print("─" * 78)
        t1 = len(self.tier1_failures())
        t2 = len(self.tier2_failures())
        if t1:
            print(f"  TIER 1 FAILURES: {t1} — must fix before declaring audit done")
        if t2:
            print(f"  Tier 2 failures: {t2} — fix this week or write a backlog note")
        if not t1 and not t2:
            print("  Audit closed: no Tier 1 or Tier 2 failures outstanding.")
        print()

    def summary(self) -> str:
        """One-line human summary for log output."""
        t1 = len(self.tier1_failures())
        t2 = len(self.tier2_failures())
        t3 = sum(1 for r in self.results if r.outcome == "tier3_fail")
        ok = sum(1 for r in self.results if r.outcome == "ok")
        return f"probe: {ok}/{len(self.results)} ok, {t1} T1, {t2} T2, {t3} T3"


# ── Outcome classification ───────────────────────────────────────────────


def _is_safe_json(result: str) -> bool:
    """Result must parse strictly (no NaN/Inf in the wire form)."""
    try:
        json.loads(result)
        return True
    except (json.JSONDecodeError, TypeError, ValueError):
        return False


def _is_no_nan(result: str) -> bool:
    """Result must not contain NaN/Infinity literals."""
    return not any(tok in result for tok in ("NaN", "Infinity", "-Infinity"))


def _matches_shape(result: str, expected: str) -> tuple[bool, str]:
    """Check the result against the expected outcome class."""
    try:
        parsed = json.loads(result, strict=False)
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        return False, f"unparseable: {e}"

    if expected in ("no NaN", "no Infinity"):
        if not _is_no_nan(result):
            return False, "result contains NaN/Infinity literal"
        return True, ""
    if expected == "dict":
        if not isinstance(parsed, dict):
            return False, f"expected dict, got {type(parsed).__name__}"
        return True, ""
    if expected == "any":
        return True, ""
    return True, ""


def classify(result: str, tier: int, expected: str) -> tuple[str, str]:
    """Return (outcome, notes) for a probe result."""
    if not _is_safe_json(result):
        return "unparseable", "output is not valid JSON"
    ok, notes = _matches_shape(result, expected)
    if not ok:
        if tier == 1:
            return "tier1_fail", notes
        if tier == 2:
            return "tier2_fail", notes
        return "tier3_fail", notes
    return "ok", ""


# ── Probe driver ────────────────────────────────────────────────────────


def run_probe(
    repair_fn,
    cases: list[tuple[str, str, int, str]] | None = None,
    tool_name: str = "probe",
) -> ProbeReport:
    """Run the full probe grid against a repair function.

    Args:
        repair_fn: callable ``(raw: str, tool_name: str) -> str``
        cases: optional override of the default 44-case grid
        tool_name: passed through to repair_fn for log context

    Returns a ProbeReport with classified results.
    """
    grid = cases or DEFAULT_CASES
    report = ProbeReport()
    for desc, raw, tier, expected in grid:
        try:
            result = repair_fn(raw, tool_name)
        except Exception as e:
            result = f"<EXC {type(e).__name__}: {e}>"
        outcome, notes = classify(result, tier, expected)
        report.results.append(
            ProbeResult(
                description=desc,
                raw=raw,
                tier=tier,
                result=result,
                outcome=outcome,
                notes=notes,
            )
        )
    return report


# ── CLI ──────────────────────────────────────────────────────────────────


def _import_repair_fn(module_path: str) -> object:
    """Import ``module_path`` and return its ``_repair_tool_call_arguments``
    (or fall back to a ``repair`` attribute) for probing.
    """
    mod = importlib.import_module(module_path)
    for attr in ("_repair_tool_call_arguments", "repair_tool_call_arguments", "repair"):
        if hasattr(mod, attr):
            return getattr(mod, attr)
    raise SystemExit(
        f"Module {module_path!r} has no repair function "
        f"(looked for _repair_tool_call_arguments, repair_tool_call_arguments, repair)"
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument(
        "--module",
        default="agent.message_sanitization",
        help="Python module containing the repair function. "
             "Default: agent.message_sanitization (Hermes' repair lives there as of mid-2026). "
             "Earlier versions exposed it via run_agent; if you're on a pre-2026 checkout, pass "
             "--module run_agent instead. Pass any other harness module to probe a custom install.",
    )
    p.add_argument(
        "--cases",
        default=None,
        help="Path to a JSON file with custom cases. Schema: "
             "[{description, raw, tier, expected}]",
    )
    p.add_argument(
        "--tool-name",
        default="probe",
        help="tool_name passed through to the repair function",
    )
    args = p.parse_args()

    if args.cases:
        with open(args.cases) as f:
            raw_cases = json.load(f)
        cases = [(c["description"], c["raw"], c["tier"], c["expected"]) for c in raw_cases]
    else:
        cases = None

    repair_fn = _import_repair_fn(args.module)
    report = run_probe(repair_fn, cases, tool_name=args.tool_name)
    report.print()
    print(report.summary())

    # Exit nonzero if any Tier 1 failures remain — useful in CI.
    return 1 if report.tier1_failures() else 0


if __name__ == "__main__":
    sys.exit(main())
