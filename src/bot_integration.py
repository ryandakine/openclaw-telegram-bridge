"""
Bot Integration Example for OpenClaw Telegram Bridge

Shows how the notification system integrates with the Telegram bot.
This can be extended into the full bot.py implementation.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import telegram libraries
try:
    from telegram import Update
    from telegram.ext import (
        Application,
        CommandHandler,
        CallbackQueryHandler,
        MessageHandler,
        filters,
        ContextTypes,
    )
    from telegram.constants import ParseMode
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger.warning("python-telegram-bot not installed. Running in demo mode.")

# Import our notification system
from notifications import (
    NotificationManager,
    NotificationType,
    TaskInfo,
    QuestionOption,
)


class OpenClawBot:
    """
    Telegram Bot for OpenClaw Bridge with Notification System.
    
    Features:
    - Task submission and tracking
    - Question/answer flow with inline keyboards
    - Progress updates for long-running tasks
    - Error alerts with retry options
    - File attachment support
    """
    
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.allowed_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.notification_manager: Optional[NotificationManager] = None
        self.application: Optional[Application] = None
        
        # Track active tasks (in production, use proper storage)
        self.active_tasks: dict = {}
        
    async def initialize(self):
        """Initialize the bot and notification manager."""
        if not TELEGRAM_AVAILABLE:
            logger.error("Telegram library not available")
            return False
            
        if not self.token:
            logger.error("TELEGRAM_BOT_TOKEN not set")
            return False
            
        self.application = Application.builder().token(self.token).build()
        
        # Initialize notification manager
        self.notification_manager = NotificationManager(
            bot=self.application.bot,
            chat_id=self.allowed_chat_id
        )
        
        # Register handlers
        self._register_handlers()
        
        logger.info("Bot initialized successfully")
        return True
    
    def _register_handlers(self):
        """Register command and message handlers."""
        app = self.application
        
        # Command handlers
        app.add_handler(CommandHandler("start", self._cmd_start))
        app.add_handler(CommandHandler("help", self._cmd_help))
        app.add_handler(CommandHandler("task", self._cmd_task))
        app.add_handler(CommandHandler("status", self._cmd_status))
        app.add_handler(CommandHandler("ask", self._cmd_ask))
        app.add_handler(CommandHandler("cancel", self._cmd_cancel))
        
        # Callback query handler for inline keyboards
        app.add_handler(CallbackQueryHandler(self._handle_callback))
        
        # Message handler for replies
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        
        # Error handler
        app.add_error_handler(self._handle_error)
    
    async def _check_auth(self, update: Update) -> bool:
        """Check if user is authorized."""
        user_id = str(update.effective_chat.id)
        if user_id != self.allowed_chat_id:
            await update.message.reply_text(
                "🚫 <b>Access Denied</b>\n\nYou are not authorized to use this bot.",
                parse_mode=ParseMode.HTML
            )
            logger.warning(f"Unauthorized access attempt from {user_id}")
            return False
        return True
    
    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        if not await self._check_auth(update):
            return
            
        welcome_message = """🚀 <b>Welcome to OpenClaw Telegram Bridge!</b>

I'm your remote interface to Kimi Code CLI. Here's what you can do:

<b>📋 Commands:</b>
• /task &lt;description&gt; - Submit a new task
• /ask &lt;question&gt; - Ask a question
• /status - Check system status
• /help - Show this help message

<b>💡 Tips:</b>
• Reply to my messages to answer questions
• I'll notify you when tasks complete
• Use inline buttons for quick responses

Ready to work! What would you like me to do?"""

        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.HTML
        )
    
    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        if not await self._check_auth(update):
            return
            
        help_message = """❓ <b>OpenClaw Bot Help</b>

<b>Task Management:</b>
• /task &lt;description&gt; - Submit a new task to Kimi
• /status - View current tasks and system status
• /cancel - Cancel the current operation

<b>Communication:</b>
• /ask &lt;question&gt; - Ask Kimi a question
• Reply to any message - Respond to Kimi's questions

<b>Special Replies:</b>
• "done" - Acknowledge completion
• "stop" - Cancel current task
• Send file - Attach file to current context

