#!/usr/bin/env python3
"""
OpenClaw Telegram Bridge - Kimi Code CLI Integration Layer

This module provides the bridge between Kimi Code CLI and the Telegram bot,
enabling bi-directional communication for remote task management.
"""

import json
import os
import sys
import uuid
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Default storage paths
STORAGE_DIR = Path(__file__).parent / "storage"
QUEUE_FILE = STORAGE_DIR / "queue.json"
RESPONSES_FILE = STORAGE_DIR / "responses.json"

# Ensure storage directory exists
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def _init_storage():
    """Initialize storage files if they don't exist."""
    if not QUEUE_FILE.exists():
        QUEUE_FILE.write_text(json.dumps([], indent=2))
    if not RESPONSES_FILE.exists():
        RESPONSES_FILE.write_text(json.dumps([], indent=2))


def _load_json(filepath: Path) -> list:
    """Load JSON data from file."""
    if not filepath.exists():
        return []
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_json(filepath: Path, data: list):
    """Save JSON data to file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def get_pending_tasks() -> list:
    """
    Return a list of pending tasks from the queue.
    
    Returns:
        List of task dictionaries with status 'pending'
    """
    _init_storage()
    queue = _load_json(QUEUE_FILE)
    return [item for item in queue if item.get('status') == 'pending']


def mark_task_complete(task_id: str, result: str) -> bool:
    """
    Mark a task as complete with the given result.
    
    Args:
        task_id: The unique ID of the task
        result: The result/completion message
        
    Returns:
        True if successful, False if task not found
    """
    _init_storage()
    queue = _load_json(QUEUE_FILE)
    
    task_found = False
    for item in queue:
        if item.get('id') == task_id:
            item['status'] = 'completed'
            item['completed_at'] = datetime.now(timezone.utc).isoformat()
            item['result'] = result
            task_found = True
            break
    
    if task_found:
        _save_json(QUEUE_FILE, queue)
        
        # Also add to responses for notification
        responses = _load_json(RESPONSES_FILE)
        responses.append({
            'id': str(uuid.uuid4()),
            'type': 'completion',
            'task_id': task_id,
            'content': result,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        _save_json(RESPONSES_FILE, responses)
        
    return task_found


def send_notification(message: str, notification_type: str = 'info') -> dict:
    """
    Format a message for Telegram notification and save to responses.
    
    Args:
        message: The notification message content
        notification_type: Type of notification (info, success, warning, error)
        
    Returns:
        The created notification entry
    """
    _init_storage()
    
    notification = {
        'id': str(uuid.uuid4()),
        'type': 'notification',
        'notification_type': notification_type,
        'content': message,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'formatted_for_telegram': _format_telegram_message(message, notification_type)
    }
    
    responses = _load_json(RESPONSES_FILE)
    responses.append(notification)
    _save_json(RESPONSES_FILE, responses)
    
    return notification


def _format_telegram_message(message: str, msg_type: str = 'info') -> str:
    """
    Format a message for Telegram with appropriate emoji and styling.
    
    Args:
        message: The raw message content
        msg_type: Type of message for emoji selection
        
    Returns:
        Formatted message string
    """
    emojis = {
        'info': 'ℹ️',
        'success': '✅',
        'warning': '⚠️',
        'error': '❌',
        'task': '📋',
        'question': '❓'
    }
    
    emoji = emojis.get(msg_type, 'ℹ️')
    return f"{emoji} {message}"


def process_queue():
    """
    Process all pending tasks in the queue.
    Prints tasks and questions to console for Kimi to see.
    """
    _init_storage()
    queue = _load_json(QUEUE_FILE)
    
    pending_items = [item for item in queue if item.get('status') == 'pending']
    
    if not pending_items:
        print("=" * 60)
        print("🤖 Kimi Code CLI - OpenClaw Telegram Bridge")
        print("=" * 60)
        print("No pending tasks or questions.")
        print("-" * 60)
        return
    
    print("=" * 60)
    print("🤖 Kimi Code CLI - OpenClaw Telegram Bridge")
    print("=" * 60)
    print(f"\n📥 Found {len(pending_items)} pending item(s):\n")
    
    for item in pending_items:
        item_type = item.get('type', 'unknown')
        item_id = item.get('id', 'unknown')
        content = item.get('content', '')
        timestamp = item.get('timestamp', 'unknown')
        
        if item_type == 'task':
            print(f"\n📋 TASK #{item_id[:8]}")
            print(f"   Time: {timestamp}")
            print(f"   Content: {content}")
            print(f"   {'-' * 50}")
            
        elif item_type == 'question':
            print(f"\n❓ QUESTION #{item_id[:8]}")
            print(f"   Time: {timestamp}")
            print(f"   Question: {content}")
            print(f"   {'-' * 50}")
        
        # Mark as processing
        item['status'] = 'processing'
        item['processing_started_at'] = datetime.now(timezone.utc).isoformat()
    
    # Update queue with processing status
    _save_json(QUEUE_FILE, queue)
    
    print("\n💡 Use 'bridge.py complete <id> <result>' when done")
    print("=" * 60)


def add_task_to_queue(content: str, item_type: str = 'task') -> dict:
    """
    Add a new task or question to the queue.
    
    Args:
        content: The task/question content
        item_type: Type of item ('task' or 'question')
        
    Returns:
        The created queue item
    """
    _init_storage()
    
    item = {
        'id': str(uuid.uuid4()),
        'type': item_type,
        'content': content,
        'status': 'pending',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'from': 'user',
        'metadata': {}
    }
    
    queue = _load_json(QUEUE_FILE)
    queue.append(item)
    _save_json(QUEUE_FILE, queue)
    
    return item


def list_pending_tasks():
    """Display all pending tasks in a formatted list."""
    tasks = get_pending_tasks()
    
    print("=" * 60)
    print("📋 Pending Tasks & Questions")
    print("=" * 60)
    
    if not tasks:
        print("\nNo pending items.")
    else:
        for task in tasks:
            task_id = task.get('id', 'unknown')[:8]
            task_type = task.get('type', 'unknown').upper()
            content = task.get('content', '')[:50]
            if len(task.get('content', '')) > 50:
                content += '...'
            
            print(f"\n[{task_type}] #{task_id}")
            print(f"  {content}")
    
    print("\n" + "-" * 60)


def complete_task(task_id_short: str, result: str):
    """
    Mark a task as complete using a short ID prefix.
    
    Args:
        task_id_short: The first 8 characters (or full) task ID
        result: The completion result
    """
    _init_storage()
    queue = _load_json(QUEUE_FILE)
    
    # Find task by full or partial ID
    matching_task = None
    for item in queue:
        if item.get('id', '').startswith(task_id_short):
            matching_task = item
            break
    
    if not matching_task:
        print(f"❌ Task with ID '{task_id_short}' not found.")
        return False
    
    full_id = matching_task['id']
    success = mark_task_complete(full_id, result)
    
    if success:
        print(f"✅ Task #{task_id_short} marked as complete.")
        print(f"📤 Result sent to Telegram notification queue.")
    else:
        print(f"❌ Failed to complete task #{task_id_short}.")
    
    return success


def ask_user(question: str):
    """
    Send a question to the user via Telegram.
    
    Args:
        question: The question to ask
    """
    _init_storage()
    
    # Add to queue as a question from Kimi
    item = {
        'id': str(uuid.uuid4()),
        'type': 'question_from_kimi',
        'content': question,
        'status': 'pending',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'from': 'kimi',
        'metadata': {}
    }
    
    queue = _load_json(QUEUE_FILE)
    queue.append(item)
    _save_json(QUEUE_FILE, queue)
    
    # Also add to responses for notification
    notification = send_notification(question, 'question')
    
    print(f"❓ Question sent to user via Telegram:")
    print(f"   {question}")
    
    return notification


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="OpenClaw Telegram Bridge - Kimi Code CLI Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  bridge.py                    Process queue and display pending items
  bridge.py list              Show pending tasks
  bridge.py complete abc123 "Done!"  Mark task abc123 as complete
  bridge.py ask "What color?"  Send question to user via Telegram
        """
    )
    
    parser.add_argument(
        'command',
        nargs='?',
        choices=['list', 'complete', 'ask'],
        help='Command to execute (list, complete, ask)'
    )
    parser.add_argument(
        'args',
        nargs='*',
        help='Additional arguments for the command'
    )
    
    args = parser.parse_args()
    
    # Initialize storage
    _init_storage()
    
    if args.command is None:
        # Default: process queue and show pending items
        process_queue()
    
    elif args.command == 'list':
        list_pending_tasks()
    
    elif args.command == 'complete':
        if len(args.args) < 2:
            print("❌ Usage: bridge.py complete <task_id> <result>")
            print("   Example: bridge.py complete abc123 'Task completed successfully!'")
            sys.exit(1)
        
        task_id = args.args[0]
        result = ' '.join(args.args[1:])
        complete_task(task_id, result)
    
    elif args.command == 'ask':
        if not args.args:
            print("❌ Usage: bridge.py ask <question>")
            print("   Example: bridge.py ask 'Should I use blue or green?'")
            sys.exit(1)
        
        question = ' '.join(args.args)
        ask_user(question)


if __name__ == '__main__':
    main()
