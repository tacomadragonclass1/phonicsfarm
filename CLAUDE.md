# Claude Code handoff

Read AGENTS.md for repository instructions, PROGRESS.md for current session
state and outstanding limitations, and README.md for architecture and test
commands before editing. Keep shared handoff updates in PROGRESS.md so Claude
Code, Codex, and OpenCode/Qwen use the same memory.

Start with **Session handoff — 2026-09-20 (i)** at the top of PROGRESS.md.
Implemented: CVC Land audio, lever, visual feedback, word recognition,
Phoneme Village, the 40x40-per-clearing field, the single outer boundary, and
the camera/crop/prompt/Annette-touch fixes.

Two things that look like bugs but are decisions: the board sits 15 degrees off
screen-axis because the camera yaw is 30 for a three-quarter view (45 is the
axis-aligned value), and Phoneme Village uses 23 letters because k, q and x
collide with c by ear. Both are explained in README and PROGRESS.
Older sections record superseded decisions; they are not pending instructions.

Annette's two sentences are now **Milo's own recordings**, not TTS -- do not
re-render them. Only `wrong_chime.wav` is still synthesized and unheard.

`tools/build_phoneme_village.py` was a one-time scaffold. `village/phoneme_village.tscn`
is the source of truth now and the user edits scenes in the editor; do not
regenerate it with `--force`.

Preserve the uncommitted changes and untracked runtime assets. Await the user's
next task; do not commit, push, regenerate voices or expand gameplay on resume.
