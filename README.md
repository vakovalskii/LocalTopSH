# LocalTopSH 🐧

**AI Agent with full system access, sandboxed per user.**

> 🔥 **Battle-tested by 1500+ hackers!**
> 
> Live in [**@neuraldeepchat**](https://t.me/neuraldeepchat) — community stress-tested with **1500+ attack attempts**:
> - Token extraction (env, /proc, base64 exfil, HTTP servers)
> - RAM/CPU exhaustion (zip bombs, infinite loops, fork bombs)
> - Container escape attempts
> 
> **Result: 0 secrets leaked, 0 downtime.**

## Architecture

```
                              ┌─────────────────┐
                              │    Telegram     │
                              │      API        │
                              └────────┬────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              │                        │                        │
              ▼                        ▼                        ▼
       ┌─────────────┐          ┌─────────────┐          ┌─────────────┐
       │     bot     │          │   userbot   │          │             │
       │   aiogram   │          │  telethon   │          │             │
       │   :4001     │          │    :8080    │          │             │
       └──────┬──────┘          └──────┬──────┘          │             │
              │                        │                 │             │
              │         HTTP API       │                 │             │
              └────────────┬───────────┘                 │             │
                           │                             │             │
                           ▼                             │             │
                    ╔═════════════╗                      │             │
                    ║    CORE     ║                      │             │
                    ║   Agent     ║                      │   proxy     │
                    ║  (FastAPI)  ║─────────────────────▶│   :3200     │
                    ║   :4000     ║      LLM/Search      │             │
                    ╠═════════════╣                      │  Secrets:   │
                    ║ • ReAct     ║                      │  • api_key  │
                    ║ • 14 Tools  ║                      │  • base_url │
                    ║ • Scheduler ║                      │  • zai_key  │
                    ║ • Security  ║                      └─────────────┘
                    ╚══════┬══════╝
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
       ┌───────────┐ ┌───────────┐ ┌───────────┐
       │ sandbox_1 │ │ sandbox_2 │ │ sandbox_N │
       │  user123  │ │  user456  │ │   user... │
       │ py:3.11   │ │ py:3.11   │ │ py:3.11   │
       │ ports 5000│ │ ports 5010│ │ ports ... │
       └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
             │             │             │
             ▼             ▼             ▼
       ┌───────────────────────────────────────┐
       │           /workspace (volume)         │
       │  /123/  │  /456/  │  /.../ │ /_shared │
       └───────────────────────────────────────┘
```

**100% Python Stack:**

| Service | Stack | Port | Description |
|---------|-------|------|-------------|
| **core** | FastAPI | 4000 | ReAct Agent, 14 tools, scheduler, security |
| **bot** | aiogram | 4001 | Telegram Bot API, reactions, thoughts |
| **userbot** | Telethon | 8080 | User account bot (optional) |
| **proxy** | aiohttp | 3200 | Secrets isolation, LLM/search proxy |
| **sandbox_*** | python:slim | 5000-5999 | Per-user isolated containers |

## Core Agent

The **core** is the brain of the system:

```
core/
├── main.py          # Entry + sandbox init
├── agent.py         # ReAct loop (Think→Act→Observe)
├── api.py           # HTTP endpoints for bot/userbot
├── security.py      # 247 blocked patterns
├── config.py        # All settings
├── logger.py        # Centralized logging
└── tools/           # 14 tools
    ├── bash.py      # run_command (→ sandbox)
    ├── sandbox.py   # Docker sandbox manager
    ├── files.py     # read/write/edit/delete/search
    ├── web.py       # search_web, fetch_page
    ├── memory.py    # Persistent notes
    ├── scheduler.py # Cron/reminders
    ├── tasks.py     # Todo list
    ├── send_file.py # Send files to chat
    ├── send_dm.py   # Private messages
    ├── message.py   # Edit/delete messages
    └── ask_user.py  # Interactive questions
```

## Tools (14)

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
| `ask_user` | Ask question, wait answer |

**Bot-only tools** (via HTTP callback):
- `send_file` — Send file to chat
- `send_dm` — Send private message
- `manage_message` — Edit/delete bot messages

## Dynamic Sandbox

Each user gets isolated Docker container:

- **Image**: `python:3.11-slim`
- **Ports**: 10 ports per user (5000-5999)
- **Resources**: 512MB RAM, 50% CPU, 100 PIDs
- **Workspace**: Only own `/workspace/{user_id}/`
- **TTL**: 10 min inactivity → auto-cleanup
- **Security**: `no-new-privileges`, no secrets access

## Quick Start

```bash
# 1. Create secrets
mkdir secrets
echo "your-telegram-token" > secrets/telegram_token.txt
echo "http://your-llm:8000/v1" > secrets/base_url.txt
echo "your-llm-key" > secrets/api_key.txt
echo "your-zai-key" > secrets/zai_api_key.txt

# 2. Start
docker compose up -d

# 3. Check
docker compose logs -f
```

## Security

**266+ protection patterns:**
- 247 blocked shell command patterns
- 19 prompt injection patterns

**Layers:**
1. **Sandbox isolation** — each user in separate container
2. **Workspace separation** — users can't access each other's files
3. **Secrets via Proxy** — agent never sees API keys
4. **Command blocking** — env, /proc, secrets paths blocked
5. **Output sanitization** — secrets redacted from output
6. **Rate limiting** — Telegram API, groups, reactions

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
│   ├── security.py      # Blocked patterns
│   ├── tools/           # 14 tools
│   └── Dockerfile
│
├── bot/                  # Telegram Bot (Python/aiogram)
│   ├── main.py
│   ├── handlers.py
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
└── workspace/            # User data (gitignored)
    ├── {user_id}/       # Per-user workspace
    └── _shared/         # Shared data
```

## Secrets

| Secret | Required | Description |
|--------|----------|-------------|
| `telegram_token.txt` | ✅ | Bot token from @BotFather |
| `base_url.txt` | ✅ | LLM API URL |
| `api_key.txt` | ✅ | LLM API key |
| `zai_api_key.txt` | ✅ | Z.AI search key |

## License

MIT
