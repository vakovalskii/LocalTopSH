# 🐧 LocalTopSH

**AI Agent with full system access — your own infrastructure, your own rules.**

> 🔥 **Battle-tested by 1500+ hackers!**
> 
> Live in [**@neuraldeepchat**](https://t.me/neuraldeepchat) — community stress-tested with **1500+ attack attempts**:
> - Token extraction (env, /proc, base64 exfil, HTTP servers)
> - RAM/CPU exhaustion (zip bombs, infinite loops, fork bombs)
> - Container escape attempts
> 
> **Result: 0 secrets leaked, 0 downtime.**

---

## Philosophy: Engineering Over Subscription Abuse

Unlike projects that rely on abusing consumer subscriptions (Claude Max, ChatGPT Plus) through browser automation and cookie theft, **LocalTopSH is built on honest engineering principles**:

| Approach | LocalTopSH ✅ | Subscription Abuse ❌ |
|----------|--------------|----------------------|
| **LLM Access** | Your own API keys | Stolen browser sessions |
| **Cost Model** | Pay for what you use | Violate ToS, risk bans |
| **Reliability** | 100% uptime (your infra) | Breaks when UI changes |
| **Security** | Full control over secrets | Cookies stored who-knows-where |
| **Ethics** | Transparent & legal | Gray area at best |

**We believe in building real infrastructure, not hacks that break tomorrow.**

---

## Built-in Capabilities

What the agent can do out of the box:

### 💻 System & Files
| Capability | Description |
|------------|-------------|
| **Shell execution** | Run any command in isolated sandbox |
| **File operations** | Read, write, edit, delete, search files |
| **Directory navigation** | List, search by glob patterns |
| **Code execution** | Python, Node.js, bash scripts |

### 🌐 Web & Research
| Capability | Description |
|------------|-------------|
| **Web search** | Search via Z.AI API |
| **Page fetching** | Get any URL as clean markdown |
| **Link extraction** | Parse and follow links |

### 🧠 Memory & Context
| Capability | Description |
|------------|-------------|
| **Persistent memory** | Remember facts across sessions |
| **Task management** | Todo lists within session |
| **Chat history** | Full conversation context |

### ⏰ Automation
| Capability | Description |
|------------|-------------|
| **Scheduled tasks** | Cron-like reminders |
| **Background jobs** | Long-running processes |

### 📱 Telegram Integration
| Capability | Description |
|------------|-------------|
| **Send files** | Share generated files |
| **Direct messages** | Send DMs to users |
| **Message management** | Edit/delete bot messages |
| **Interactive prompts** | Ask user and wait for response |

---

## Skills System

Skills are extensible packages that add new tools, prompts, and commands to the agent. Similar to Anthropic's Skills feature.

### How Skills Work

```
┌─────────────────────────────────────────────────────────────────┐
│                      SKILLS ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   /workspace/{user_id}/skills/    ← User-specific skills       │
│   └── my-skill/                                                 │
│       └── skill.json                                            │
│                                                                 │
│   /data/skills/                   ← Shared skills (all users)  │
│   └── common-skill/                                             │
│       └── skill.json                                            │
│                                                                 │
│   Tools API scans these directories on each request             │
│   New skills are picked up automatically!                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### skill.json Format

```json
{
  "name": "my-skill",
  "description": "What this skill does",
  "version": "1.0.0",
  "author": "Your Name",
  
  "tools": [
    {
      "name": "my_tool",
      "description": "What this tool does",
      "parameters": {
        "type": "object",
        "properties": {
          "input": {"type": "string", "description": "Input parameter"}
        },
        "required": ["input"]
      }
    }
  ],
  
  "system_prompt": "Additional instructions for the agent when this skill is active.",
  
  "commands": {
    "/mycommand": "Description of slash command"
  },
  
  "enabled": true
}
```

### Creating a Skill

```bash
# 1. Create skill directory in your workspace
mkdir -p /workspace/skills/my-skill

# 2. Create skill.json
cat > /workspace/skills/my-skill/skill.json << 'EOF'
{
  "name": "my-skill",
  "description": "My custom skill",
  "version": "1.0.0",
  "tools": [
    {
      "name": "hello",
      "description": "Say hello",
      "parameters": {"type": "object", "properties": {}}
    }
  ]
}
EOF

# 3. Skills are loaded automatically on next agent request!
```

### Skills API

```bash
# List all skills
curl http://localhost:8100/skills?user_id=123456

# Get skill details
curl http://localhost:8100/skills/my-skill?user_id=123456

# Force rescan
curl -X POST http://localhost:8100/skills/scan?user_id=123456

# Get all system prompts from skills
curl http://localhost:8100/skills/prompts/all?user_id=123456

# Enable/disable skill
curl -X PUT http://localhost:8100/skills/my-skill \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

### Tool Naming

Skill tools are prefixed with `skill_{name}_{tool}`:
- `skill_my-skill_hello`
- `skill_github_create_pr`

---

## MCP Support

LocalTopSH supports MCP (Model Context Protocol) for extensible tool integration:

```
┌─────────────────────────────────────────────────────────────────┐
│                      MCP Architecture                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────┐     ┌─────────────┐     ┌─────────────────────┐  │
│   │  Agent  │────▶│  Tools API  │────▶│  MCP Servers        │  │
│   └─────────┘     │  (registry) │     ├─────────────────────┤  │
│                   └─────────────┘     │ • filesystem        │  │
│                         │             │ • git               │  │
│                         ▼             │ • database          │  │
│                   ┌───────────┐       │ • browser           │  │
│                   │ Builtin   │       │ • custom tools...   │  │
│                   │ Tools (14)│       └─────────────────────┘  │
│                   └───────────┘                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### MCP Features

- [x] MCP server registry (`/mcp/servers`)
- [x] Dynamic tool loading from MCP servers
- [x] Tool search (`search_tools` tool)
- [x] Per-server tool refresh
- [ ] Resource access (files, databases)
- [ ] Prompt templates from MCP

### Adding MCP Server

```bash
# Via API
curl -X POST http://localhost:8100/mcp/servers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "filesystem",
    "url": "http://mcp-filesystem:3001",
    "transport": "http",
    "description": "File system operations"
  }'

