#!/usr/bin/env bash
# Rebuild every Painted Storybook asset from source.
#
#   art_src/build_all.sh
#
# Blender is needed ONLY here. GitHub Actions builds the game from the .glb
# files in assets/storybook/, which are committed, so the deploy pipeline
# never installs Blender.
set -euo pipefail
cd "$(dirname "$0")/.."

BLENDER="${BLENDER:-blender}"
command -v "$BLENDER" >/dev/null || {
    echo "Blender not found. Set BLENDER=/path/to/blender." >&2
    exit 1
}

for asset in block chuck cottage tree pedestal path_stone meadow; do
    echo "=== $asset ==="
    "$BLENDER" --background --python "art_src/build_${asset}.py" 2>&1 \
        | grep -E '^\[asset\]|Error|Traceback' || true
done

echo
echo "Re-import in Godot before the GLBs take effect:"
echo "  \$GODOT --headless --path . --editor --import"
