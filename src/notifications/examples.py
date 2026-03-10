"""
Example usage and demonstrations of the Notification System.

Run this file to see example message formats:
    python src/notifications/examples.py
"""

import asyncio
from datetime import datetime

from .formatter import (
    NotificationFormatter,
    NotificationType,
    TaskInfo,
    QuestionOption,
    info, success, warning, error,
    task_started, task_completed, task_failed,
    progress, question, yes_no_keyboard
)


def print_header(text: str):
    """Print a header for examples."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_separator():
    """Print a separator between examples."""
    print("\n" + "-" * 40 + "\n")


def demo_task_notifications():
    """Demonstrate task notification formats."""
    print_header("TASK NOTIFICATIONS")
    
    # Task Started
    task = TaskInfo(
        id="TASK-001",
        description="Create Python backup script for database",
        status="in_progress",
        created_at=datetime.now()
    )
    
    print("📤 TASK STARTED:")
    print(NotificationFormatter.format_task_started(task))
    print_separator()
    
    # Task Completed
    task_completed_info = TaskInfo(
        id="TASK-001",
        description="Create Python backup script for database",
        status="completed",
        duration_minutes=8.5,
        files_created=["backup.py", "config.yaml", "requirements.txt"],
        result_summary="Daily backup at 2 AM\nGzip compression enabled\n7-day retention policy"
    )
    
    print("✅ TASK COMPLETED:")
    print(NotificationFormatter.format_task_completed(task_completed_info))
    print_separator()
    
    # Task Failed
    task_failed_info = TaskInfo(
        id="TASK-002",
        description="Deploy application to production",
        status="failed",
        error_message="Connection timeout after 30 seconds. Server at 192.168.1.100 not responding."
    )
    
    print("❌ TASK FAILED:")
    print(NotificationFormatter.format_task_failed(task_failed_info))


def demo_question_prompts():
    """Demonstrate question prompt formats."""
    print_header("QUESTION PROMPTS WITH INLINE KEYBOARDS")
    
    # Simple yes/no question
    print("❓ YES/NO QUESTION:")
    message = NotificationFormatter.format_question(
        question="Should the backup include database dumps?",
        context="This will add ~500MB to each backup"
    )
    print(message)
    print("\nKeyboard Layout (horizontal):")
    keyboard = NotificationFormatter.create_yes_no_keyboard()
    for row in keyboard:
        print(f"  Row: {row}")
    print_separator()
    
    # Multiple options
    print("📋 MULTIPLE OPTIONS:")
    options = [
        QuestionOption("Database only", "opt_db", "🗄️"),
        QuestionOption("Files only", "opt_files", "📁"),
        QuestionOption("Both", "opt_both", "📦"),
        QuestionOption("Cancel", "opt_cancel", "❌"),
    ]
    message = NotificationFormatter.format_question(
        question="What should be included in the backup?",
        options=options
    )
    print(message)
    print("\nKeyboard Layout (grid):")
    keyboard = NotificationFormatter.create_inline_keyboard(options, layout="grid")
    for row in keyboard:
        print(f"  Row: {row}")


def demo_progress_updates():
    """Demonstrate progress update formats."""
    print_header("PROGRESS UPDATES")
    
    # 25% progress
    print("📊 PROGRESS AT 25%:")
    print(NotificationFormatter.format_progress(
        current=25,
        total=100,
        description="Processing database records",
        eta_seconds=180,
        extra_info="Table: users, Records processed: 25,000"
    ))
    print_separator()
    
    # 50% progress
    print("📊 PROGRESS AT 50%:")
    print(NotificationFormatter.format_progress(
        current=50,
        total=100,
        description="Generating backup archive",
        eta_seconds=120
    ))
    print_separator()
    
    # 100% progress
    print("📊 PROGRESS AT 100%:")
    print(NotificationFormatter.format_progress(
        current=100,
        total=100,
        description="Uploading to cloud storage",
        eta_seconds=0
    ))
    print_separator()
    
    # Progress with keyboard
    print("📊 PROGRESS WITH KEYBOARD:")
    keyboard = NotificationFormatter.create_progress_keyboard("TASK-003")
    print("Keyboard:")
    for row in keyboard:
        print(f"  {row}")


def demo_error_alerts():
    """Demonstrate error alert formats."""
    print_header("ERROR ALERTS")
    
    # Simple error
    print("❌ SIMPLE ERROR:")
    print(NotificationFormatter.format_error_alert(
        error="Failed to connect to database"
    ))
    print_separator()
    
    # Error with context and suggestion
    print("❌ ERROR WITH CONTEXT & SUGGESTION:")
    print(NotificationFormatter.format_error_alert(
        error="Repository not found: openclaw-telegram-bridge",
        context="Attempting to create pull request",
        suggestion="Check the repository name and ensure you have access rights"
    ))
    print_separator()
    
    # Error with stack trace (truncated)
    print("❌ ERROR WITH STACK TRACE:")
    stack_trace = """Traceback (most recent call last):
  File "bot.py", line 42, in handle_command
    result = process_task(task_id)
  File "tasks.py", line 156, in process_task
    raise TaskError("Processing failed")
