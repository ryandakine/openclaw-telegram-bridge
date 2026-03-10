# OpenClaw Telegram Bridge - Notification System

A comprehensive notification and alert system for the OpenClaw Telegram Bridge with beautiful message formatting, inline keyboards, progress bars, and multiple notification types.

## Features

### ✅ Task Notifications
- **Task Started**: 🚀 Animated notification with task ID and start time
- **Task Completed**: ✨ Shows duration, files created, and summary
- **Task Failed**: 💥 Error details with retry/view logs buttons

### ✅ Question Prompts with Inline Keyboards
- Yes/No/More options with emojis
- Multiple layout options: horizontal, vertical, grid
- Callback data handling with timeout support
- Context information for complex questions

### ✅ Progress Updates for Long Tasks
- Visual progress bars with Unicode blocks (█░)
- ETA calculation and display
- Real-time message updates
- Cancel/View Details action buttons

### ✅ Error Alerts
- Formatted error messages with context
- Stack trace truncation for long errors
- Suggestion display for common issues
- Get Help / Report Issue buttons

### ✅ Additional Features
- File attachment notifications
- System status updates
- General info/success/warning notifications
- HTML escaping for security
- Message truncation for Telegram limits
- Reply keyboards for quick commands

## Quick Start

```python
from src.notifications import NotificationManager, NotificationType, TaskInfo

# Initialize manager
manager = NotificationManager(bot, chat_id="YOUR_CHAT_ID")

# Send task notification
task = TaskInfo(id="123", description="Create backup script")
await manager.send_task_started(task)

# Update progress
await manager.send_progress("123", current=50, total=100, description="Processing")

# Ask question with inline keyboard
await manager.send_question(
    question_id="q1",
    question_text="Include database dumps?",
    options=[
        QuestionOption("Yes", "db_yes", "✅"),
        QuestionOption("No", "db_no", "❌"),
    ]
)

# Send completion
await manager.send_task_completed(task)
```

## Message Formats

### Task Started
```
🚀 Task Started!

📋 Description: Create Python backup script
🆔 Task ID: #TASK-001
⏱️ Started: 2025-03-10 10:30:00

I'll notify you when it's complete.
[Cancel button]
```

### Progress Update
```
📊 Progress Update

📋 Task: Processing database records

[████████░░░░░░░░░░░░] 40%

📊 Completed: 40/100
⏱️ ETA: 2m 30s

[View Details] [Cancel Task]
```

### Question Prompt
```
❓ I need clarification:

Should the backup include database dumps?
Context: This will add ~500MB to each backup

Options:
• 🗄️ Database only
• 📁 Files only  
• 📦 Both

Tap a button below or reply with your answer.
[Yes] [No] [More options...]
```

### Error Alert
```
❌ Error Alert

<pre>Connection timeout after 30s</pre>
Context: Database connection attempt

💡 Suggestion: Check network settings
[Get Help] [Report Issue]
```

## API Reference

### NotificationFormatter

Core formatting class with static methods:

- `format_task_started(task)` - Task start notification
- `format_task_completed(task)` - Task completion notification
- `format_task_failed(task)` - Task failure notification
- `format_question(question, options, context)` - Question with options
- `format_progress(current, total, description, eta, extra)` - Progress bar
- `format_error_alert(error, context, suggestion)` - Error alert
- `format_status_update(working_dir, active_tasks, completed)` - System status
- `format_file_notification(file, size, action, caption)` - File notification

### NotificationManager

High-level manager for sending messages:

- `send_task_started(task)` - Send with cancel button
- `send_task_completed(task)` - Send with action buttons
- `send_task_failed(task)` - Send with retry button
- `send_question(...)` - Send with inline keyboard
- `send_progress(...)` - Send/update progress message
- `send_error_alert(...)` - Send error with help buttons
- `send_file(...)` - Send file attachment
- `handle_callback_query(update, context)` - Handle button clicks

### Keyboard Builders

- `create_yes_no_keyboard(yes_cb, no_cb, more_cb)` - Standard yes/no
- `create_inline_keyboard(options, layout)` - Custom options
- `create_progress_keyboard(task_id)` - Progress actions
- `create_quick_commands_keyboard()` - Common commands

## Convenience Functions

Quick one-liners for common notifications:

```python
from notifications import (
    info, success, warning, error,
    task_started, task_completed, task_failed,
    progress, question, yes_no_keyboard
)

# Quick notifications
message = info("System initialized")
message = success("Task completed!")
message = warning("Low disk space")
message = error("Connection failed")

# Quick task notifications
message = task_started("TASK-001", "Backup database")
message = task_completed("TASK-001", "Backup database", duration_minutes=5.2)
message = task_failed("TASK-001", "Backup database", "Permission denied")

# Quick progress
message = progress(75, 100, "Uploading", eta_seconds=120)

# Quick question
message = question("Continue?")
keyboard = yes_no_keyboard()
```

## Testing

Run the test suite:

```bash
# Run all tests
python -m pytest tests/test_notifications.py -v

# Run examples/demo
python -c "
import sys
sys.path.insert(0, 'src')
from notifications.examples import run_all_demos
run_all_demos()
"
```

## File Structure

```
src/notifications/
├── __init__.py          # Package exports
├── formatter.py         # Message formatting
├── manager.py           # Notification manager
├── examples.py          # Usage examples
└── README.md            # This file
```

## Integration

See `src/bot_integration.py` for a complete bot integration example.

```python
from telegram.ext import Application
from notifications import NotificationManager

# Initialize
app = Application.builder().token(TOKEN).build()
manager = NotificationManager(bot=app.bot, chat_id=CHAT_ID)

# Use in handlers
async def task_handler(update, context):
    task = TaskInfo(id="123", description="Do something")
    await manager.send_task_started(task)
```

## License

Part of the OpenClaw Telegram Bridge project.
