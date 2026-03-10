"""
Notification Manager for OpenClaw Telegram Bridge

Manages sending notifications, handling inline keyboard callbacks,
and tracking message state for updates.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable, Coroutine, Union
from dataclasses import dataclass, field
from enum import Enum

try:
    from telegram import (
        Update, 
        InlineKeyboardButton, 
        InlineKeyboardMarkup,
        ReplyKeyboardMarkup,
        ReplyKeyboardRemove,
        InputFile
    )
    from telegram.constants import ParseMode
    from telegram.ext import ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    # Mock classes for type hints
    class Update:
        pass
    class ContextTypes:
        DEFAULT_TYPE = None
    class ParseMode:
        HTML = "HTML"

from .formatter import (
    NotificationFormatter, 
    NotificationType, 
    TaskInfo, 
    QuestionOption,
    FileAttachment
)


logger = logging.getLogger(__name__)


@dataclass
class MessageState:
    """Track state of sent messages for updates."""
    message_id: int
    chat_id: int
    message_type: str
    content_hash: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PendingQuestion:
    """Track pending questions awaiting user response."""
    question_id: str
    question_text: str
    callback_handlers: Dict[str, Callable] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    timeout_seconds: int = 300  # 5 minutes default
    answered: bool = False
    answer: Optional[str] = None


class NotificationManager:
    """
    Manager for sending notifications and handling user interactions.
    
    Features:
    - Send different notification types
    - Handle inline keyboard callbacks
    - Update existing messages
    - Track pending questions
    - Support file attachments
    """
    
    def __init__(self, bot=None, chat_id: Optional[str] = None):
        self.bot = bot
        self.chat_id = chat_id
        self.message_states: Dict[str, MessageState] = {}
        self.pending_questions: Dict[str, PendingQuestion] = {}
        self.callback_handlers: Dict[str, Callable] = {}
        self._progress_messages: Dict[str, int] = {}  # task_id -> message_id
        
    def register_callback_handler(self, callback_prefix: str, handler: Callable):
        """Register a handler for callback queries with given prefix."""
        self.callback_handlers[callback_prefix] = handler
        logger.debug(f"Registered callback handler for prefix: {callback_prefix}")
    
    async def send_notification(
        self,
        message: str,
        notif_type: NotificationType = NotificationType.INFO,
        title: Optional[str] = None,
        chat_id: Optional[str] = None,
        reply_markup: Optional[Any] = None,
        parse_mode: str = "HTML"
    ) -> Optional[MessageState]:
        """Send a notification message."""
        if not self.bot or not TELEGRAM_AVAILABLE:
            logger.warning("Telegram bot not available, logging notification instead")
            logger.info(f"[{notif_type.name}] {title or notif_type.title}: {message}")
            return None
        
        target_chat = chat_id or self.chat_id
        if not target_chat:
            raise ValueError("No chat_id provided")
        
        formatted_message = NotificationFormatter.format_notification(
            message, notif_type, title
        )
        
        try:
            sent_message = await self.bot.send_message(
                chat_id=target_chat,
                text=formatted_message,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
            
            state = MessageState(
                message_id=sent_message.message_id,
                chat_id=sent_message.chat.id,
                message_type="notification",
                content_hash=hash(formatted_message) % 10000
            )
            
            self.message_states[str(sent_message.message_id)] = state
            logger.debug(f"Sent notification: {notif_type.name}")
            return state
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            raise
    
    async def send_task_started(
        self,
        task: TaskInfo,
        chat_id: Optional[str] = None
    ) -> Optional[MessageState]:
        """Send task started notification."""
        message = NotificationFormatter.format_task_started(task)
        
        # Add cancel button
        keyboard = [[
            InlineKeyboardButton("⏹️ Cancel", callback_data=f"task_cancel:{task.id}")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return await self._send_message(
            message=message,
            chat_id=chat_id,
            reply_markup=reply_markup,
            message_type="task_started",
            metadata={"task_id": task.id}
        )
    
    async def send_task_completed(
        self,
        task: TaskInfo,
        chat_id: Optional[str] = None,
        include_actions: bool = True
    ) -> Optional[MessageState]:
        """Send task completed notification."""
        message = NotificationFormatter.format_task_completed(task)
        
        reply_markup = None
        if include_actions:
            keyboard = [
                [InlineKeyboardButton("📖 View Code", callback_data=f"task_code:{task.id}")],
                [InlineKeyboardButton("🔄 Run Again", callback_data=f"task_rerun:{task.id}")],
                [InlineKeyboardButton("✅ Done", callback_data=f"task_done:{task.id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Clean up any progress message for this task
        if task.id in self._progress_messages:
            try:
                await self.bot.delete_message(
                    chat_id=chat_id or self.chat_id,
                    message_id=self._progress_messages[task.id]
                )
            except Exception:
                pass
            del self._progress_messages[task.id]
        
        return await self._send_message(
            message=message,
            chat_id=chat_id,
            reply_markup=reply_markup,
            message_type="task_completed",
            metadata={"task_id": task.id}
        )
    
    async def send_task_failed(
        self,
        task: TaskInfo,
        chat_id: Optional[str] = None,
        include_retry: bool = True
    ) -> Optional[MessageState]:
        """Send task failed notification."""
        message = NotificationFormatter.format_task_failed(task)
        
        reply_markup = None
        if include_retry:
            keyboard = [
                [InlineKeyboardButton("🔄 Retry", callback_data=f"task_retry:{task.id}")],
                [InlineKeyboardButton("📋 View Logs", callback_data=f"task_logs:{task.id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Clean up progress message
        if task.id in self._progress_messages:
            try:
                await self.bot.delete_message(
                    chat_id=chat_id or self.chat_id,
                    message_id=self._progress_messages[task.id]
                )
            except Exception:
                pass
            del self._progress_messages[task.id]
        
        return await self._send_message(
            message=message,
            chat_id=chat_id,
            reply_markup=reply_markup,
            message_type="task_failed",
            metadata={"task_id": task.id}
        )
    
    async def send_question(
        self,
        question_id: str,
        question_text: str,
        options: Optional[List[QuestionOption]] = None,
        context: Optional[str] = None,
        chat_id: Optional[str] = None,
        timeout_seconds: int = 300,
        on_answer: Optional[Callable[[str, str], Coroutine]] = None
    ) -> Optional[MessageState]:
        """
        Send a question with inline keyboard options.
        
        Args:
            question_id: Unique ID for tracking this question
            question_text: The question to ask
            options: List of QuestionOption for inline keyboard
            context: Optional context information
            chat_id: Target chat ID
            timeout_seconds: How long to wait for answer
            on_answer: Callback when answer is received
        """
        # Default yes/no options if none provided
        if options is None:
            options = [
                QuestionOption("Yes", f"q:{question_id}:yes", "✅"),
                QuestionOption("No", f"q:{question_id}:no", "❌")
            ]
        
        message = NotificationFormatter.format_question(
            question_text, options, context
        )
        
        # Create inline keyboard
        keyboard = []
        for opt in options:
            text = f"{opt.emoji} {opt.text}" if opt.emoji else opt.text
            keyboard.append([InlineKeyboardButton(text, callback_data=opt.callback_data)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Track pending question
        pending = PendingQuestion(
            question_id=question_id,
            question_text=question_text,
            timeout_seconds=timeout_seconds
        )
        
        if on_answer:
            # Register callback handlers for each option
            for opt in options:
                async def handler(query_data, ans=opt.callback_data.split(":")[-1]):
                    await on_answer(question_id, ans)
                self.callback_handlers[opt.callback_data] = handler
        
        self.pending_questions[question_id] = pending
        
        # Set up timeout
        asyncio.create_task(self._question_timeout(question_id, timeout_seconds))
        
        return await self._send_message(
            message=message,
            chat_id=chat_id,
            reply_markup=reply_markup,
            message_type="question",
            metadata={"question_id": question_id}
        )
    
    async def _question_timeout(self, question_id: str, timeout_seconds: int):
        """Handle question timeout."""
        await asyncio.sleep(timeout_seconds)
        
        if question_id in self.pending_questions:
            question = self.pending_questions[question_id]
            if not question.answered:
                logger.warning(f"Question {question_id} timed out")
                # Could send a timeout notification here
                del self.pending_questions[question_id]
    
    async def send_progress(
        self,
        task_id: str,
        current: int,
        total: int,
        description: str,
        eta_seconds: Optional[int] = None,
        extra_info: Optional[str] = None,
        chat_id: Optional[str] = None,
        update_existing: bool = True
    ) -> Optional[MessageState]:
        """
        Send or update a progress message.
        
        Args:
            task_id: Unique task identifier
            current: Current progress value
            total: Total progress value
            description: Task description
            eta_seconds: Estimated time remaining
            extra_info: Additional information to display
            chat_id: Target chat ID
            update_existing: Whether to update existing progress message
        """
        message = NotificationFormatter.format_progress(
            current, total, description, eta_seconds, extra_info
        )
        
        # Create keyboard
        keyboard = NotificationFormatter.create_progress_keyboard(task_id)
        telegram_keyboard = []
        for row in keyboard:
            telegram_row = []
            for btn in row:
                telegram_row.append(InlineKeyboardButton(btn["text"], callback_data=btn["callback_data"]))
            telegram_keyboard.append(telegram_row)
        reply_markup = InlineKeyboardMarkup(telegram_keyboard) if telegram_keyboard else None
        
        # Check if we should update existing message
        if update_existing and task_id in self._progress_messages:
            try:
                await self.bot.edit_message_text(
                    chat_id=chat_id or self.chat_id,
                    message_id=self._progress_messages[task_id],
                    text=message,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )
                return None  # Message updated, no new state
            except Exception as e:
                logger.warning(f"Could not update progress message: {e}")
        
        # Send new message
        state = await self._send_message(
            message=message,
            chat_id=chat_id,
            reply_markup=reply_markup,
            message_type="progress",
            metadata={"task_id": task_id}
        )
        
        if state:
            self._progress_messages[task_id] = state.message_id
        
        return state
    
    async def send_error_alert(
        self,
        error: str,
        context: Optional[str] = None,
        suggestion: Optional[str] = None,
        chat_id: Optional[str] = None,
        include_help: bool = True
    ) -> Optional[MessageState]:
        """Send an error alert notification."""
        message = NotificationFormatter.format_error_alert(error, context, suggestion)
        
        reply_markup = None
        if include_help:
            keyboard = [
                [InlineKeyboardButton("❓ Get Help", callback_data="error_help")],
                [InlineKeyboardButton("📝 Report Issue", callback_data="error_report")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
        
        return await self._send_message(
            message=message,
            chat_id=chat_id,
            reply_markup=reply_markup,
            message_type="error_alert",
            metadata={"error_preview": error[:100]}
        )
    
    async def send_file(
        self,
        file_path: str,
        caption: Optional[str] = None,
        chat_id: Optional[str] = None,
        filename: Optional[str] = None
    ) -> Optional[MessageState]:
        """Send a file attachment."""
        if not self.bot or not TELEGRAM_AVAILABLE:
            logger.warning("Cannot send file: Telegram bot not available")
            return None
        
        target_chat = chat_id or self.chat_id
        if not target_chat:
            raise ValueError("No chat_id provided")
        
        try:
            with open(file_path, 'rb') as f:
                file_data = InputFile(f, filename=filename)
                
                # Determine file type and send accordingly
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                    sent = await self.bot.send_photo(
                        chat_id=target_chat,
                        photo=file_data,
                        caption=caption,
                        parse_mode=ParseMode.HTML
                    )
                elif file_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                    sent = await self.bot.send_video(
                        chat_id=target_chat,
                        video=file_data,
                        caption=caption,
                        parse_mode=ParseMode.HTML
                    )
                else:
                    sent = await self.bot.send_document(
                        chat_id=target_chat,
                        document=file_data,
                        caption=caption,
                        parse_mode=ParseMode.HTML
                    )
                
                state = MessageState(
                    message_id=sent.message_id,
                    chat_id=sent.chat.id,
                    message_type="file",
                    content_hash=hash(file_path) % 10000,
                    metadata={"file_path": file_path}
                )
                
                logger.debug(f"Sent file: {file_path}")
                return state
                
        except Exception as e:
            logger.error(f"Failed to send file: {e}")
            # Send error notification instead
            await self.send_error_alert(
                error=f"Failed to send file: {e}",
                context=f"File: {file_path}",
                suggestion="Check if file exists and is accessible"
            )
            raise
    
    async def send_status_update(
        self,
        working_dir: str,
        active_tasks: List[TaskInfo],
        recent_completed: List[TaskInfo],
        system_status: str = "🟢 Online",
        chat_id: Optional[str] = None
    ) -> Optional[MessageState]:
        """Send a system status update."""
        message = NotificationFormatter.format_status_update(
            working_dir, active_tasks, recent_completed, system_status
        )
        
        # Add action buttons
        keyboard = [
            [InlineKeyboardButton("📋 View All Tasks", callback_data="status_tasks")],
            [InlineKeyboardButton("🔄 Refresh", callback_data="status_refresh")],
            [InlineKeyboardButton("⏸️ Pause Notifications", callback_data="status_pause")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return await self._send_message(
            message=message,
            chat_id=chat_id,
            reply_markup=reply_markup,
            message_type="status_update",
            metadata={"working_dir": working_dir}
        )
    
    async def update_message(
        self,
        message_id: int,
        new_text: str,
        chat_id: Optional[str] = None,
        reply_markup: Optional[Any] = None
    ) -> bool:
        """Update an existing message."""
        if not self.bot or not TELEGRAM_AVAILABLE:
            return False
        
        target_chat = chat_id or self.chat_id
        if not target_chat:
            return False
        
        try:
            await self.bot.edit_message_text(
                chat_id=target_chat,
                message_id=message_id,
                text=new_text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
            
            # Update state
            state_key = str(message_id)
            if state_key in self.message_states:
                self.message_states[state_key].updated_at = datetime.now()
                self.message_states[state_key].content_hash = hash(new_text) % 10000
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update message {message_id}: {e}")
            return False
    
    async def delete_message(self, message_id: int, chat_id: Optional[str] = None) -> bool:
        """Delete a message."""
        if not self.bot or not TELEGRAM_AVAILABLE:
            return False
        
        target_chat = chat_id or self.chat_id
        if not target_chat:
            return False
        
        try:
            await self.bot.delete_message(chat_id=target_chat, message_id=message_id)
            
            # Remove from state
            state_key = str(message_id)
            if state_key in self.message_states:
                del self.message_states[state_key]
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete message {message_id}: {e}")
            return False
    
    async def handle_callback_query(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        """
        Handle inline keyboard callback queries.
        
        Returns True if the callback was handled.
        """
        if not TELEGRAM_AVAILABLE:
            return False
        
        query = update.callback_query
        await query.answer()  # Acknowledge the callback
        
        data = query.data
        logger.debug(f"Received callback query: {data}")
        
        # Check for exact match handlers
        if data in self.callback_handlers:
            handler = self.callback_handlers[data]
            if asyncio.iscoroutinefunction(handler):
                await handler(data)
            else:
                handler(data)
            return True
        
        # Check for prefix handlers
        for prefix, handler in self.callback_handlers.items():
            if data.startswith(prefix):
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
                return True
        
        # Handle question answers
        if data.startswith("q:"):
            parts = data.split(":")
            if len(parts) >= 3:
                question_id = parts[1]
                answer = parts[2]
                
                if question_id in self.pending_questions:
                    self.pending_questions[question_id].answered = True
                    self.pending_questions[question_id].answer = answer
                    
                    # Update the message to show the answer
                    await query.edit_message_text(
                        text=f"{query.message.text}\n\n✅ <b>You answered:</b> {answer.title()}",
                        parse_mode=ParseMode.HTML
                    )
                    
                    logger.debug(f"Question {question_id} answered: {answer}")
                    return True
        
        # Handle task actions
        if data.startswith("task_"):
            await self._handle_task_callback(query, data)
            return True
        
        logger.warning(f"Unhandled callback query: {data}")
        return False
    
    async def _handle_task_callback(self, query, data: str):
        """Handle task-related callbacks."""
        action, task_id = data.split(":") if ":" in data else (data, None)
        
        if action == "task_cancel":
            await query.edit_message_text(
                text=f"{query.message.text}\n\n⏹️ <b>Task cancelled by user</b>",
                parse_mode=ParseMode.HTML
            )
            # TODO: Notify task manager to cancel task
            
        elif action == "task_done":
            await query.edit_message_text(
                text=f"{query.message.text}\n\n✅ <b>Acknowledged</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=None
            )
            
        elif action == "task_retry":
            await query.edit_message_text(
                text=f"{query.message.text}\n\n🔄 <b>Retrying...</b>",
                parse_mode=ParseMode.HTML
            )
            # TODO: Notify task manager to retry task
            
        elif action == "task_details":
            # TODO: Fetch and display task details
            await query.answer("Task details feature coming soon!")
            
        else:
            await query.answer(f"Action: {action}")
    
    async def _send_message(
        self,
        message: str,
        chat_id: Optional[str] = None,
        reply_markup: Optional[Any] = None,
        message_type: str = "unknown",
        metadata: Optional[Dict] = None,
        parse_mode: str = "HTML"
    ) -> Optional[MessageState]:
        """Internal method to send a message and track its state."""
        if not self.bot or not TELEGRAM_AVAILABLE:
            logger.warning(f"Telegram not available. Message type: {message_type}")
            logger.info(f"Would send: {message[:200]}...")
            return None
        
        target_chat = chat_id or self.chat_id
        if not target_chat:
            raise ValueError("No chat_id provided")
        
        # Truncate if necessary (Telegram limit is 4096)
        if len(message) > 4096:
            message = message[:4093] + "..."
        
        try:
            sent_message = await self.bot.send_message(
                chat_id=target_chat,
                text=message,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
            
            state = MessageState(
                message_id=sent_message.message_id,
                chat_id=sent_message.chat.id,
                message_type=message_type,
                content_hash=hash(message) % 10000,
                metadata=metadata or {}
            )
            
            self.message_states[str(sent_message.message_id)] = state
            return state
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise
    
    def get_pending_answer(self, question_id: str) -> Optional[str]:
        """Get the answer for a pending question if it has been answered."""
        if question_id in self.pending_questions:
            question = self.pending_questions[question_id]
            if question.answered:
                return question.answer
        return None
    
    def is_question_answered(self, question_id: str) -> bool:
        """Check if a question has been answered."""
        if question_id in self.pending_questions:
            return self.pending_questions[question_id].answered
        return False
    
    def cancel_question(self, question_id: str) -> bool:
        """Cancel a pending question."""
        if question_id in self.pending_questions:
            del self.pending_questions[question_id]
            return True
        return False
    
    def clear_progress_message(self, task_id: str):
        """Clear tracked progress message for a task."""
        if task_id in self._progress_messages:
            del self._progress_messages[task_id]