# Refresh tools from server
curl -X POST http://localhost:8100/mcp/servers/filesystem/refresh

# List all tools (builtin + MCP)
curl http://localhost:8100/tools
```

### MCP Config File

Tools API stores MCP config in `/data/mcp_servers.json`:

```json
{
  "filesystem": {
    "name": "filesystem",
    "url": "http://mcp-filesystem:3001",
    "enabled": true,
    "transport": "http",
    "description": "File system operations"
  },
  "github": {
    "name": "github",
    "url": "http://mcp-github:3002",
    "enabled": true,
    "transport": "http",
    "api_key": "ghp_xxx"
  }
}
```

### Tool Naming

MCP tools are prefixed with `mcp_{server}_{tool}`:
- `mcp_filesystem_read_file`
- `mcp_github_create_issue`
- `mcp_database_query`

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DOCKER COMPOSE                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│                                 ┌─────────────────┐                              │
│                                 │    Telegram     │                              │
│                                 │      API        │                              │
│                                 └────────┬────────┘                              │
│                                          │                                       │
│               ┌──────────────────────────┴──────────────────────────┐            │
│               │                                                     │            │
│               ▼                                                     ▼            │
│  ┌────────────────────────┐                          ┌────────────────────────┐  │
│  │ 📦 CONTAINER: bot      │                          │ 📦 CONTAINER: userbot  │  │
│  │ ─────────────────────  │                          │ ─────────────────────  │  │
│  │ Image: python:3.11     │                          │ Image: python:3.11     │  │
│  │ Port:  4001            │                          │ Port:  8080            │  │
│  │ Stack: aiogram         │                          │ Stack: telethon        │  │
│  │ ─────────────────────  │                          │ ─────────────────────  │  │
│  │ • Telegram handlers    │                          │ • User account bot     │  │
│  │ • Reactions/thoughts   │                          │ • Extended API access  │  │
│  │ • Access control       │                          │ • (optional)           │  │
│  └───────────┬────────────┘                          └───────────┬────────────┘  │
│              │                                                   │               │
│              │                    HTTP API                       │               │
│              └───────────────────────┬───────────────────────────┘               │
│                                      │                                           │
│                                      ▼                                           │
│  ┌────────────────────────┐  ╔══════════════════════════╗  ┌──────────────────┐  │
│  │ 📦 CONTAINER: admin    │  ║ 📦 CONTAINER: core       ║  │ 📦 CONTAINER:    │  │
│  │ ─────────────────────  │  ║ ════════════════════════ ║  │    proxy         │  │
│  │ Image: node:20         │  ║ Image: python:3.11       ║  │ ───────────────  │  │
│  │ Port:  3000            │  ║ Port:  4000              ║  │ Image: python    │  │
│  │ Stack: React + Vite    │  ║ Stack: FastAPI           ║  │ Port:  3200      │  │
│  │ ─────────────────────  │  ║ ════════════════════════ ║  │ Stack: aiohttp   │  │
│  │ • Dashboard            │──▶║ • ReAct Agent loop      ║──▶│ ───────────────  │  │
│  │ • Config editor        │  ║ • Security validation   ║  │ • LLM API proxy  │  │
│  │ • User management      │  ║ • Tool execution        ║  │ • Search proxy   │  │
│  │ • Logs viewer          │  ║ • Sandbox orchestration ║  │ • Holds secrets  │  │
│  └────────────────────────┘  ║ • Scheduler             ║  │ • Agent sees 0   │  │
│                              ╚════════════╤═════════════╝  └──────────────────┘  │
│                                           │                                      │
│              ┌────────────────────────────┼────────────────────────────┐         │
│              │                            │                            │         │
│              ▼                            ▼                            ▼         │
│  ┌────────────────────────┐  ┌────────────────────────┐  ┌──────────────────────┐│
│  │ 📦 CONTAINER:          │  │ 📦 CONTAINER:          │  │ 📦 CONTAINER:        ││
│  │    tools-api           │  │    mcp-test            │  │    sandbox_{user_id} ││
│  │ ─────────────────────  │  │ ─────────────────────  │  │ ────────────────────-││
│  │ Image: python:3.11     │  │ Image: python:3.11     │  │ Image: python:3.11   ││
│  │ Port:  8100            │  │ Port:  8200            │  │ Port:  5000-5999     ││
│  │ Stack: FastAPI         │  │ Stack: FastAPI         │  │ ────────────────────-││
│  │ ─────────────────────  │  │ ─────────────────────  │  │ • Per-user isolated  ││
│  │ • Tool definitions     │  │ • Test MCP server      │  │ • 512MB RAM limit    ││
│  │ • MCP client           │  │ • echo/time/random     │  │ • 50% CPU limit      ││
│  │ • Skills registry      │  │ • JSON-RPC 2.0         │  │ • 100 PIDs max       ││
│  │ • Dynamic loading      │  │                        │  │ • Auto-cleanup 10min ││
│  └────────────────────────┘  └────────────────────────┘  └──────────────────────┘│
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                              VOLUMES                                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  📁 ./workspace:/workspace          📁 ./secrets:/run/secrets (readonly)         │
│  ├── {user_id}/                     ├── telegram_token.txt                       │
│  │   ├── MEMORY.md                  ├── base_url.txt                             │
│  │   └── files...                   ├── api_key.txt                              │
│  └── _shared/                       ├── model_name.txt                           │
│      ├── skills/                    └── zai_api_key.txt                          │
│      ├── CHAT_HISTORY.md                                                         │
│      └── pairing.json               📁 /var/run/docker.sock (core only)          │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Services Summary

| Container | Image | Port | Stack | Role |
|-----------|-------|------|-------|------|
| **core** | python:3.11 | 4000 | FastAPI | 🧠 ReAct Agent, security, sandbox orchestration |
| **bot** | python:3.11 | 4001 | aiogram | 🤖 Telegram Bot API, reactions, thoughts |
| **userbot** | python:3.11 | 8080 | telethon | 👤 User account bot (optional) |
| **proxy** | python:3.11 | 3200 | aiohttp | 🔐 Secrets isolation, LLM/search proxy |
| **tools-api** | python:3.11 | 8100 | FastAPI | 🔧 Tool registry, MCP client, skills |
| **mcp-test** | python:3.11 | 8200 | FastAPI | 🧪 Test MCP server (echo/time/random) |
| **admin** | node:20 | 3000 | React+Vite | 🖥️ Web admin panel |
| **sandbox_{id}** | python:3.11 | 5000-5999 | - | 📦 Per-user isolated execution |

## Tools

### Shared Tools (13)

| Tool | Description |
|------|-------------|
| `run_command` | Execute shell in user's sandbox |
| `read_file` | Read file content |
| `write_file` | Create/overwrite file |
| `edit_file` | Edit file (find & replace) |
| `delete_file` | Delete file |
| `search_files` | Find files by glob |
| `search_text` | Grep in files |
| `list_directory` | List directory |
| `search_web` | Web search (Z.AI) |
| `fetch_page` | Fetch URL as markdown |
| `memory` | Persistent user notes |
| `schedule_task` | Schedule reminders/cron |
| `manage_tasks` | Session todo list |

### Bot-Only Tools (4)

| Tool | Description |
|------|-------------|
| `send_file` | Send file to chat |
| `send_dm` | Send private message |
| `manage_message` | Edit/delete bot messages |
| `ask_user` | Ask question, wait answer |

## Security

> 📖 **Full documentation:** [SECURITY.md](SECURITY.md)

### Five Layers of Protection

| Layer | Protection | Details |
|-------|------------|---------|
| **Access Control** | DM Policy | admin/allowlist/pairing/public modes |
| **Input Validation** | Blocked patterns | 247 dangerous commands blocked |
| **Injection Defense** | Pattern matching | 19 prompt injection patterns |
| **Sandbox Isolation** | Docker per-user | 512MB RAM, 50% CPU, 100 PIDs |
| **Secrets Protection** | Proxy architecture | 0 secrets visible to agent |

### Security Audit

```bash
# Run security doctor
python scripts/doctor.py

