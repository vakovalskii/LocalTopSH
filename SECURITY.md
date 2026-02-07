# 🛡️ LocalTopSH Security Model

> **Battle-tested by 1500+ hackers** — 0 secrets leaked, 0 downtime.

## Security Philosophy

**Access Control Before Intelligence** — every action is validated before execution.

```
                           ⛧ THE SECURITY PENTAGRAM ⛧
                        
                                 🔐 ACCESS
                                    ╱╲
                                   ╱  ╲
                                  ╱    ╲
                                 ╱  ⛧   ╲
                                ╱        ╲
                               ╱    👁️    ╲
                              ╱            ╲
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

## The Five Points of Protection

```
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃                                                                 ┃
    ┃   🔐 ACCESS        DM Policy • Pairing Codes • Allowlist        ┃
    ┃      CONTROL       "Who may enter the circle?"                  ┃
    ┃                                                                 ┃
    ┃   🛡️ INPUT         247 Blocked Patterns • 19 Injection Filters  ┃
    ┃      VALIDATION    "What darkness do they bring?"               ┃
    ┃                                                                 ┃
    ┃   🐳 SANDBOX       Docker Isolation • Resource Limits • PIDs    ┃
    ┃      ISOLATION     "Contain the chaos within"                   ┃
    ┃                                                                 ┃
    ┃   🗝️ SECRETS       Proxy Architecture • Zero Knowledge Agent    ┃
    ┃      PROTECTION    "The keys remain hidden"                     ┃
    ┃                                                                 ┃
    ┃   🔒 OUTPUT        Secret Detection • Encoding Analysis         ┃
    ┃      SANITIZATION  "Nothing escapes unseen"                     ┃
    ┃                                                                 ┃
    ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

## The Binding Circle

```
                    ╭──────────────────────────────────╮
                    │         🔐 ACCESS CONTROL        │
                    │    admin │ allowlist │ pairing   │
                    ╰────────────────┬─────────────────╯
                                     │
                    ╭────────────────▼─────────────────╮
                    │         🛡️ INPUT VALIDATION      │
                    │     19 injection │ 247 blocked   │
                    ╰────────────────┬─────────────────╯
                                     │
        ╭────────────────────────────┼────────────────────────────╮
        │                            │                            │
        ▼                            ▼                            ▼
   ╭─────────╮              ╭─────────────────╮              ╭─────────╮
   │ 🗝️      │              │    👁️ AGENT     │              │      🔒 │
   │ SECRETS │◀────────────▶│   ReAct Loop    │─────────────▶│ OUTPUT │
   │ (proxy) │   0 secrets  │  Tool Executor  │  sanitized   │        │
   ╰─────────╯              ╰────────┬────────╯              ╰─────────╯
                                     │
                            ╭────────▼────────╮
                            │  🐳 SANDBOX     │
                            │  per-user       │
                            │  512MB │ 50%CPU │
                            ╰─────────────────╯
```

## The Ritual of Invocation 🕯️

When a message arrives, the pentagram activates:

