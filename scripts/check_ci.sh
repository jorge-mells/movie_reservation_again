#!/bin/bash
set -euo pipefail

# apparently it's not always called act
ACT=$(command -v act-cli 2>/dev/null || command -v act 2>/dev/null || {
  echo "Error: act or act-cli not found" >&2
  exit 1
})

# Detect container runtime socket
# NOTE: use this if you're using rootful podman or rootful docker on linux;
# docker desktop users should be fine without --userns=keep-id due to VM isolation
if [[ -S /run/podman/podman.sock ]]; then
  SOCKET="unix:///run/podman/podman.sock"
elif [[ -S /var/run/docker.sock ]]; then
  SOCKET="unix:///var/run/docker.sock"
else
  echo "Error: no container runtime socket found" >&2
  exit 1
fi

DOCKER_HOST="$SOCKET" "$ACT" push \
  --container-options "--privileged" \
  --container-options "--user $(id -u):$(id -g)" \
  --bind
