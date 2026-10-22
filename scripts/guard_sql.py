#!/usr/bin/env python3
"""PreToolUse hook: let SQL run freely, but ask the owner first when it could
delete or overwrite existing data. Reads the hook JSON on stdin; prints an
"ask" decision when the statement (or a psql command) contains a destructive
keyword. Anything else passes through untouched (exit 0, no output).

Permission rules cannot look inside SQL, so this is the only place that can
tell a harmless CREATE/ALTER ... ADD from a DELETE/DROP/UPDATE.
"""
import json
import re
import sys

DESTRUCTIVE = re.compile(
    r"\b(DELETE\s+FROM|DROP\s+(TABLE|COLUMN|SCHEMA|DATABASE|INDEX|CONSTRAINT|VIEW)|TRUNCATE|"
    r"UPDATE\s+\S+\s+SET|ALTER\s+TABLE\s+\S+\s+(DROP|RENAME)|ALTER\s+COLUMN\s+\S+\s+(TYPE|DROP)|"
    r"DROP\s+OWNED|REVOKE)\b",
    re.IGNORECASE,
)


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return
    tool_input = event.get("tool_input") or {}
    text = json.dumps(tool_input)
    if event.get("tool_name") == "Bash" and not re.search(r"\bpsql\b|DATABASE_URL|postgres(ql)?://", text):
        return
    match = DESTRUCTIVE.search(text)
    if not match:
        return
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": (
                f"SQL contains '{match.group(0)}', which can delete or overwrite existing data. "
                "Owner approval required (CLAUDE.md: existing production data)."
            ),
        }
    }))


if __name__ == "__main__":
    main()
