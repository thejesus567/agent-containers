#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_dir=""
resume=false
delete_history=false
history_volume=agent-containers-codex-history

usage() {
  cat <<'HELP'
Uso: ./codex.sh [--resume] [--project CARPETA] [-- OPCIONES_CODEX]

Sin argumentos: abre Codex sin compartir archivos del equipo.
--project CARPETA: permite leer y modificar exclusivamente esa carpeta del equipo.
--resume: muestra las conversaciones guardadas para retomar una.
--delete-history: elimina permanentemente el historial guardado y sale.
Las opciones después de -- se pasan a Codex (por ejemplo, -- --help).
HELP
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --resume) resume=true; shift ;;
    --delete-history) delete_history=true; shift ;;
    --project)
      if [[ $# -lt 2 || ! -d "$2" ]]; then
        echo 'Indica una carpeta existente después de --project.' >&2
        exit 2
      fi
      project_dir="$(cd -- "$2" && pwd -P)"
      shift 2
      ;;
    --help|-h) usage; exit 0 ;;
    --) shift; break ;;
    *) echo "Opción desconocida: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if command -v podman >/dev/null 2>&1; then
  engine=podman
elif command -v docker >/dev/null 2>&1; then
  engine=docker
else
  echo 'Instala Docker o Podman y arranca su servicio antes de continuar.' >&2
  exit 1
fi

if ! "$engine" info >/dev/null 2>&1; then
  echo "No se puede conectar a $engine. Arranca Docker Desktop o la máquina de Podman." >&2
  exit 1
fi

if [[ "$delete_history" == true ]]; then
  if "$engine" volume inspect "$history_volume" >/dev/null 2>&1; then
    # The engine refuses removal while a running container uses the volume.
    "$engine" volume rm "$history_volume"
  else
    echo 'No hay historial guardado que eliminar.'
  fi
  exit 0
fi

# Rebuild older images that do not support the separated history layout.
if [[ "$("$engine" image inspect --format '{{ index .Config.Labels "io.agent-containers.codex.history-layout" }}' openai-codex 2>/dev/null)" != 1 ]]; then
  make -C "$repo_dir" openai-codex "CONTAINER_ENGINE=$engine"
fi

run_args=(run --rm --interactive --init --cap-drop=ALL
  --security-opt=no-new-privileges --read-only
  --tmpfs /tmp:rw,nosuid,nodev,mode=1777
  --tmpfs /home/node/.codex:rw,nosuid,nodev,uid=1000,gid=1000,mode=0700
  --mount "type=volume,source=$history_volume,target=/home/node/codex-history"
  --env NPM_CONFIG_CACHE=/tmp/npm-cache
  --env XDG_CACHE_HOME=/tmp/cache
  --workdir /app)
if [[ "$engine" == podman ]]; then
  run_args+=(--userns=keep-id:uid=1000,gid=1000)
fi
if [[ -t 0 && -t 1 ]]; then
  run_args+=(--tty)
fi
if [[ -n "$project_dir" ]]; then
  # Docker --mount uses commas as separators; reject ambiguous paths.
  if [[ "$project_dir" == *,* ]]; then
    echo 'La ruta del proyecto no puede contener comas.' >&2
    exit 2
  fi
  run_args+=(--mount "type=bind,source=$project_dir,target=/app")
fi

# Docker keeps the image read-only while the explicitly shared project is writable.
# Nested Bubblewrap is blocked by Docker.
# Only conversation data is persisted; CODEX_HOME and credentials remain temporary.
# No host environment, credential directories, sockets or auth volumes are forwarded.
codex_args=(--sandbox danger-full-access --ask-for-approval on-request
  -c 'cli_auth_credentials_store="ephemeral"')
if [[ "$resume" == true ]]; then
  codex_args+=(resume --all)
fi
exec "$engine" "${run_args[@]}" openai-codex "${codex_args[@]}" "$@"
