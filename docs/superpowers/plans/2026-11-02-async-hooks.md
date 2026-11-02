# Asynchronous Hooks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop waiting for the three post-edit hooks by configuring them to run asynchronously.

**Architecture:** Change only `.claude/settings.json`, adding `async: true` to each existing hook command. Preserve matchers, commands, timeouts, and status messages.

**Tech Stack:** JSON; Claude Code hook settings.

---

### Task 1: Configure all post-edit hooks as asynchronous

**Files:**
- Modify: `.claude/settings.json`

- [ ] **Step 1: Verify the current setting does not yet satisfy the requirement**

Run from the repository root:

```powershell
python -c "import json; d=json.load(open('.claude/settings.json', encoding='utf-8')); hooks=[h for group in d['hooks']['PostToolUse'] for h in group['hooks']]; assert len(hooks) == 3 and all(h.get('async') is True for h in hooks); print('3 hooks are async')"
```

Expected: FAIL with `AssertionError`, because none of the three hooks currently has `async: true`.

- [ ] **Step 2: Add `async: true` to each existing hook**

In `.claude/settings.json`, add `"async": true` to each of the three hook objects, preserving the existing command, timeout, and status message. For example:

```json
{
  "type": "command",
  "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/sync_copilot_instructions.py\"",
  "timeout": 30,
  "statusMessage": "CLAUDE.md を copilot-instructions.md に同期しています",
  "async": true
}
```

- [ ] **Step 3: Verify JSON and all three async settings**

Run from the repository root:

```powershell
python -c "import json; d=json.load(open('.claude/settings.json', encoding='utf-8')); hooks=[h for group in d['hooks']['PostToolUse'] for h in group['hooks']]; assert len(hooks) == 3 and all(h.get('async') is True for h in hooks); print('3 hooks are async')"
```

Expected: `3 hooks are async`.

- [ ] **Step 4: Review the exact diff**

Run:

```powershell
git diff --check; git --no-pager diff -- .claude/settings.json
```

Expected: no whitespace errors, and only three `"async": true` additions.
