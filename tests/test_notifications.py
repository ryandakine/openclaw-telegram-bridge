"""
Tests for the Notification System

Run tests with:
    python -m pytest tests/test_notifications.py -v
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from notifications.formatter import (
    NotificationFormatter,
    NotificationType,
    TaskInfo,
    QuestionOption,
)
from notifications.manager import NotificationManager, PendingQuestion


class TestNotificationFormatter:
    """Tests for NotificationFormatter class."""
    
    def test_notification_type_values(self):
        """Test that notification types have correct values."""
        assert NotificationType.INFO.emoji == "ℹ️"
        assert NotificationType.SUCCESS.emoji == "✅"
        assert NotificationType.WARNING.emoji == "⚠️"
        assert NotificationType.ERROR.emoji == "❌"
        assert NotificationType.TASK_START.emoji == "🚀"
    
    def test_format_task_started(self):
        """Test task started notification formatting."""
        task = TaskInfo(id="T001", description="Test task")
        message = NotificationFormatter.format_task_started(task)
        
        assert "🚀" in message
        assert "Task Started" in message
        assert "T001" in message
        assert "Test task" in message
        assert "<b>" in message  # HTML formatting
    
    def test_format_task_completed(self):
        """Test task completed notification formatting."""
        task = TaskInfo(
            id="T001",
            description="Test task",
            duration_minutes=5.5,
            files_created=["file1.py", "file2.py"],
            result_summary="Success!"
        )
        message = NotificationFormatter.format_task_completed(task)
        
        assert "✨" in message
        assert "Task Complete" in message
        assert "5 minutes" in message or "6 minutes" in message
        assert "file1.py" in message
        assert "file2.py" in message
        assert "Success!" in message
    
    def test_format_task_failed(self):
        """Test task failed notification formatting."""
        task = TaskInfo(
            id="T001",
            description="Test task",
            error_message="Something went wrong"
        )
        message = NotificationFormatter.format_task_failed(task)
        
        assert "💥" in message
        assert "Task Failed" in message
        assert "Something went wrong" in message
    
    def test_format_question(self):
        """Test question formatting."""
        message = NotificationFormatter.format_question("Is this a test?")
        
        assert "❓" in message
        assert "Is this a test?" in message
    
    def test_format_question_with_options(self):
        """Test question formatting with options."""
        options = [
            QuestionOption("Yes", "yes", "✅"),
            QuestionOption("No", "no", "❌"),
        ]
        message = NotificationFormatter.format_question("Continue?", options)
        
        assert "❓" in message
        assert "Continue?" in message
        assert "Options:" in message
    
    def test_format_question_with_context(self):
        """Test question formatting with context."""
        message = NotificationFormatter.format_question(
            "Delete file?",
            context="This action cannot be undone"
        )
        
        assert "Delete file?" in message
        assert "Context:" in message
        assert "cannot be undone" in message
    
    def test_format_progress(self):
        """Test progress formatting."""
        message = NotificationFormatter.format_progress(
            current=50,
            total=100,
            description="Processing"
        )
        
        assert "📊" in message
        assert "Progress Update" in message
        assert "Processing" in message
        assert "50%" in message
        assert "█" in message  # Progress bar
        assert "░" in message  # Empty progress
        assert "50/100" in message
    
    def test_format_progress_with_eta(self):
        """Test progress formatting with ETA."""
        message = NotificationFormatter.format_progress(
            current=50,
            total=100,
            description="Processing",
            eta_seconds=120
        )
        
        assert "ETA:" in message
        assert "2m" in message or "120s" in message
    
    def test_format_error_alert(self):
        """Test error alert formatting."""
        message = NotificationFormatter.format_error_alert(
            error="Connection failed",
            context="Database connection",
            suggestion="Check network settings"
        )
        
        assert "❌" in message
        assert "Error Alert" in message
        assert "Connection failed" in message
        assert "Database connection" in message
        assert "Suggestion:" in message
        assert "Check network settings" in message
    
    def test_format_status_update(self):
        """Test status update formatting."""
        active_tasks = [
            TaskInfo(id="T1", description="Task 1"),
            TaskInfo(id="T2", description="Task 2"),
        ]
        recent_completed = [
            TaskInfo(id="T0", description="Completed task"),
        ]
        
        message = NotificationFormatter.format_status_update(
            working_dir="/home/test",
            active_tasks=active_tasks,
            recent_completed=recent_completed
        )
        
        assert "🔧" in message
        assert "System Status" in message
        assert "/home/test" in message
        assert "T1" in message
        assert "T2" in message
        assert "Active Tasks (2)" in message
    
    def test_format_file_notification(self):
        """Test file notification formatting."""
        message = NotificationFormatter.format_file_notification(
            file_name="test.txt",
            file_size="1.5 MB",
            action="received"
        )
        
        assert "📁" in message
        assert "File Received" in message
        assert "test.txt" in message
        assert "1.5 MB" in message
    
    def test_create_inline_keyboard_horizontal(self):
        """Test horizontal keyboard layout."""
        options = [
            QuestionOption("A", "a"),
            QuestionOption("B", "b"),
        ]
        keyboard = NotificationFormatter.create_inline_keyboard(options, "horizontal")
        
        assert len(keyboard) == 1  # One row
        assert len(keyboard[0]) == 2  # Two buttons
        assert keyboard[0][0]["text"] == "A"
        assert keyboard[0][0]["callback_data"] == "a"
    
    def test_create_inline_keyboard_vertical(self):
        """Test vertical keyboard layout."""
        options = [
            QuestionOption("A", "a"),
            QuestionOption("B", "b"),
        ]
        keyboard = NotificationFormatter.create_inline_keyboard(options, "vertical")
        
        assert len(keyboard) == 2  # Two rows
        assert len(keyboard[0]) == 1  # One button per row
    
    def test_create_inline_keyboard_grid(self):
        """Test grid keyboard layout."""
        options = [
            QuestionOption("A", "a"),
            QuestionOption("B", "b"),
            QuestionOption("C", "c"),
            QuestionOption("D", "d"),
        ]
        keyboard = NotificationFormatter.create_inline_keyboard(options, "grid")
        
        assert len(keyboard) == 2  # Two rows (4 options / 2 per row)
        assert len(keyboard[0]) == 2  # Two buttons per row
    
    def test_create_yes_no_keyboard(self):
        """Test yes/no keyboard creation."""
        keyboard = NotificationFormatter.create_yes_no_keyboard()
        
        assert len(keyboard) == 1  # One row
        assert len(keyboard[0]) == 2  # Yes and No
        assert "✅" in keyboard[0][0]["text"]
        assert "❌" in keyboard[0][1]["text"]
    
    def test_create_yes_no_keyboard_with_more(self):
        """Test yes/no keyboard with more option."""
        keyboard = NotificationFormatter.create_yes_no_keyboard(more_callback="more")
        
        assert len(keyboard) == 1
        assert len(keyboard[0]) == 3  # Yes, No, and More
    
    def test_create_progress_keyboard(self):
        """Test progress keyboard creation."""
        keyboard = NotificationFormatter.create_progress_keyboard("TASK-001")
        
        assert len(keyboard) == 2  # View Details and Cancel
        assert "View Details" in keyboard[0][0]["text"]
        assert "Cancel Task" in keyboard[1][0]["text"]
    
    def test_escape_html(self):
        """Test HTML escaping."""
        text = "<script>alert('xss')</script>"
        escaped = NotificationFormatter._escape_html(text)
        
        assert "<script>" not in escaped
        assert "&lt;script&gt;" in escaped
    
    def test_truncate_message(self):
        """Test message truncation."""
        long_message = "A" * 5000
        truncated = NotificationFormatter.truncate_message(long_message, max_length=100)
        
        assert len(truncated) <= 100
        assert truncated.endswith("...")
    
    def test_format_code_block(self):
        """Test code block formatting."""
        code = "print('hello')"
        formatted = NotificationFormatter.format_code_block(code, "python")
        
        assert "```python" in formatted
        assert "print('hello')" in formatted
        assert "```" in formatted
    
    def test_format_inline_code(self):
        """Test inline code formatting."""
        text = "variable_name"
        formatted = NotificationFormatter.format_inline_code(text)
        
        assert formatted == "`variable_name`"
    
    def test_task_info_with_emoji(self):
        """Test question option with emoji."""
        opt = QuestionOption("Yes", "yes", "✅")
        keyboard = NotificationFormatter.create_inline_keyboard([opt])
        
        assert "✅" in keyboard[0][0]["text"]
        assert "Yes" in keyboard[0][0]["text"]


class TestNotificationManager:
    """Tests for NotificationManager class."""
    
    def test_manager_initialization(self):
        """Test manager can be initialized without bot."""
        manager = NotificationManager()
        assert manager.bot is None
        assert manager.chat_id is None
        assert manager.message_states == {}
        assert manager.pending_questions == {}
    
    def test_manager_with_params(self):
        """Test manager initialization with parameters."""
        manager = NotificationManager(bot=None, chat_id="12345")
        assert manager.chat_id == "12345"
    
    def test_register_callback_handler(self):
        """Test callback handler registration."""
        manager = NotificationManager()
        
        def handler(data):
            return data
        
        manager.register_callback_handler("test", handler)
        assert "test" in manager.callback_handlers
    
    def test_pending_question_creation(self):
        """Test PendingQuestion dataclass."""
        from datetime import datetime
        
        pq = PendingQuestion(
            question_id="q1",
            question_text="Test?",
            timeout_seconds=60
        )
        
        assert pq.question_id == "q1"
        assert pq.question_text == "Test?"
        assert pq.timeout_seconds == 60
        assert pq.answered is False
        assert pq.answer is None


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_empty_task_description(self):
        """Test formatting with empty description."""
        task = TaskInfo(id="T1", description="")
        message = NotificationFormatter.format_task_started(task)
        assert "T1" in message
    
    def test_long_error_message(self):
        """Test that long errors are truncated."""
        long_error = "Error: " + "X" * 2000
        message = NotificationFormatter.format_error_alert(long_error)
        assert len(message) < 1500  # Should be truncated
    
    def test_progress_zero_percent(self):
        """Test progress at 0%."""
        message = NotificationFormatter.format_progress(0, 100, "Starting")
        assert "0%" in message
        assert "0/100" in message
    
    def test_progress_100_percent(self):
        """Test progress at 100%."""
        message = NotificationFormatter.format_progress(100, 100, "Done")
        assert "100%" in message
        assert "100/100" in message
    
    def test_no_active_tasks(self):
        """Test status with no tasks."""
        message = NotificationFormatter.format_status_update(
            working_dir="/test",
            active_tasks=[],
            recent_completed=[]
        )
        assert "Active Tasks:" in message
        assert "None" in message or "0" in message


if __name__ == "__main__":
    # Run tests with pytest if available
    try:
        import pytest
        pytest.main([__file__, "-v"])
    except ImportError:
        print("pytest not installed, running basic tests...")
        
        # Run basic tests manually
        test_class = TestNotificationFormatter()
        for method_name in dir(test_class):
            if method_name.startswith("test_"):
                try:
                    getattr(test_class, method_name)()
                    print(f"✅ {method_name}")
                except AssertionError as e:
                    print(f"❌ {method_name}: {e}")
                except Exception as e:
                    print(f"💥 {method_name}: {e}")
        
        print("\nBasic tests complete!")
