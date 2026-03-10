"""
Notification Formatter Module for OpenClaw Telegram Bridge

This module provides beautiful message formatting, inline keyboards,
progress bars, and different notification types for the Telegram bot.
"""

import json
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass, field


class NotificationType(Enum):
    """Types of notifications with associated emojis and styles."""
    INFO = ("ℹ️", "Info", "#3498db")
    SUCCESS = ("✅", "Success", "#2ecc71")
    WARNING = ("⚠️", "Warning", "#f39c12")
    ERROR = ("❌", "Error", "#e74c3c")
    TASK_START = ("🚀", "Task Started", "#9b59b6")
    TASK_COMPLETE = ("✨", "Task Complete", "#2ecc71")
    TASK_FAIL = ("💥", "Task Failed", "#e74c3c")
    QUESTION = ("❓", "Question", "#f1c40f")
    PROGRESS = ("📊", "Progress", "#3498db")
    FILE = ("📁", "File", "#95a5a6")
    SYSTEM = ("🔧", "System", "#34495e")

    def __init__(self, emoji: str, title: str, color: str):
        self.emoji = emoji
        self.title = title
        self.color = color


@dataclass
class TaskInfo:
    """Information about a task for notifications."""
    id: str
    description: str
    status: str = "pending"
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_minutes: Optional[float] = None
    result_summary: Optional[str] = None
    files_created: List[str] = field(default_factory=list)
    error_message: Optional[str] = None


@dataclass
class QuestionOption:
    """Option for inline keyboard questions."""
    text: str
    callback_data: str
    emoji: Optional[str] = None


@dataclass
class FileAttachment:
    """File attachment information."""
    file_path: str
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    caption: Optional[str] = None


