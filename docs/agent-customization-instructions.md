# Agent Customization — Instructions (draft)

## Purpose
Provide a concise, repo-scoped instructions file used to customize AI assistant behavior when working in this repository.

## Scope
- Applies repository-wide by default. If a rule should be narrower, set `scope` per-rule to target specific files or folders (for example `src/`, `charts/`, or `dashboard/`).

## Extracted preferences from conversation
- Concise, direct, friendly tone.
- Use `manage_todo_list` for multi-step tasks and track progress.
- Send a short preamble before making automated tool calls.
- Use `apply_patch` for file edits and avoid unrelated changes.
- Prefer minimal, surgical edits; don't reformat unrelated code.
- Don't volunteer model details unless explicitly asked.
- When editing files, reference them using workspace-relative links in messages.
- Run unit tests / CI validation before releasing.

## Instruction template (copy into agent config)
- **Tone & style:** Keep responses concise, direct, friendly. Ask clarifying questions only when necessary.
- **Before tool calls:** Send a 1–2 sentence preamble describing the immediate action.
- **Multi-step work:** Create a todo list via `manage_todo_list` before starting; mark one step `in-progress`.
- **File edits:** Use `apply_patch` with minimal changes. Preserve code style and public APIs.
- **Releases:** Follow the repository's `Justfile` release flow: run tests, bump versions in `pyproject.toml` and `src/cerebro/__init__.py`, tag, and push.
- **Safety & secrets:** Never print secrets or credentials. Use environment variables for sensitive values.

## Hard rules vs preferences
- Hard rules (must follow):
  - None at this time. Treat the guidance in this document as team preferences unless a specific policy is requested.
- Preferences (recommended, confirm before strict enforcement):
  - Use `manage_todo_list` for multi-step tasks to track progress.
  - Send a short preamble before tool calls (8–12 words recommended).
  - Use `apply_patch` for file modifications; avoid unrelated changes and preserve style.
  - Do not volunteer the model name unless explicitly asked.

## Example prompts (to test the instruction)
- "Update the version to 1.2.3 and tag a release." → Agent should create a todo list, show a preamble, run checks, and use `apply_patch` to update files.
- "Run the full test suite." → Agent should create a todo list, run tests, and report results.
- "Refactor utils/parser.py for readability." → Agent should propose a small plan, ask clarifying scope questions, then patch files minimally.

## Questions for you
1. Should these rules apply repository-wide, or only to code (`src/`) and infra (`charts/`, `dashboard/`)?
2. Which items are hard policy vs. team preference? (I marked a proposal above — confirm.)
3. For preambles: prefer 8–12 words, or allow shorter/longer?
4. Where should finalized instructions be stored and who should approve them?

## Next steps (after confirmation)
- Finalize the text and move to `docs/agent-customization-instructions.md`.
- Add an entry to `CONTRIBUTING.md` linking to this file.
- Optionally, create a CI check that validates presence of the file and format.

---
Draft created by assistant; reply with answers to the four questions to finalize.
