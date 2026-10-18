#!/usr/bin/env bash
set -euo pipefail

# Run from the directory containing this script, wherever the checkout lives.
lab_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
cd -- "$lab_dir"
image='firdaussahran/netlab-mininet:1.0'

if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    exec docker run -it --rm --privileged --mount "type=bind,source=$lab_dir,target=/lab" -w /lab "$image"
elif command -v docker.exe >/dev/null 2>&1 && command -v wslpath >/dev/null 2>&1; then
    # WSL fallback when Docker Desktop's Windows client is on PATH.
    windows_dir="$(wslpath -w "$lab_dir")"
    exec docker.exe run -it --rm --privileged --mount "type=bind,source=$windows_dir,target=/lab" -w /lab "$image"
else
    printf '%s\n' 'Docker was not found. Start Docker Desktop and enable WSL integration for this distribution.' >&2
    exit 1
fi
