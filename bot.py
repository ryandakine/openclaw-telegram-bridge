#!/usr/bin/env python3
"""
OpenClaw Telegram Bridge - Main Bot Application

A bi-directional communication bridge between the user and Kimi Code CLI via Telegram.
"""
import logging
import sys
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    LOG_LEVEL,
    LOG_FORMAT,
    validate_config,
    is_authorized,
    BOT_NAME,
    BOT_VERSION
)
from queue_manager import QueueManager, MessageType, MessageStatus

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler("logs/bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize queue manager
queue_manager = QueueManager()


# ============== Authorization Decorator ==============

def authorized_only(handler):
    """Decorator to restrict commands to authorized users only."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_chat:
            return
        
        chat_id = update.effective_chat.id
        
        if not is_authorized(chat_id):
            logger.warning(f"Unauthorized access attempt from chat_id: {chat_id}")
            await update.message.reply_text(
                "🚫 Access denied. You are not authorized to use this bot."
            )
            return
        
        await handler(update, context)
    
    return wrapper


# ============== Command Handlers ==============

@authorized_only
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start command - Show welcome message.
    """
    welcome_message = f"""
🤖 Welcome to <b>{BOT_NAME}</b> v{BOT_VERSION}!

I'm your bridge to Kimi Code CLI. You can use me to:

📋 <b>/task</b> &lt;description&gt; - Submit a new task
❓ <b>/ask</b> &lt;question&gt; - Ask a question  
📊 <b>/status</b> - Check task queue status
❓ <b>/help</b> - Show this help message

Simply type any message to send it to Kimi.

<i>Connected and ready! 🚀</i>
"""
    await update.message.reply_html(welcome_message)
    logger.info(f"User {update.effective_chat.id} started the bot")


@authorized_only
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /help command - Show available commands.
    """
    help_message = f"""
<b>📚 Available Commands</b>

<b>Core Commands:</b>
/start - Initialize bot and show welcome
/help - Show this help message

<b>Task Management:</b>
/task &lt;description&gt; - Submit a new task
  Example: /task Create a Python backup script

/status - Check current queue status
  Shows pending, processing, and completed tasks

<b>Communication:</b>
/ask &lt;question&gt; - Ask Kimi a question
  Example: /ask What's the best way to backup my database?

<b>Direct Messages:</b>
Send any text message to communicate directly with Kimi.

<b>Quick Replies:</b>
Reply "done" to acknowledge completion
Reply "stop" to cancel current operation
"""
    await update.message.reply_html(help_message)
    logger.info(f"User {update.effective_chat.id} requested help")


@authorized_only
async def task_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /task command - Submit a new task.
    
    Usage: /task <description>
    """
    # Get task description from command arguments
    if not context.args:
        await update.message.reply_html(
            "❌ <b>Missing task description</b>\n\n"
            "Usage: <code>/task &lt;description&gt;</code>\n\n"
            "Example: <code>/task Create a Python script to backup files</code>"
        )
        return
    
    description = " ".join(context.args)
    
    # Save task to queue
    message = queue_manager.add_message(
        msg_type=MessageType.TASK,
        from_user="user",
        content=description,
        metadata={
            "telegram_message_id": update.message.message_id,
            "chat_id": update.effective_chat.id
        }
    )
    
    # Send confirmation
    confirmation = f"""
🚀 <b>Task Received!</b>

📋 <b>Description:</b> {description}
🆔 <b>Task ID:</b> #{message.id[:8]}
⏱️ <b>Status:</b> Queued

I'll notify you when processing begins and when it's complete.
"""
    await update.message.reply_html(confirmation)
    logger.info(f"Task created: {message.id} - {description[:50]}...")


@authorized_only
async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /ask command - Ask a question.
    
    Usage: /ask <question>
    """
    # Get question from command arguments
    if not context.args:
        await update.message.reply_html(
            "❌ <b>Missing question</b>\n\n"
            "Usage: <code>/ask &lt;question&gt;</code>\n\n"
            "Example: <code>/ask How do I optimize my database queries?</code>"
        )
        return
    
    question = " ".join(context.args)
    
    # Save question to queue
    message = queue_manager.add_message(
        msg_type=MessageType.QUESTION,
        from_user="user",
        content=question,
        metadata={
            "telegram_message_id": update.message.message_id,
            "chat_id": update.effective_chat.id
        }
    )
    
    # Send confirmation
    confirmation = f"""
❓ <b>Question Received!</b>

<b>Question:</b> {question}
🆔 <b>Message ID:</b> #{message.id[:8]}

I'll get back to you with an answer shortly.
"""
    await update.message.reply_html(confirmation)
    logger.info(f"Question created: {message.id} - {question[:50]}...")


@authorized_only
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /status command - Show current queue status.
    """
    status = queue_manager.get_queue_status()
    
    # Get pending messages for more detail
    pending = queue_manager.get_pending_messages()
    pending_tasks = [m for m in pending if m.type == MessageType.TASK.value]
    pending_questions = [m for m in pending if m.type == MessageType.QUESTION.value]
    
    status_message = f"""
📊 <b>System Status</b>

<b>Queue Summary:</b>
⏳ Pending: {status['pending']}
🔄 Processing: {status['processing']}
✅ Completed: {status['completed']}
❌ Failed: {status['failed']}
📊 Total: {status['total']}

<b>Pending Items:</b>
📝 Tasks: {len(pending_tasks)}
❓ Questions: {len(pending_questions)}

<i>Last updated: Just now</i>
"""
    await update.message.reply_html(status_message)
    logger.info(f"Status requested by user {update.effective_chat.id}")


@authorized_only
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle regular text messages from the user.
    These are treated as general communications.
    """
    if not update.message or not update.message.text:
        return
    
    # Skip if this is a command (shouldn't happen due to filters, but safety check)
    if update.message.text.startswith("/"):
        return
    
    text = update.message.text
    
    # Handle special reply patterns
    if text.lower().strip() == "done":
        await update.message.reply_html("✅ <b>Acknowledged!</b> Completion noted.")
        logger.info("User acknowledged completion")
        return
    
    if text.lower().strip() == "stop":
        await update.message.reply_html("🛑 <b>Stop signal received.</b> Cancelling current operation...")
        logger.info("User requested stop")
        return
    
    # Save as a general message/response
    message = queue_manager.add_message(
        msg_type=MessageType.RESPONSE,
        from_user="user",
        content=text,
        metadata={
            "telegram_message_id": update.message.message_id,
            "chat_id": update.effective_chat.id,
            "is_reply": update.message.reply_to_message is not None
        }
    )
    
    # Send acknowledgment
    await update.message.reply_html(
        f"✅ <b>Message received!</b>\n\n"
        f"Your message has been saved (ID: #{message.id[:8]}).\n"
        f"Kimi will process it shortly."
    )
    logger.info(f"Message received: {message.id}")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle errors that occur in the bot.
    """
    logger.error(f"Update {update} caused error: {context.error}", exc_info=True)
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ An error occurred while processing your request. "
            "Please try again or contact support."
        )