class NotificationFormatter:
    """
    Formatter for creating beautiful Telegram messages with markdown,
    emojis, inline keyboards, and progress bars.
    """

    # Progress bar characters
    PROGRESS_FILL = "█"
    PROGRESS_EMPTY = "░"
    PROGRESS_WIDTH = 20

    @staticmethod
    def format_task_started(task: TaskInfo) -> str:
        """Format a task started notification."""
        emoji = NotificationType.TASK_START.emoji
        
        message = f"""{emoji} <b>Task Started!</b>

📋 <b>Description:</b> {NotificationFormatter._escape_html(task.description)}
🆔 <b>Task ID:</b> <code>#{task.id}</code>
⏱️ <b>Started:</b> {NotificationFormatter._format_time(datetime.now())}

I'll notify you when it's complete."""
        
        return message

    @staticmethod
    def format_task_completed(task: TaskInfo) -> str:
        """Format a task completed notification."""
        emoji = NotificationType.TASK_COMPLETE.emoji
        
        duration_text = ""
        if task.duration_minutes:
            if task.duration_minutes < 1:
                duration_text = f"{int(task.duration_minutes * 60)} seconds"
            elif task.duration_minutes < 60:
                duration_text = f"{int(task.duration_minutes)} minutes"
            else:
                hours = int(task.duration_minutes // 60)
                mins = int(task.duration_minutes % 60)
                duration_text = f"{hours}h {mins}m"
        
        files_text = ""
        if task.files_created:
            files_list = "\n• ".join(task.files_created)
            files_text = f"\n📁 <b>Files created:</b>\n• {files_list}\n"
        
        summary_text = ""
        if task.result_summary:
            summary_text = f"\n<b>Summary:</b>\n{NotificationFormatter._escape_html(task.result_summary)}\n"
        
        message = f"""{emoji} <b>Task Complete!</b>

📋 <b>Task:</b> {NotificationFormatter._escape_html(task.description)}
⏱️ <b>Duration:</b> {duration_text}{files_text}{summary_text}
Anything else you need?"""
        
        return message

    @staticmethod
    def format_task_failed(task: TaskInfo) -> str:
        """Format a task failed notification."""
        emoji = NotificationType.TASK_FAIL.emoji
        
        error_text = ""
        if task.error_message:
            # Truncate long error messages
            error = task.error_message[:500] + "..." if len(task.error_message) > 500 else task.error_message
            error_text = f"""
<b>Error Details:</b>
<pre>{NotificationFormatter._escape_html(error)}</pre>
"""
        
        message = f"""{emoji} <b>Task Failed</b>

📋 <b>Task:</b> {NotificationFormatter._escape_html(task.description)}
🆔 <b>Task ID:</b> <code>#{task.id}</code>{error_text}

Please check the logs or try again. Use /help for assistance."""
        
        return message

    @staticmethod
    def format_question(
        question: str, 
        options: Optional[List[QuestionOption]] = None,
        context: Optional[str] = None
    ) -> str:
        """Format a question with optional context."""
        emoji = NotificationType.QUESTION.emoji
        
        context_text = f"\n<b>Context:</b> {NotificationFormatter._escape_html(context)}\n" if context else ""
        
        options_text = ""
        if options:
            options_text = "\n<b>Options:</b>\n" + "\n".join([
                f"• {opt.emoji or '🔘'} {NotificationFormatter._escape_html(opt.text)}"
                for opt in options
            ])
        
        message = f"""{emoji} <b>I need clarification:</b>

{NotificationFormatter._escape_html(question)}{context_text}{options_text}

Tap a button below or reply with your answer."""
        
        return message

    @staticmethod
    def format_progress(
        current: int, 
        total: int, 
        description: str,
        eta_seconds: Optional[int] = None,
        extra_info: Optional[str] = None
    ) -> str:
        """Format a progress update with visual progress bar."""
        emoji = NotificationType.PROGRESS.emoji
        
        percentage = min(100, max(0, int((current / total) * 100))) if total > 0 else 0
        
        # Build progress bar
        filled = int((percentage / 100) * NotificationFormatter.PROGRESS_WIDTH)
        empty = NotificationFormatter.PROGRESS_WIDTH - filled
        progress_bar = NotificationFormatter.PROGRESS_FILL * filled + NotificationFormatter.PROGRESS_EMPTY * empty
        
        eta_text = ""
        if eta_seconds is not None:
            if eta_seconds < 60:
                eta_text = f"⏱️ <b>ETA:</b> {eta_seconds}s\n"
            elif eta_seconds < 3600:
                eta_text = f"⏱️ <b>ETA:</b> {eta_seconds // 60}m {eta_seconds % 60}s\n"
            else:
                hours = eta_seconds // 3600
                mins = (eta_seconds % 3600) // 60
                eta_text = f"⏱️ <b>ETA:</b> {hours}h {mins}m\n"
        
        extra_text = f"\n<i>{NotificationFormatter._escape_html(extra_info)}</i>" if extra_info else ""
        
        message = f"""{emoji} <b>Progress Update</b>

📋 <b>Task:</b> {NotificationFormatter._escape_html(description)}

<code>[{progress_bar}]</code> {percentage}%

📊 <b>Completed:</b> {current}/{total}
{eta_text}{extra_text}"""
        
        return message

    @staticmethod
    def format_notification(
        message: str, 
        notif_type: NotificationType = NotificationType.INFO,
        title: Optional[str] = None
    ) -> str:
        """Format a general notification."""
        display_title = title or notif_type.title
        return f"{notif_type.emoji} <b>{NotificationFormatter._escape_html(display_title)}</b>\n\n{message}"

    @staticmethod
    def format_error_alert(
        error: str, 
        context: Optional[str] = None,
        suggestion: Optional[str] = None
    ) -> str:
        """Format an error alert with optional context and suggestion."""
        emoji = NotificationType.ERROR.emoji
        
        context_text = f"\n<b>Context:</b> {NotificationFormatter._escape_html(context)}" if context else ""
        suggestion_text = f"\n\n💡 <b>Suggestion:</b> {NotificationFormatter._escape_html(suggestion)}" if suggestion else ""
        
        # Truncate long errors
        error_display = error[:800] + "..." if len(error) > 800 else error
        
        message = f"""{emoji} <b>Error Alert</b>

<pre>{NotificationFormatter._escape_html(error_display)}</pre>{context_text}{suggestion_text}"""
        
        return message

    @staticmethod
    def format_status_update(
        working_dir: str,
        active_tasks: List[TaskInfo],
        recent_completed: List[TaskInfo],
        system_status: str = "🟢 Online"
    ) -> str:
        """Format a system status update."""
        emoji = NotificationType.SYSTEM.emoji
        
        active_text = ""
        if active_tasks:
            tasks_list = "\n".join([
                f"• <code>#{t.id}</code> {NotificationFormatter._escape_html(t.description[:40])}..."
                for t in active_tasks[:5]
            ])
            active_text = f"\n<b>📝 Active Tasks ({len(active_tasks)}):</b>\n{tasks_list}\n"
        else:
            active_text = "\n<b>📝 Active Tasks:</b> None\n"
        
        completed_text = ""
        if recent_completed:
            completed_list = "\n".join([
                f"• ✅ <code>#{t.id}</code> {NotificationFormatter._escape_html(t.description[:35])}..."
                for t in recent_completed[:3]
            ])
            completed_text = f"<b>✅ Recent Completed:</b>\n{completed_list}\n"
        
        message = f"""{emoji} <b>System Status</b>

📂 <b>Working Directory:</b>
<code>{NotificationFormatter._escape_html(working_dir)}</code>

🔰 <b>System:</b> {system_status}{active_text}
{completed_text}
Use /tasks for full task list."""
        
        return message

    @staticmethod
    def format_file_notification(
        file_name: str,
        file_size: Optional[str] = None,
        action: str = "received",
        caption: Optional[str] = None
    ) -> str:
        """Format a file attachment notification."""
        emoji = NotificationType.FILE.emoji
        
        size_text = f" ({file_size})" if file_size else ""
        caption_text = f"\n\n<i>{NotificationFormatter._escape_html(caption)}</i>" if caption else ""
        
        message = f"""{emoji} <b>File {action.title()}</b>

📄 <b>Name:</b> <code>{NotificationFormatter._escape_html(file_name)}</code>{size_text}{caption_text}"""
        
        return message

    @staticmethod
    def create_inline_keyboard(
        options: List[QuestionOption],
        layout: str = "horizontal"  # "horizontal", "vertical", "grid"
    ) -> List[List[Dict[str, str]]]:
        """
        Create inline keyboard markup for Telegram.
        
        Returns a list of rows, where each row is a list of button dictionaries.
        """
        keyboard = []
        
        if layout == "horizontal":
            # All buttons in one row
            row = []
            for opt in options:
                text = f"{opt.emoji} {opt.text}" if opt.emoji else opt.text
                row.append({"text": text, "callback_data": opt.callback_data})
            keyboard.append(row)
            
        elif layout == "vertical":
            # Each button on its own row
            for opt in options:
                text = f"{opt.emoji} {opt.text}" if opt.emoji else opt.text
                keyboard.append([{"text": text, "callback_data": opt.callback_data}])
                
        elif layout == "grid":
            # 2 buttons per row
            for i in range(0, len(options), 2):
                row = []
                for opt in options[i:i+2]:
                    text = f"{opt.emoji} {opt.text}" if opt.emoji else opt.text
                    row.append({"text": text, "callback_data": opt.callback_data})
                keyboard.append(row)
        
        return keyboard

    @staticmethod
    def create_yes_no_keyboard(
        yes_callback: str = "answer_yes",
        no_callback: str = "answer_no",
        yes_text: str = "Yes",
        no_text: str = "No",
        more_callback: Optional[str] = None,
        more_text: str = "More options..."
    ) -> List[List[Dict[str, str]]]:
        """Create a standard yes/no inline keyboard with optional 'more' button."""
        options = [
            QuestionOption(yes_text, yes_callback, "✅"),
            QuestionOption(no_text, no_callback, "❌"),
        ]
        
        if more_callback:
            options.append(QuestionOption(more_text, more_callback, "📋"))
        
        return NotificationFormatter.create_inline_keyboard(options, layout="horizontal")

    @staticmethod
    def create_progress_keyboard(
        task_id: str,
        show_cancel: bool = True,
        show_details: bool = True
    ) -> List[List[Dict[str, str]]]:
        """Create keyboard for progress updates."""
        keyboard = []
        
        if show_details:
            keyboard.append([{
                "text": "📊 View Details",
                "callback_data": f"task_details:{task_id}"
            }])
        
        if show_cancel:
            keyboard.append([{
                "text": "⏹️ Cancel Task",
                "callback_data": f"task_cancel:{task_id}"
            }])
        
        return keyboard

    @staticmethod
    def create_reply_keyboard(
        buttons: List[str],
        resize: bool = True,
        one_time: bool = False
    ) -> Dict[str, Any]:
        """Create a reply keyboard markup."""
        keyboard = [[btn] for btn in buttons]
        return {
            "keyboard": keyboard,
            "resize_keyboard": resize,
            "one_time_keyboard": one_time
        }

    @staticmethod
    def create_quick_commands_keyboard() -> Dict[str, Any]:
        """Create a reply keyboard with common commands."""
        return NotificationFormatter.create_reply_keyboard([
            "📋 /status",
            "➕ /task",
            "❓ /ask",
            "❌ /cancel"
        ])

    @staticmethod
    def format_code_block(code: str, language: str = "") -> str:
        """Format code for Telegram markdown."""
        # Escape backticks and backslashes
        escaped = code.replace("\\", "\\\\").replace("`", "\\`")
        return f"```{language}\n{escaped}\n```"

    @staticmethod
    def format_inline_code(text: str) -> str:
        """Format inline code."""
        escaped = text.replace("\\", "\\\\").replace("`", "\\`")
        return f"`{escaped}`"

    @staticmethod
    def truncate_message(message: str, max_length: int = 4096, suffix: str = "...") -> str:
        """Truncate message to fit Telegram limits."""
        if len(message) <= max_length:
            return message
        
        # Account for suffix
        truncate_at = max_length - len(suffix)
        return message[:truncate_at] + suffix

    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape HTML special characters."""
        if not text:
            return ""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))

    @staticmethod
    def _format_time(dt: Optional[datetime]) -> str:
        """Format datetime for display."""
        if not dt:
            return "Unknown"
        return dt.strftime("%Y-%m-%d %H:%M:%S")


# Convenience functions for quick formatting
def info(message: str, title: Optional[str] = None) -> str:
    """Quick info notification."""
    return NotificationFormatter.format_notification(message, NotificationType.INFO, title)


def success(message: str, title: Optional[str] = None) -> str:
    """Quick success notification."""
    return NotificationFormatter.format_notification(message, NotificationType.SUCCESS, title)


def warning(message: str, title: Optional[str] = None) -> str:
    """Quick warning notification."""
    return NotificationFormatter.format_notification(message, NotificationType.WARNING, title)


def error(message: str, title: Optional[str] = None) -> str:
    """Quick error notification."""
    return NotificationFormatter.format_notification(message, NotificationType.ERROR, title)


def task_started(task_id: str, description: str) -> str:
    """Quick task started notification."""
    task = TaskInfo(id=task_id, description=description)
    return NotificationFormatter.format_task_started(task)


def task_completed(
    task_id: str, 
    description: str, 
    duration_minutes: Optional[float] = None,
    files_created: Optional[List[str]] = None,
    result_summary: Optional[str] = None
) -> str:
    """Quick task completed notification."""
    task = TaskInfo(
        id=task_id,
        description=description,
        duration_minutes=duration_minutes,
        files_created=files_created or [],
        result_summary=result_summary
    )
    return NotificationFormatter.format_task_completed(task)


def task_failed(task_id: str, description: str, error_message: str) -> str:
    """Quick task failed notification."""
    task = TaskInfo(id=task_id, description=description, error_message=error_message)
    return NotificationFormatter.format_task_failed(task)


def progress(current: int, total: int, description: str, **kwargs) -> str:
    """Quick progress notification."""
    return NotificationFormatter.format_progress(current, total, description, **kwargs)


def question(text: str, options: Optional[List[QuestionOption]] = None, **kwargs) -> str:
    """Quick question notification."""
    return NotificationFormatter.format_question(text, options, **kwargs)


def yes_no_keyboard(yes_callback: str = "answer_yes", no_callback: str = "answer_no", **kwargs):
    """Quick yes/no keyboard."""
    return NotificationFormatter.create_yes_no_keyboard(yes_callback, no_callback, **kwargs)
