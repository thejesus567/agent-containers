FROM node:23-slim

ARG HOST_UID=1000
ARG HOST_GID=1000
# Combine all tools here. Note: added specific tools you listed for runtime
#ARG LOCAL_TOOLS="git curl jq ripgrep vim make zip unzip ssh-client wget tree imagemagick ca-certificates gnupg procps"
ARG LOCAL_TOOLS="git curl jq ca-certificates gnupg unzip less groff-base"

# 1. Install System Dependencies (as root)
RUN apt-get update && \
  apt-get install -y --no-install-recommends ${LOCAL_TOOLS} && \
  rm -rf /var/lib/apt/lists/*

# Install AWS CLI v2 using the official bundled installer
RUN ARCH="$(dpkg --print-architecture)" && \
  case "${ARCH}" in \
    amd64) AWS_ARCH="x86_64" ;; \
    arm64) AWS_ARCH="aarch64" ;; \
    *) echo "Unsupported architecture: ${ARCH}" >&2; exit 1 ;; \
  esac && \
  curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-${AWS_ARCH}.zip" -o "/tmp/awscliv2.zip" && \
  unzip -q /tmp/awscliv2.zip -d /tmp && \
  /tmp/aws/install --bin-dir /usr/local/bin --install-dir /usr/local/aws-cli && \
  rm -rf /tmp/aws /tmp/awscliv2.zip && \
  aws --version && \
  rm -rf /var/lib/apt/lists/*

# Install kubectl from the official Kubernetes apt repository
RUN install -m 0755 -d /etc/apt/keyrings && \
  curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.35/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg && \
  chmod 0644 /etc/apt/keyrings/kubernetes-apt-keyring.gpg && \
  echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.35/deb/ /" > /etc/apt/sources.list.d/kubernetes.list && \
  chmod 0644 /etc/apt/sources.list.d/kubernetes.list && \
  apt-get update && \
  apt-get install -y --no-install-recommends kubectl && \
  kubectl version --client && \
  rm -rf /var/lib/apt/lists/*

# Install Terraform from the official HashiCorp apt repository
RUN install -m 0755 -d /etc/apt/keyrings && \
  curl -fsSL https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg && \
  chmod 0644 /usr/share/keyrings/hashicorp-archive-keyring.gpg && \
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(. /etc/os-release && echo \"${VERSION_CODENAME}\") main" > /etc/apt/sources.list.d/hashicorp.list && \
  apt-get update && \
  apt-get install -y --no-install-recommends terraform && \
  terraform version && \
  rm -rf /var/lib/apt/lists/*

# Install OpenTofu from the official apt repository
RUN install -m 0755 -d /etc/apt/keyrings && \
  curl -fsSL https://get.opentofu.org/opentofu.gpg > /etc/apt/keyrings/opentofu.gpg && \
  curl -fsSL https://packages.opentofu.org/opentofu/tofu/gpgkey | gpg --no-tty --batch --dearmor -o /etc/apt/keyrings/opentofu-repo.gpg && \
  chmod 0644 /etc/apt/keyrings/opentofu.gpg /etc/apt/keyrings/opentofu-repo.gpg && \
  echo "deb [signed-by=/etc/apt/keyrings/opentofu.gpg,/etc/apt/keyrings/opentofu-repo.gpg] https://packages.opentofu.org/opentofu/tofu/any/ any main" > /etc/apt/sources.list.d/opentofu.list && \
  chmod 0644 /etc/apt/sources.list.d/opentofu.list && \
  apt-get update && \
  apt-get install -y --no-install-recommends tofu && \
  tofu version

# Install Bun by copying from the official image
# This installs bun globally to /usr/local/bin so it is available to everyone
COPY --from=oven/bun:1 /usr/local/bin/bun /usr/local/bin/bun
# Create the bunx symlink (standard practice)
RUN ln -s /usr/local/bin/bun /usr/local/bin/bunx

# Install tod (One Dev CLI / MCP binary)
COPY bin/tod /usr/local/bin/tod
RUN chmod +x /usr/local/bin/tod

# Install Playwright system dependencies for Chromium (required by agent-browser)
RUN npx playwright install-deps chromium

# Corepack
RUN corepack enable

# 2. Configure the existing 'node' user
# The node image usually creates the node user. We ensure it owns the app dir.
WORKDIR /app
RUN chown -R node:node /app

# 3. Switch to 'node' user for config setup
USER node

# 4. Configure NPM global location for the 'node' user
# This allows npm install -g without root permissions
ENV NPM_CONFIG_PREFIX=/home/node/.npm-global
ENV PATH=$NPM_CONFIG_PREFIX/bin:$PATH

# Configure Bun global location for 'node' user ---
# This ensures 'bun install -g' works without root and saves to the user home
ENV BUN_INSTALL=/home/node/.bun
ENV PATH=$BUN_INSTALL/bin:$PATH

RUN mkdir -p /home/node/.npm-global && \
  mkdir -p /home/node/.config && \
  mkdir -p /home/node/.local && \
  mkdir -p /home/node/.bun/bin

# 5. Install agent-browser (headless browser automation CLI for AI agents)
# Downloads Chromium browser to user's cache
RUN npm install -g agent-browser && \
  agent-browser install

# 6. Bash Configuration
# Add the path export to bashrc so interactive shells pick it up
RUN echo "export PATH=${NPM_CONFIG_PREFIX}/bin:${BUN_INSTALL}/bin:\$PATH" >> /home/node/.bashrc

# 7. Copy aliases to the 'node' user's home
COPY --chown=node:node ./.bash_aliases /home/node/.bash_aliases
RUN echo "if [ -f ~/.bash_aliases ]; then . ~/.bash_aliases; fi" >> /home/node/.bashrc

CMD ["/bin/bash"]