TaskError: Processing failed after 3 retries"""
    print(NotificationFormatter.format_error_alert(
        error=stack_trace,
        context="Task processing",
        suggestion="Check task configuration and retry"
    ))


def demo_status_updates():
    """Demonstrate status update formats."""
    print_header("STATUS UPDATES")
    
    active_tasks = [
        TaskInfo(id="T001", description="Create notification system for Telegram bot"),
        TaskInfo(id="T002", description="Implement progress bars with visual indicators"),
    ]
    
    recent_completed = [
        TaskInfo(id="T000", description="Set up project structure and initial files"),
    ]
    
    print("🔧 SYSTEM STATUS:")
    print(NotificationFormatter.format_status_update(
        working_dir="/home/ryan/openclaw-telegram-bridge",
        active_tasks=active_tasks,
        recent_completed=recent_completed,
        system_status="🟢 Online"
    ))


def demo_file_notifications():
    """Demonstrate file notification formats."""
    print_header("FILE NOTIFICATIONS")
    
    print("📁 FILE RECEIVED:")
    print(NotificationFormatter.format_file_notification(
        file_name="database_backup_2025-03-10.sql.gz",
        file_size="15.4 MB",
        action="received",
        caption="Database backup from production server"
    ))
    print_separator()
    
    print("📁 FILE SENT:")
    print(NotificationFormatter.format_file_notification(
        file_name="report.pdf",
        file_size="2.1 MB",
        action="sent"
    ))


def demo_general_notifications():
    """Demonstrate general notification formats."""
    print_header("GENERAL NOTIFICATIONS")
    
    print("ℹ️ INFO:")
    print(info("Bot is initializing...", "System Info"))
    print_separator()
    
    print("✅ SUCCESS:")
    print(success("Configuration saved successfully!", "Saved"))
    print_separator()
    
    print("⚠️ WARNING:")
    print(warning("Low disk space: 15% remaining", "Storage Warning"))
    print_separator()
    
    print("❌ ERROR:")
    print(error("Failed to save file: Permission denied", "Save Failed"))


def demo_convenience_functions():
    """Demonstrate convenience functions."""
    print_header("CONVENIENCE FUNCTIONS")
    
    print("Quick task started:")
    print(task_started("TASK-123", "Deploy to production"))
    print_separator()
    
    print("Quick task completed:")
    print(task_completed(
        task_id="TASK-123",
        description="Deploy to production",
        duration_minutes=5.2,
        files_created=["deploy.log"],
        result_summary="Successfully deployed v1.2.3"
    ))
    print_separator()
    
    print("Quick task failed:")
    print(task_failed(
        task_id="TASK-124",
        description="Database migration",
        error_message="Table 'users' already exists"
    ))
    print_separator()
    
    print("Quick progress:")
    print(progress(75, 100, "Uploading files", eta_seconds=45))
    print_separator()
    
    print("Quick question:")
    print(question("Continue with deployment?"))
    print("\nKeyboard:", yes_no_keyboard())


def demo_inline_keyboards():
    """Demonstrate different keyboard layouts."""
    print_header("INLINE KEYBOARD LAYOUTS")
    
    options = [
        QuestionOption("Option 1", "opt1", "1️⃣"),
        QuestionOption("Option 2", "opt2", "2️⃣"),
        QuestionOption("Option 3", "opt3", "3️⃣"),
        QuestionOption("Option 4", "opt4", "4️⃣"),
    ]
    
    print("HORIZONTAL (all in one row):")
    keyboard = NotificationFormatter.create_inline_keyboard(options, "horizontal")
    for row in keyboard:
        print(f"  {row}")
    print_separator()
    
    print("VERTICAL (each in own row):")
    keyboard = NotificationFormatter.create_inline_keyboard(options, "vertical")
    for row in keyboard:
        print(f"  {row}")
    print_separator()
    
    print("GRID (2 per row):")
    keyboard = NotificationFormatter.create_inline_keyboard(options, "grid")
    for row in keyboard:
        print(f"  {row}")
    print_separator()
    
    print("YES/NO with MORE:")
    keyboard = NotificationFormatter.create_yes_no_keyboard(
        more_callback="more_options"
    )
    for row in keyboard:
        print(f"  {row}")


def run_all_demos():
    """Run all demonstration functions."""
    print("\n" + "🚀" * 30)
    print("  OPENCLAW TELEGRAM BRIDGE - NOTIFICATION SYSTEM DEMO")
    print("🚀" * 30)
    
    demo_task_notifications()
    demo_question_prompts()
    demo_progress_updates()
    demo_error_alerts()
    demo_status_updates()
    demo_file_notifications()
    demo_general_notifications()
    demo_convenience_functions()
    demo_inline_keyboards()
    
    print("\n" + "=" * 60)
    print("  DEMO COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    run_all_demos()