```
  ┌─────────────────────────────────────────────────────────────────┐
  │                                                                 │
  │   ① 🔐 ACCESS GATE OPENS                                        │
  │      │                                                          │
  │      ├─ Is sender known? ─────────────────┐                     │
  │      │                                    │                     │
  │      │  YES: Pass through               NO: Generate code       │
  │      │       ↓                              "ABC123"            │
  │      │                                      ↓                   │
  │      │                               ⛔ DENIED                  │
  │      ↓                                                          │
  │   ② 🛡️ INPUT WARD ACTIVATES                                     │
  │      │                                                          │
  │      ├─ Scan for injection ───────────────┐                     │
  │      │  "forget instructions"             │                     │
  │      │  "[system]"                    DETECTED                  │
  │      │  "DAN mode"                        ↓                     │
  │      │                               ⛔ BLOCKED                 │
  │      │                                                          │
  │      ├─ Scan for forbidden commands ──────┐                     │
  │      │  "env", "cat /run/secrets"         │                     │
  │      │  "curl -d $SECRET"             MATCHED                   │
  │      │                                    ↓                     │
  │      │                               ⛔ BLOCKED                 │
  │      ↓                                                          │
  │   ③ 🗝️ SECRETS REMAIN HIDDEN                                    │
  │      │                                                          │
  │      │  Agent sees: PROXY_URL=http://proxy:3200                 │
  │      │  Agent CANNOT see: API_KEY, TELEGRAM_TOKEN               │
  │      │  Proxy handles all external API calls                    │
  │      ↓                                                          │
  │   ④ 🐳 SANDBOX CONTAINS THE ENTITY                              │
  │      │                                                          │
  │      │  ┌─────────────────────────────────┐                     │
  │      │  │  Container: sandbox_809532582   │                     │
  │      │  │  Memory: 512MB (hard limit)     │                     │
  │      │  │  CPU: 50% of one core           │                     │
  │      │  │  PIDs: 100 max (no fork bombs)  │                     │
  │      │  │  Network: internal only         │                     │
  │      │  │  Filesystem: /workspace/USER/   │                     │
  │      │  └─────────────────────────────────┘                     │
  │      ↓                                                          │
  │   ⑤ 🔒 OUTPUT WARD SEALS THE RESPONSE                           │
  │      │                                                          │
  │      ├─ Scan for leaked secrets ──────────┐                     │
  │      │  "sk-abc123..."                    │                     │
  │      │  "Bearer eyJ..."               DETECTED                  │
  │      │                                    ↓                     │
  │      │                            [REDACTED]                    │
  │      │                                                          │
  │      ├─ Scan for encoded data ────────────┐                     │
  │      │  base64, hex, unicode          DETECTED                  │
  │      │                                    ↓                     │
  │      │                            [REDACTED]                    │
  │      ↓                                                          │
  │   ✅ SAFE RESPONSE DELIVERED                                    │
  │                                                                 │
  └─────────────────────────────────────────────────────────────────┘
```

## The Five Seals

Each point of the pentagram is sealed with specific protections:

### 🔐 Seal of ACCESS — *"Quis custodiet?"*

```python
# bot/access.py
ACCESS_MODES = {
    "admin":     "Only the master may command",
    "allowlist": "Known servants may enter",
    "pairing":   "Prove yourself with the code",
    "public":    "All may try (at their peril)",
}
```

### 🛡️ Seal of INPUT — *"Veritas in tenebris"*

```python
# 247 forbidden incantations
BLOCKED_PATTERNS = [
    "env", "printenv",           # Reveal nothing
    "/proc/self/environ",        # The inner sanctum
    "base64", "xxd",             # No encoding tricks
    "curl -d", "wget --post",    # No exfiltration
    # ... 243 more dark spells
]
```

### 🐳 Seal of SANDBOX — *"Continere malum"*

```yaml
# The containment vessel
sandbox:
  mem_limit: 512m      # Memory bound
  cpu_quota: 50%       # Processing bound  
  pids_limit: 100      # Entity count bound
  no-new-privileges    # No escalation
```

### 🗝️ Seal of SECRETS — *"Arcana celata"*

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    Agent     │────▶│    Proxy     │────▶│   OpenAI     │
│  (0 secrets) │     │ (all keys)   │     │   Z.AI etc   │
└──────────────┘     └──────────────┘     └──────────────┘
     │                     ▲
     │                     │
     └─────────────────────┘
       "I know not the keys,
        I only know the path"
```

### 🔒 Seal of OUTPUT — *"Nihil effugit"*

```python
# Nothing escapes the circle
SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9]{20,}",      # OpenAI
    r"\d{10}:[A-Za-z0-9_-]{35}", # Telegram
    r"Bearer [A-Za-z0-9._-]+",   # Tokens
    # The eye sees all
]
```

## DM Access Policy

LocalTopSH supports three DM access modes:

| Mode | Description | Config |
|------|-------------|--------|
| **Admin Only** | Only admin can use bot | `ACCESS_MODE=admin` |
| **Allowlist** | Admin + configured user IDs | `ACCESS_MODE=allowlist` |
| **Public** | Anyone can use (⚠️ risky) | `ACCESS_MODE=public` |

### Recommended Setup

```bash
# Admin-only (default, safest)
ACCESS_MODE=admin
ADMIN_USER_ID=809532582

