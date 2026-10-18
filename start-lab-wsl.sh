#!/usr/bin/env bash
set -e
cd '/mnt/c/Users/dtpha/Documents/Programmable Network'
# Windows Docker client works even before Ubuntu WSL integration is enabled.
'/mnt/c/Users/dtpha/AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe' run -it --rm --privileged -v 'C:\Users\dtpha\Documents\Programmable Network:/lab' -w /lab firdaussahran/netlab-mininet:1.0
