# LocalTopSH Agent Evolution

## Что это
Telegram бот с ReAct агентом, который дает пользователям доступ к изолированному Linux окружению.
Протестирован 1500+ хакерами в группе @neuraldeepchat в течение 7 часов.
Результат: 0 утечек секретов, 0 даунтайма.

## Security Model — The Pentagram 🔮

```
                           ⛧ THE SECURITY PENTAGRAM ⛧
                        
                                 🔐 ACCESS
                                    ╱╲
                                   ╱  ╲
                                  ╱    ╲
                                 ╱  ⛧   ╲
                                ╱        ╲
                               ╱    👁️    ╲
                              ╱   AGENT    ╲
                      🛡️ INPUT ────────────── OUTPUT 🔒
                            ╲      ╱╲      ╱
                             ╲    ╱  ╲    ╱
                              ╲  ╱    ╲  ╱
                               ╲╱  ⛧   ╲╱
                               ╱╲      ╱╲
                              ╱  ╲    ╱  ╲
                             ╱    ╲  ╱    ╲
                            ╱      ╲╱      ╲
                     🐳 SANDBOX ──────── SECRETS 🗝️
                        
           "Per aspera ad securitatem" — Through hardship to security
```

### The Five Points of Protection

| Point | Guardian | Power | Patterns |
|-------|----------|-------|----------|
| 🔐 **ACCESS** | DM Policy | Who enters the circle | pairing/allowlist |
| 🛡️ **INPUT** | Validators | What darkness they bring | 247 + 19 patterns |
| 🐳 **SANDBOX** | Docker | Contain the chaos | 512MB, 50% CPU |
| 🗝️ **SECRETS** | Proxy | Keys remain hidden | 0 secrets in agent |
| 🔒 **OUTPUT** | Sanitizer | Nothing escapes unseen | base64/hex detect |

## Цикл эволюции — The Eternal Vigil 🕯️

```
              ╭─────────────────────────────────────╮
              │         ① 👁️ OBSERVE               │
              │    "Watch the shadows move"        │
              │    docker logs -f | grep SECURITY  │
              ╰──────────────┬──────────────────────╯
                             │
         ╭───────────────────┼───────────────────╮
         │                   │                   │
         ▼                   ▼                   ▼
    ┌─────────┐        ┌─────────┐        ┌─────────┐
    │[BLOCKED]│        │[INJECT] │        │ [DENY]  │
    │ Command │        │ Prompt  │        │  Tool   │
    └────┬────┘        └────┬────┘        └────┬────┘
         │                   │                   │
         ╰───────────────────┼───────────────────╯
                             │
              ╭──────────────▼──────────────────────╮
              │         ② 🔮 DIVINE                │
              │    "Understand the attack"         │
              │    Analyze pattern, find weakness  │
              ╰──────────────┬──────────────────────╯
                             │
              ╭──────────────▼──────────────────────╮
              │         ③ ⚔️ FORTIFY               │
              │    "Strengthen the seals"          │
              │    Add pattern to blocked-*.json   │
              ╰──────────────┬──────────────────────╯
                             │
              ╭──────────────▼──────────────────────╮
              │         ④ 🔥 REBIRTH               │
              │    "Rise anew, stronger"           │
              │    docker compose up -d --build    │
              ╰──────────────┬──────────────────────╯
                             │
              ╭──────────────▼──────────────────────╮
              │         ⑤ ⛧ VERIFY                 │
              │    "The Pentagram must hold"       │
              │    python scripts/doctor.py        │
              ╰──────────────┬──────────────────────╯
                             │
                             ╰──────────▶ ① (eternal loop)
```

## Ключевые файлы для патчинга

| Файл | Что патчить |
|------|-------------|
| `core/src/approvals/blocked-patterns.json` | 247 security patterns |
| `bot/prompt-injection-patterns.json` | 19 injection patterns |
| `core/tools/permissions.py` | Tool allowlist/denylist |
| `bot/access.py` | DM Policy (pairing/allowlist) |
| `core/src/agent/system.txt` | Системный промпт |
| `scripts/doctor.py` | Security audit CLI |

## Access Control Commands

```bash
# Show access status (admin only)
/access

# Change mode
/access_mode admin      # Only admin
/access_mode allowlist  # Admin + allowed users
/access_mode pairing    # OpenClaw-style pairing codes
/access_mode public     # Anyone (⚠️ risky)

# Approve pairing code
/approve ABC123

# Revoke user
/revoke 123456789

# Add to allowlist
/allow 123456789
```

## Security Audit

```bash
# Run security doctor
python scripts/doctor.py

# Output as JSON
python scripts/doctor.py --json

# Checks performed:
# - Secrets configuration
# - Docker compose security
# - Blocked patterns (247)
# - Injection patterns (19)
# - Network exposure
# - File permissions
# - Access mode
# - Resource limits
```

## Tool Permissions by Session Type

| Session | Available Tools | Denied Tools |
|---------|----------------|--------------|
| **Main (DM)** | All 17 | - |
| **Group** | 14 | send_dm, manage_message, schedule_task |
| **Sandbox** | 10 | telegram tools, scheduler |
| **Userbot** | 13 | send_file, send_dm, manage_message, ask_user |

## Архитектура безопасности

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Gateway   │────▶│    Proxy    │────▶│  External   │
│  (Bot+Agent)│     │ (API Keys)  │     │    APIs     │
│  0 secrets  │     │  /run/sec/  │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
       │
       ▼
┌─────────────┐
│  /workspace │
│  per-user   │
│  isolated   │
└─────────────┘
```

## Команды мониторинга

```bash
# Security audit
python scripts/doctor.py

# Логи в реальном времени
docker logs gateway -f --tail 100

# Проверить что контейнеры живы
docker ps

# Перезапуск после патча
docker compose down && docker compose up -d --build

# Посмотреть историю чата
cat workspace/_shared/CHAT_HISTORY.md | tail -100

# Посмотреть pairing коды (admin)
cat workspace/_shared/pairing.json
```

## При падении сервера

1. `docker ps` - все контейнеры должны быть Up
2. `docker logs gateway` - проверить ошибки
3. `python scripts/doctor.py` - security audit
4. Если OOM - увеличить memory limit в docker-compose.yml
5. Если rate limit - увеличить интервалы в `src/config.ts`

## Centralized Config

Все настройки в `src/config.ts`:
- Rate limits, timeouts, agent behavior
- Reactions, thoughts, messages
- Storage limits (chat history, memory)
- Admin ID, valid emojis

## Comparison with OpenClaw

| Feature | LocalTopSH | OpenClaw |
|---------|------------|----------|
| DM Policy | ✅ admin/allowlist/public/pairing | ✅ pairing/allowlist/open |
| Sandbox | ✅ Docker per-user | ✅ Docker per-session |
| Blocked Patterns | 247 | ~200 |
| Prompt Injection | 19 patterns | ~20 patterns |
| Tool Permissions | ✅ by session type | ✅ similar |
| Security Audit CLI | ✅ `python scripts/doctor.py` | ✅ `openclaw doctor` |
| Multi-channel | Telegram only | 12+ channels |
| Admin Panel | ✅ React :3000 | ✅ Control UI |
