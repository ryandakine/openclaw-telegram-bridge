# OpenClaw Telegram Bridge — AI Assistant Guide

## Project Overview

A bidirectional Telegram bot bridge connecting the user (Ryan) to Kimi Code CLI (an AI coding assistant running on the workstation). Enables remote task assignment, async Q&A between user and Kimi, and progress notifications from a phone.

This is intentionally a simple, local, file-based system with no external service dependencies beyond Telegram's Bot API.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| Bot framework | python-telegram-bot v20+ (async) |
| Message queue | File-based JSON + SQLite (no Redis) |
| Async runtime | asyncio |
| HTTP client | aiohttp |
| File I/O | aiofiles |
| Config | python-dotenv |

## Repository Structure

```
bot.py           Main Telegram bot — command handlers, polling loop
bridge.py        CLI integration layer called directly by Kimi Code CLI
config.py        Configuration management
queue_manager.py Atomic JSON queue read/write
src/             Additional source modules
storage/
  queue.json     Pending tasks: user → Kimi
  responses.json Completed results + notifications: Kimi → user
logs/            Rotating log files
tests/           Test suite
```

## Key Commands

```bash
pip install -r requirements.txt
cp .env.example .env     # Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID

python bot.py

# CLI commands called by Kimi Code CLI
python bridge.py                         # Process queue / show pending items
python bridge.py list                    # Show all pending tasks
python bridge.py complete <id> "result"  # Mark task done, notify user via Telegram
python bridge.py ask "question"          # Send clarifying question to user via Telegram

# System service
sudo systemctl enable openclaw-telegram-bridge
sudo systemctl start openclaw-telegram-bridge
```

## How It Works

### User → Kimi
1. User sends /task command to Telegram bot
2. bot.py appends task to storage/queue.json
3. Kimi Code CLI calls python bridge.py to check for pending items
4. Kimi processes the task
5. Kimi calls python bridge.py complete <id> "result"
6. bridge.py sends result back to user via Telegram

### Kimi → User (Questions)
1. Kimi calls python bridge.py ask "Do you want X or Y?"
2. bridge.py sends question to user's Telegram chat
3. User replies in Telegram
4. bot.py stores reply in storage/responses.json
5. Kimi polls bridge.py and receives the answer

## Queue File Format (storage/queue.json)
```json
[{"id": "uuid", "task": "description", "status": "pending|in_progress|completed", "created_at": "ISO timestamp", "result": null}]
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| TELEGRAM_BOT_TOKEN | Bot token from @BotFather |
| TELEGRAM_CHAT_ID | Your personal chat ID (whitelist) |

## Security Model

Whitelist-only: only the single TELEGRAM_CHAT_ID configured in .env can send commands. All other chat IDs are silently ignored. Do not add multi-user support without redesigning the auth model.

## Testing

```bash
pytest tests/
```

## Design Decisions (Do Not Change Without Good Reason)

- File-based queue: Intentionally no Redis/RabbitMQ. Self-contained, zero external deps. Single-user use case does not need message broker throughput.
- No web server: bridge.py is a CLI tool called as a subprocess by Kimi. Avoids port management.
- systemd for auto-restart: Let systemd handle restarts. Do not add Python-level retry loops.

## Important Constraints

- Never add multi-user support without redesigning auth.
- Queue writes must be atomic — use queue_manager.py; never write to queue files directly.
- bridge.py must remain a CLI tool — it is called as a subprocess by external AI tools.
- No external service dependencies — the file-based queue is a feature.