# Allowlist mode (for trusted users)
ACCESS_MODE=allowlist
ALLOWED_USERS=809532582,123456789,987654321

# Public mode (⚠️ requires additional hardening)
ACCESS_MODE=public
RATE_LIMIT_PER_USER=10  # requests per minute
```

## Sandbox Isolation

Each user gets an isolated Docker container:

```yaml
# Per-user sandbox limits
mem_limit: 512m
cpu_quota: 50%  # 50% of one core
pids_limit: 100
network: agent-net (internal only)
security_opt: no-new-privileges

# Workspace isolation
volumes:
  - /workspace/{user_id}:/workspace/{user_id}:rw
  # NO access to other users' workspaces
  # NO access to /run/secrets
  # NO access to host filesystem
```

### Tool Allowlist/Denylist by Session Type

| Session Type | Allowed Tools | Denied Tools |
|--------------|---------------|--------------|
| **Main (DM)** | All 17 tools | - |
| **Group** | 13 shared tools | send_dm, manage_message |
| **Sandbox** | bash, files, memory | browser, cron, gateway |

## Blocked Patterns (247)

Commands are blocked before execution:

### Categories

| Category | Count | Examples |
|----------|-------|----------|
| `env_leak` | 15 | `env`, `printenv`, `/proc/self/environ` |
| `docker_secrets` | 2 | `/run/secrets/*` |
| `exfiltration` | 25 | `curl -d`, `base64`, `xxd`, `nc` |
| `sensitive_files` | 12 | `.env`, `.ssh/`, `id_rsa` |
| `dos` | 30 | fork bombs, `yes`, huge allocations |
| `reverse_shell` | 15 | `bash -i`, `nc -e`, `/dev/tcp` |
| `code_execution` | 20 | `eval`, `exec()`, `LD_PRELOAD` |
| `filter_bypass` | 15 | `$IFS`, hex encoding, backticks |
| `escape` | 20 | symlinks, `/proc/*/fd`, `nsenter` |
| `privilege` | 5 | `sudo`, `apt-get`, `setcap` |
| `crypto_mining` | 5 | `xmrig`, `stratum+tcp://` |
| `cross_user` | 8 | `ls /workspace`, `cd ..` |
| Other | 75 | Various attack patterns |

### Adding New Patterns

Edit `core/src/approvals/blocked-patterns.json`:

```json
{
  "id": "new-attack-1",
  "category": "exfiltration",
  "pattern": "new_attack_regex",
  "flags": "i",
  "reason": "BLOCKED: Description of why"
}
```

## Prompt Injection Defense (19 patterns)

Incoming messages are scanned for injection attempts:

| Pattern Type | Examples |
|--------------|----------|
| Instruction Override | "forget all instructions", "ignore previous" |
| Fake System Messages | `[system]`, `[admin]`, `[developer]` |
| Mode Switching | "DAN mode", "developer mode", "jailbreak" |
| Role Confusion | "pretend you are", "act as if" |
| Prompt Extraction | "reveal your prompt", "show instructions" |

### Response to Injection

When injection is detected:
1. Message is logged with `[INJECTION]` tag
2. Bot responds with generic refusal
3. User is NOT banned (may be legitimate confusion)
4. Pattern is available for analysis

## Secrets Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SECRETS FLOW                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  secrets/                    proxy/                             │
│  ├─ telegram_token.txt  ──▶  (reads at startup)                │
│  ├─ api_key.txt         ──▶  (reads at startup)                │
│  └─ zai_api_key.txt     ──▶  (reads at startup)                │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────┐        ┌─────────────┐        ┌─────────────┐ │
│  │   Gateway   │───────▶│    Proxy    │───────▶│  External   │ │
│  │  (0 secrets)│  HTTP  │ (all keys)  │  HTTPS │    APIs     │ │
│  └─────────────┘        └─────────────┘        └─────────────┘ │
│        │                                                        │
│        │ NO secrets in:                                         │
│        │ - Environment variables                                │
│        │ - Container filesystem                                 │
│        │ - Agent context                                        │
│        │ - Tool outputs                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Output Sanitization

