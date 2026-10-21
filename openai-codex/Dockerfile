# Build stage
FROM agent-base AS builder

ARG CODEX_VERSION=0.163.0

# Install OpenAI Codex in the builder stage
RUN npm install -g "@openai/codex@${CODEX_VERSION}" && \
  echo "Installed Codex version: $(codex --version)"

# Runtime stage
FROM agent-base

# Copy the installed Codex from builder
# We must use --chown to ensure the node user owns the copied files
COPY --from=builder --chown=node:node /home/node/.npm-global /home/node/.npm-global

# Display version information
RUN echo "" && \
  echo "\e[34m=================================================================\e[0m" && \
  echo "\e[34m                   OPENAI CODEX VERSION                          \e[0m" && \
  echo "\e[34m=================================================================\e[0m" && \
  echo "\e[34m" && codex --version && \
  echo "\e[0m" && \
  echo ""

# Do not persist login tokens in the image or a host-mounted directory.
ENV CODEX_HOME=/home/node/.codex
RUN mkdir -p "$CODEX_HOME" /home/node/codex-history && \
  chmod 700 "$CODEX_HOME" /home/node/codex-history
COPY --chown=node:node --chmod=755 entrypoint.sh /usr/local/bin/codex-entrypoint
LABEL io.agent-containers.codex.history-layout="1"

# Use codex.sh to enforce a read-only container filesystem and temporary storage.
ENTRYPOINT ["/usr/local/bin/codex-entrypoint"]
CMD ["--sandbox", "danger-full-access", "--ask-for-approval", "on-request", "-c", "cli_auth_credentials_store=\"ephemeral\""]
