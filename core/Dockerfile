# LocalTopSH Core - Python ReAct Agent
FROM python:3.11-bookworm

# Install tools for agent and users
RUN apt-get update && apt-get install -y \
    git curl wget gawk \
    build-essential cmake \
    jq htop tree ripgrep fd-find \
    zip unzip tar \
    iproute2 net-tools lsof \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/fdfind /usr/bin/fd

# Pre-install common Python packages
RUN pip install --no-cache-dir flask fastapi uvicorn requests

WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy all Python modules
COPY *.py ./
COPY tools/ ./tools/

# Copy config files from src/
COPY src/agent/system.txt ./src/agent/
COPY src/approvals/blocked-patterns.json ./src/approvals/

# Create workspace
RUN mkdir -p /workspace && chmod 777 /workspace

ENV AGENT_CWD=/workspace

CMD ["python", "-u", "main.py"]
