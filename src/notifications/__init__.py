"""
Notification System for OpenClaw Telegram Bridge

Provides beautiful message formatting, inline keyboards, progress bars,
and different notification types for the Telegram bot.

Example Usage:
    from src.notifications import NotificationManager, NotificationType, TaskInfo
    
    # Initialize manager
    manager = NotificationManager(bot, chat_id="YOUR_CHAT_ID")
    
    # Send task started notification
    task = TaskInfo(id="123", description="Create backup script")
    await manager.send_task_started(task)
    
    # Send progress updates
    await manager.send_progress("123", current=50, total=100, description="Processing files")
    
    # Send question with inline keyboard
    await manager.send_question(
        question_id="q1",
        question_text="Include database dumps?",
        options=[
            QuestionOption("Yes", "db_yes", "✅"),
            QuestionOption("No", "db_no", "❌"),
            QuestionOption("Both", "db_both", "📋")
        ]
    )
    
    # Send completion notification
    await manager.send_task_completed(task)
"""

from .formatter import (
    NotificationFormatter,
    NotificationType,
    TaskInfo,
    QuestionOption,
    FileAttachment,
    # Convenience functions
    info,
    success,
    warning,
    error,
    task_started,
    task_completed,
    task_failed,
    progress,
    question,
    yes_no_keyboard,
)

from .manager import (
    NotificationManager,
    MessageState,
    PendingQuestion,
)

__all__ = [
    # Classes
    "NotificationFormatter",
    "NotificationManager",
    "NotificationType",
    "TaskInfo",
    "QuestionOption",
    "FileAttachment",
    "MessageState",
    "PendingQuestion",
    
    # Convenience functions
    "info",
    "success",
    "warning",
    "error",
    "task_started",
    "task_completed",
    "task_failed",
    "progress",
    "question",
    "yes_no_keyboard",
]

__version__ = "1.0.0"