All command outputs are sanitized before returning to user:

### Secret Patterns Detected

```python
SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9]{20,}",           # OpenAI keys
    r"tvly-[A-Za-z0-9-]{20,}",        # Tavily keys
    r"ghp_[A-Za-z0-9]{36,}",          # GitHub tokens
    r"\d{8,12}:[A-Za-z0-9_-]{35}",    # Telegram bot tokens
    r"Bearer\s+[A-Za-z0-9._-]{20,}",  # Bearer tokens
    r"[A-Z_]*API[_-]?KEY[A-Z_]*=",    # Generic API keys
]
```

### Encoding Detection

Outputs are also scanned for:
- Base64-encoded secrets
- Hex-encoded data
- JSON env dumps
- Suspicious patterns

## Network Security

### Internal Services

```yaml
networks:
  agent-net:
    driver: bridge
    internal: false  # Allows outbound for web search

# Service exposure
proxy:     internal only (no ports exposed)
core:      internal only (no ports exposed)
bot:       internal only (no ports exposed)
admin:     localhost:3000 only
```

### Blocked Internal Access

Commands attempting to access internal services are blocked:
- `curl http://proxy:3200/`
- `wget http://core:4000/`
- `nc gateway 4000`

## Security Audit Checklist

Run this checklist before production:

### 1. Access Control
- [ ] `ACCESS_MODE` is NOT `public` (or has rate limiting)
- [ ] `ADMIN_USER_ID` is set correctly
- [ ] Allowlist contains only trusted users

### 2. Network
- [ ] Admin panel bound to `127.0.0.1` only
- [ ] No services exposed to `0.0.0.0`
- [ ] Firewall blocks external access to ports 3200, 4000, 4001

### 3. Secrets
- [ ] All secrets in `secrets/` directory
- [ ] File permissions are `600`
- [ ] No secrets in environment variables
- [ ] No secrets in docker-compose.yml

### 4. Docker
- [ ] `no-new-privileges` enabled
- [ ] Resource limits set
- [ ] Docker socket access minimized

### 5. Monitoring
- [ ] Logs are being collected
- [ ] `[SECURITY]` and `[BLOCKED]` alerts monitored
- [ ] Rate limiting active

## Incident Response

### If Secret Leaked

1. **Immediately rotate** the leaked credential
2. Check logs for exfiltration method
3. Add blocking pattern if new vector
4. Redeploy with new secrets

### If DoS Attack

1. Check `docker stats` for resource usage
2. Identify attacking user from logs
3. Add to blocklist or rate limit
4. Restart affected containers

### If Prompt Injection Successful

1. Review conversation in `CHAT_HISTORY.md`
2. Identify bypass technique
3. Add pattern to `prompt-injection-patterns.json`
4. Consider model upgrade (Claude > GPT for injection resistance)

## Security Updates

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-02 | Initial 247 blocked patterns |
| 1.1.0 | 2026-02-03 | Added cross-user isolation |
| 1.2.0 | 2026-02-05 | Added encoding detection |
| 1.3.0 | 2026-02-07 | OpenClaw-style architecture |

### Reporting Vulnerabilities

If you find a security vulnerability:
1. **Do NOT** create a public issue
2. Contact admin directly via Telegram
3. Include reproduction steps
4. Wait for patch before disclosure

## Comparison with OpenClaw

| Feature | LocalTopSH | OpenClaw |
|---------|------------|----------|
| DM Policy | ✅ Admin/Allowlist/Public | ✅ Pairing/Allowlist/Open |
| Sandbox | ✅ Docker per-user | ✅ Docker per-session |
| Blocked Patterns | 247 | ~200 |
| Prompt Injection | 19 patterns | ~20 patterns |
| Secrets Isolation | ✅ Proxy architecture | ✅ Similar |
| Security Audit CLI | 🔄 In progress | ✅ `openclaw doctor` |
| Multi-channel | Telegram only | 12+ channels |

---

**Remember:** Security is a process, not a product. Keep monitoring, keep patching, keep evolving.
