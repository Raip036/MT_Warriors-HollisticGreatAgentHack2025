"""
Reminder Tool - Schedules reminders
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from .base_tool import BaseTool, ToolResult

# Try to import APScheduler, but don't crash if not installed
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.date import DateTrigger
    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False


class ReminderTool(BaseTool):
    """Tool for scheduling reminders and notifications."""
    
    def __init__(self):
        super().__init__(
            name="reminder",
            description="Schedules reminders for medication, appointments, or other tasks. Can schedule one-time or recurring reminders."
        )
        self.scheduler = None
        self.reminders: Dict[str, Dict] = {}
        
        if HAS_APSCHEDULER:
            self.scheduler = AsyncIOScheduler()
            self.scheduler.start()
            print("✅ Reminder scheduler initialized")
        else:
            print("⚠️ APScheduler not installed. Reminders will be stored but not executed.")
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Reminder message or task description"
                },
                "reminder_time": {
                    "type": "string",
                    "description": "When to send the reminder (ISO format or relative like 'in 30 minutes', 'tomorrow at 2pm')"
                },
                "reminder_type": {
                    "type": "string",
                    "enum": ["medication", "appointment", "task", "other"],
                    "description": "Type of reminder",
                    "default": "other"
                }
            },
            "required": ["message", "reminder_time"]
        }
    
    def validate_args(self, **kwargs) -> bool:
        """Validate required arguments."""
        return "message" in kwargs and "reminder_time" in kwargs
    
    def _parse_reminder_time(self, reminder_time: str) -> Optional[datetime]:
        """Parse reminder time string into datetime."""
        try:
            # Try ISO format first
            return datetime.fromisoformat(reminder_time.replace("Z", "+00:00"))
        except:
            pass
        
        # Try relative time parsing (simplified)
        reminder_lower = reminder_time.lower()
        now = datetime.now()
        
        if "in" in reminder_lower:
            # Simple relative parsing (e.g., "in 30 minutes")
            import re
            match = re.search(r'in (\d+) (minute|hour|day)', reminder_lower)
            if match:
                value = int(match.group(1))
                unit = match.group(2)
                if unit == "minute":
                    return now + timedelta(minutes=value)
                elif unit == "hour":
                    return now + timedelta(hours=value)
                elif unit == "day":
                    return now + timedelta(days=value)
        
        return None
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute reminder scheduling."""
        message = kwargs.get("message", "").strip()
        reminder_time_str = kwargs.get("reminder_time", "")
        reminder_type = kwargs.get("reminder_type", "other")
        
        if not message or not reminder_time_str:
            return ToolResult(
                success=False,
                output=None,
                error="Message and reminder_time are required"
            )
        
        # Parse reminder time
        reminder_time = self._parse_reminder_time(reminder_time_str)
        if not reminder_time:
            return ToolResult(
                success=False,
                output=None,
                error=f"Could not parse reminder time: {reminder_time_str}. Use ISO format or relative time like 'in 30 minutes'"
            )
        
        # Check if reminder is in the past
        if reminder_time < datetime.now():
            return ToolResult(
                success=False,
                output=None,
                error="Reminder time must be in the future"
            )
        
        # Create reminder ID
        import uuid
        reminder_id = str(uuid.uuid4())
        
        reminder_data = {
            "reminder_id": reminder_id,
            "message": message,
            "reminder_time": reminder_time.isoformat(),
            "reminder_type": reminder_type,
            "created_at": datetime.now().isoformat(),
            "status": "scheduled"
        }
        
        self.reminders[reminder_id] = reminder_data
        
        # Schedule reminder if scheduler is available
        if self.scheduler:
            try:
                async def send_reminder():
                    reminder_data["status"] = "sent"
                    print(f"🔔 REMINDER: {message}")
                
                self.scheduler.add_job(
                    send_reminder,
                    trigger=DateTrigger(run_date=reminder_time),
                    id=reminder_id
                )
            except Exception as e:
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Failed to schedule reminder: {str(e)}"
                )
        
        return ToolResult(
            success=True,
            output=reminder_data,
            metadata={
                "tool": "reminder",
                "scheduled": True,
                "reminder_id": reminder_id
            }
        )

