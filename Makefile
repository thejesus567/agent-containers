.PHONY: all clean deep-clean base claude-code openai-codex

# Determine container engine (podman or docker)
CONTAINER_ENGINE := $(shell which podman 2>/dev/null || which docker 2>/dev/null)

# UID/GID
HOST_UID := $(shell id -u)
HOST_GID := $(shell id -g)

# Tools to install in to the containers with apt-get
LOCAL_TOOLS := "git curl jq ripgrep vim nano make zip unzip openssh-client wget tree imagemagick build-essential python3 python3-pip ca-certificates gnupg less groff-base"


# Ensure we have a container engine
ifeq ($(CONTAINER_ENGINE),)
$(error No container engine (podman/docker) found in PATH)
endif

all: base claude-code openai-codex

base:
	@echo "Building base image"
	$(CONTAINER_ENGINE) build \
		--build-arg HOST_UID=$(HOST_UID) \
		--build-arg HOST_GID=$(HOST_GID) \
		--build-arg LOCAL_TOOLS=$(LOCAL_TOOLS) \
		-t agent-base \
		-f base/Dockerfile base

claude-code: base
	@echo "Building claude-code"
	$(CONTAINER_ENGINE) build \
		--no-cache \
		-t claude-code \
		-f claude-code/Dockerfile claude-code

openai-codex: base
	@echo "Building openai-codex"
	$(CONTAINER_ENGINE) build \
		--no-cache \
		-t openai-codex \
		-f openai-codex/Dockerfile openai-codex

open-code: base
	@echo "Building open-code"
	$(CONTAINER_ENGINE) build \
		--no-cache \
		-t open-code \
		-f open-code/Dockerfile open-code

clean:
	@echo "Removing container images"
	@for image in open-code claude-code openai-codex agent-base; do \
		if $(CONTAINER_ENGINE) image inspect $$image > /dev/null 2>&1; then \
			echo "Removing $$image"; \
			$(CONTAINER_ENGINE) rmi -f $$image; \
		else \
			echo "Image $$image does not exist, skipping"; \
		fi; \
	done
