# Project handoff

Read `PROGRESS.md` for the saved session state and `README.md` for architecture,
controls, launch commands and tests before making changes.

The initial prototype is complete. Preserve the user's intentionally small scope
and any subsequent editor changes. Implement the next requested task; do not start
the suggested future tasks automatically. Keep GDScript straightforward and scenes
reusable for future OpenCode/Qwen or Claude Code handoff.

Before editing, inspect `git status --short` and the current diff; preserve work
left by the user or another agent. After each task, update PROGRESS.md with the
result, affected files, checks actually run, outstanding limitations, and Git
state. Do not describe untested changes as verified. Commit or push only when
the user requests it.

Godot is installed at
`/home/milo/.local/opt/godot-4.5.2/Godot_v4.5.2-stable_linux.x86_64`.
Use this path for checks even when `godot` is not on PATH. See README.md for
the smoke and layout tests. Rendered captures must run without --headless.