# Output as JSON
python scripts/doctor.py --json
```

## Access Control

Four modes managed via bot commands or admin panel:

| Mode | Description |
|------|-------------|
| **Admin Only** | Only admin can use (default, safest) |
| **Allowlist** | Admin + configured user IDs |
| **Pairing** | Unknown users get pairing code for approval |
| **Public** | Anyone can use (⚠️ requires rate limiting) |

### Bot Commands

```bash
/access              # Show access status (admin only)
/access_mode admin   # Set mode
/approve ABC123      # Approve pairing code
/revoke 123456789    # Revoke user access
/allow 123456789     # Add to allowlist
```

## Quick Start

```bash
# 1. Create secrets
mkdir secrets
echo "your-telegram-token" > secrets/telegram_token.txt
echo "http://your-llm:8000/v1" > secrets/base_url.txt
echo "your-llm-key" > secrets/api_key.txt
echo "gpt-4" > secrets/model_name.txt
echo "your-zai-key" > secrets/zai_api_key.txt

# 2. Start
docker compose up -d

# 3. Check
docker compose logs -f

# 4. Admin panel
open http://localhost:3000
```

## Admin Panel

Web panel at `:3000` for managing the system:

- **Dashboard** — stats, active users, sandboxes
- **Services** — start/stop bot, userbot containers
- **Config** — agent settings, rate limits
- **Security** — blocked patterns management
- **Tools** — enable/disable shared tools
- **Users** — sessions, chat history, memory
- **Logs** — real-time service logs
- **Access Control** — public/admin-only/allowlist modes

## Dynamic Sandbox

Each user gets isolated Docker container:

- **Image**: `python:3.11-slim`
- **Ports**: 10 ports per user (5000-5999)
- **Resources**: 512MB RAM, 50% CPU, 100 PIDs
- **Workspace**: Only own `/workspace/{user_id}/`
- **TTL**: 10 min inactivity → auto-cleanup
- **Security**: `no-new-privileges`, no secrets access

## Project Structure

```
LocalTopSH/
├── docker-compose.yml
├── secrets/              # API keys (gitignored)
│
├── core/                 # ReAct Agent (Python/FastAPI)
│   ├── main.py
│   ├── agent.py         # ReAct loop
│   ├── api.py           # HTTP API
│   ├── admin_api.py     # Admin panel API
│   ├── security.py      # Blocked patterns
│   ├── tools/           # Tool executors
│   │   └── permissions.py  # Tool allowlist/denylist
│   └── Dockerfile
│
├── scripts/              # CLI tools
│   ├── doctor.py        # Security audit
│   └── e2e_test.py      # E2E tests (10 checks)
│
├── bot/                  # Telegram Bot (Python/aiogram)
│   ├── main.py
│   ├── handlers.py
│   ├── access.py        # DM Policy
│   ├── thoughts.py      # Autonomous messages
│   ├── security.py      # Prompt injection
│   └── Dockerfile
│
├── userbot/              # Telegram Userbot (Python/Telethon)
│   ├── main.py
│   └── Dockerfile
│
├── proxy/                # API Proxy (Python/aiohttp)
│   ├── main.py
│   └── Dockerfile
│
├── tools-api/            # Shared Tools Registry (Python/FastAPI)
│   ├── app.py            # Entry point
│   ├── src/
│   │   ├── config.py     # Configuration
│   │   ├── tools.py      # Built-in tool definitions
│   │   ├── mcp.py        # MCP client & cache
│   │   ├── skills.py     # Skills manager
│   │   └── routes/       # API endpoints
│   │       ├── tools.py
│   │       ├── mcp.py
│   │       └── skills.py
│   └── Dockerfile
│
├── admin/                # Admin Panel (React/Vite)
│   ├── src/
│   │   ├── pages/       # Dashboard, Config, Security, Tools, Users, Logs
│   │   └── api.js
│   └── Dockerfile
│
└── workspace/            # User data (gitignored)
    ├── {user_id}/       # Per-user workspace
    └── _shared/         # Shared config (tools, access)
```

## Secrets

| Secret | Required | Description |
|--------|----------|-------------|
| `telegram_token.txt` | ✅ | Bot token from @BotFather |
| `base_url.txt` | ✅ | LLM API URL (e.g. `http://your-llm:8000/v1`) |
| `api_key.txt` | ✅ | LLM API key |
| `model_name.txt` | ✅ | Model name (e.g. `gpt-4`, `gpt-oss-120b`) |
| `zai_api_key.txt` | ✅ | Z.AI search key |
| `telegram_api_id.txt` | Userbot | Telegram API ID |
| `telegram_api_hash.txt` | Userbot | Telegram API Hash |
| `telegram_phone.txt` | Userbot | Phone number |

## License

MIT