# ============== Bot Application ==============

def create_application() -> Application:
    """
    Create and configure the Telegram bot application.
    """
    # Validate configuration
    errors = validate_config()
    if errors:
        logger.error("Configuration errors:")
        for error in errors:
            logger.error(f"  - {error}")
        raise RuntimeError("Invalid configuration. Please check your .env file.")
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("task", task_command))
    application.add_handler(CommandHandler("ask", ask_command))
    application.add_handler(CommandHandler("status", status_command))
    
    # Add message handler for text messages
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
    )
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    return application


async def post_init(application: Application) -> None:
    """
    Post-initialization hook - runs after bot is initialized.
    """
    logger.info(f"{BOT_NAME} v{BOT_VERSION} started successfully!")
    logger.info(f"Authorized chat ID: {TELEGRAM_CHAT_ID}")
    
    # Send startup notification to authorized user
    try:
        chat_id = int(TELEGRAM_CHAT_ID)
        await application.bot.send_message(
            chat_id=chat_id,
            text=f"🤖 <b>{BOT_NAME}</b> v{BOT_VERSION} is now online!\n\n"
                 f"Send /help to see available commands.",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.warning(f"Could not send startup notification: {e}")


def main() -> None:
    """
    Main entry point for the bot.
    """
    logger.info(f"Starting {BOT_NAME} v{BOT_VERSION}...")
    
    try:
        # Create application
        application = create_application()
        
        # Set up post-init
        application.post_init = post_init
        
        # Run the bot until stopped
        logger.info("Bot is running. Press Ctrl+C to stop.")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