<b>Need more help?</b>
Contact the system administrator."""

        await update.message.reply_text(
            help_message,
            parse_mode=ParseMode.HTML
        )
    
    async def _cmd_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /task command."""
        if not await self._check_auth(update):
            return
            
        # Get task description
        task_description = ' '.join(context.args)
        if not task_description:
            await update.message.reply_text(
                "⚠️ <b>Please provide a task description</b>\n\n"
                "Example: <code>/task Create a backup script</code>",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Create task info
        task_id = f"TASK-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        task = TaskInfo(
            id=task_id,
            description=task_description,
            status="in_progress",
            created_at=datetime.now()
        )
        
        # Store task
        self.active_tasks[task_id] = task
        
        # Send notification
        await self.notification_manager.send_task_started(task)
        
        # TODO: Notify Kimi about the new task
        logger.info(f"New task submitted: {task_id}")
    
    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        if not await self._check_auth(update):
            return
        
        # Get current working directory
        working_dir = os.getcwd()
        
        # Get active and recent tasks
        active_tasks = [
            task for task in self.active_tasks.values()
            if task.status in ["in_progress", "pending"]
        ]
        
        recent_completed = [
            task for task in self.active_tasks.values()
            if task.status == "completed"
        ][-3:]  # Last 3 completed
        
        # Send status update
        await self.notification_manager.send_status_update(
            working_dir=working_dir,
            active_tasks=active_tasks,
            recent_completed=recent_completed
        )
    
    async def _cmd_ask(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ask command."""
        if not await self._check_auth(update):
            return
            
        question_text = ' '.join(context.args)
        if not question_text:
            await update.message.reply_text(
                "⚠️ <b>Please provide a question</b>\n\n"
                "Example: <code>/ask What is the project structure?</code>",
                parse_mode=ParseMode.HTML
            )
            return
        
        # TODO: Forward question to Kimi
        await update.message.reply_text(
            f"❓ <b>Question sent to Kimi:</b>\n\n{question_text}\n\n"
            "I'll get back to you shortly!",
            parse_mode=ParseMode.HTML
        )
    
    async def _cmd_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cancel command."""
        if not await self._check_auth(update):
            return
            
        await update.message.reply_text(
            "⏹️ <b>Operation cancelled</b>\n\nAny pending tasks have been stopped.",
            parse_mode=ParseMode.HTML
        )
    
    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard callbacks."""
        if not await self._check_auth(update):
            return
            
        # Pass to notification manager
        handled = await self.notification_manager.handle_callback_query(
            update, context
        )
        
        if not handled:
            await update.callback_query.answer("Unknown action")
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages (replies)."""
        if not await self._check_auth(update):
            return
            
        text = update.message.text.lower()
        
        # Handle special replies
        if text == "done":
            await update.message.reply_text("✅ Acknowledged!")
        elif text == "stop":
            await update.message.reply_text("⏹️ Stopping current task...")
        else:
            # TODO: Forward to Kimi as a reply
            await update.message.reply_text(
                f"✉️ <b>Message received:</b>\n\n"
                f"<i>Forwarding to Kimi...</i>",
                parse_mode=ParseMode.HTML
            )
    
    async def _handle_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors."""
        logger.error(f"Error occurred: {context.error}")
        
        if update and update.effective_chat:
            await self.notification_manager.send_error_alert(
                error=str(context.error),
                context="Bot error handler",
                suggestion="Please try again or contact support"
            )
    
    async def simulate_task_progress(self, task_id: str):
        """
        Simulate a task with progress updates (for demonstration).
        
        In production, this would be triggered by Kimi's actual task progress.
        """
        task = self.active_tasks.get(task_id)
        if not task:
            return
        
        steps = [
            (25, "Analyzing requirements..."),
            (50, "Writing code..."),
            (75, "Testing solution..."),
            (100, "Finalizing...")
        ]
        
        for progress_pct, extra_info in steps:
            await self.notification_manager.send_progress(
                task_id=task_id,
                current=progress_pct,
                total=100,
                description=task.description,
                eta_seconds=(100 - progress_pct) * 3,
                extra_info=extra_info
            )
            await asyncio.sleep(2)  # Simulate work
        
        # Mark as complete
        task.status = "completed"
        task.duration_minutes = 2.5
        task.files_created = ["result.py"]
        task.result_summary = "Task completed successfully!"
        
        await self.notification_manager.send_task_completed(task)
    
    async def run(self):
        """Run the bot."""
        if not await self.initialize():
            logger.error("Failed to initialize bot")
            return
            
        logger.info("Starting bot...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        # Keep running
        while True:
            await asyncio.sleep(1)
    
    def run_sync(self):
        """Run the bot synchronously."""
        asyncio.run(self.run())


def main():
    """Main entry point."""
    bot = OpenClawBot()
    
    if not TELEGRAM_AVAILABLE:
        print("\n" + "=" * 60)
        print("  TELEGRAM BOT NOT AVAILABLE")
        print("=" * 60)
        print("\nTo use the Telegram bot, install the required packages:")
        print("  pip install python-telegram-bot python-dotenv")
        print("\nThen set your environment variables in .env:")
        print("  TELEGRAM_BOT_TOKEN=your_token_here")
        print("  TELEGRAM_CHAT_ID=your_chat_id_here")
        print("\n" + "=" * 60)
        return
    
    bot.run_sync()


if __name__ == "__main__":
    main()
