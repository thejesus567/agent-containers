# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build Commands
- `make all` - Build all containers
- `make claude-code` - Build Claude Code container
- `make openai-codex` - Build OpenAI Codex container
- `make clean` - Remove Docker images and prune dangling images

## Run Commands
- Claude Code: `docker run -it --rm -v ${HOME}/.config/claude/claude.json:/home/codeuser/.claude.json:rw -v $(pwd):/app:rw claude-code`
- OpenAI Codex: `make codex` (new conversation); `make codex-resume` (saved conversations); `./codex.sh --project /path/to/project` (read and write project access)
- Aider: `docker run -it --rm --user $(id -u):$(id -g) -e OPENAI_API_KEY -e ANTHROPIC_API_KEY -v $(pwd):/app:rw paulgauthier/aider`

## Code Style Guidelines
- Docker-based project with separate containers for different AI assistants
- Use explicit mounting of configuration files with appropriate permissions (700/600)
- Never mount host credentials or forward host API keys in the Codex launcher; use ephemeral Codex authentication
- Persist only Codex conversation files and SQLite state in the history volume; keep CODEX_HOME and auth files in tmpfs
- Document configuration persistence in README files per tool
- Bash commands should use `$(pwd)` for current directory mounting
- Prioritize security for configuration files containing API keys
