"""
Slack mock data generator for testing burnout detection patterns.
Generates realistic Slack communication patterns for different burnout levels.
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SlackMockGenerator:
    """Generate mock Slack data for testing burnout analysis."""
    
    def __init__(self, workspace_id: str = "T0001TESTWS"):
        self.workspace_id = workspace_id
        self.channels = self._generate_channels()
        self.users = {}
        
        # Communication patterns by burnout risk level
        self.patterns = {
            "healthy": {
                "messages_per_day": (5, 15),
                "after_hours_ratio": 0.05,
                "weekend_ratio": 0.02,
                "response_time_minutes": (5, 30),
                "thread_participation": 0.7,
                "emoji_usage": 0.3,
                "message_length": (20, 100),
                "channels_active": (3, 5),
                "dm_ratio": 0.2
            },
            "moderate": {
                "messages_per_day": (15, 30),
                "after_hours_ratio": 0.20,
                "weekend_ratio": 0.10,
                "response_time_minutes": (1, 10),
                "thread_participation": 0.5,
                "emoji_usage": 0.15,
                "message_length": (10, 50),
                "channels_active": (5, 8),
                "dm_ratio": 0.35
            },
            "high": {
                "messages_per_day": (30, 60),
                "after_hours_ratio": 0.40,
                "weekend_ratio": 0.25,
                "response_time_minutes": (0.5, 5),
                "thread_participation": 0.3,
                "emoji_usage": 0.05,
                "message_length": (5, 30),
                "channels_active": (8, 15),
                "dm_ratio": 0.5
            }
        }
        
        # Message templates for different contexts
        self.message_templates = {
            "incident": [
                "Looking into the {service} alert",
                "I'll check the {metric} spike",
                "Investigating the {issue} now",
                "Need help with {service} incident",
                "{service} is showing {symptom}",
                "Escalating {issue} to {team}"
            ],
            "general": [
                "Hey team, quick update on {project}",
                "Thanks for the help with {task}",
                "Can someone review {pr}?",
                "Meeting notes from {meeting} sync",
                "Following up on {topic}",
                "Question about {feature}"
            ],
            "stressed": [
                "Still working on {issue}",
                "Haven't had time to look at {task}",
                "Too many fires today",
                "Can someone else take {task}?",
                "Buried in {work}, will get to it",
                "Another {issue} just came up"
            ],
            "after_hours": [
                "Still debugging {issue}",
                "Finally fixed {bug}",
                "Pushing the {fix} now",
                "Will check in the morning",
                "Logging off for tonight",
                "One more thing on {task}"
            ]
        }
    
    def _generate_channels(self) -> List[Dict[str, Any]]:
        """Generate mock Slack channels."""
        return [
            {"id": "C001GENERAL", "name": "general", "is_general": True},
            {"id": "C002INCIDENT", "name": "incidents", "is_incident": True},
            {"id": "C003ENGIN", "name": "engineering", "is_private": False},
            {"id": "C004ALERT", "name": "alerts", "is_alert": True},
            {"id": "C005ONCALL", "name": "on-call", "is_private": False},
            {"id": "C006RANDOM", "name": "random", "is_social": True},
            {"id": "C007HELP", "name": "help-requests", "is_support": True},
            {"id": "C008DEPLOY", "name": "deployments", "is_private": False},
            {"id": "C009BUGS", "name": "bug-reports", "is_private": False},
            {"id": "C010STATUS", "name": "status-updates", "is_private": False}
        ]
    
    def generate_user(self, email: str, name: str, risk_level: str = "healthy") -> Dict[str, Any]:
        """Generate a mock Slack user with specified burnout risk level."""
        user_id = f"U{len(self.users):03d}{name[:3].upper()}"
        
        user = {
            "id": user_id,
            "team_id": self.workspace_id,
            "name": name.lower().replace(" ", "."),
            "real_name": name,
            "email": email,
            "risk_level": risk_level,
            "is_bot": False,
            "is_admin": random.random() < 0.1,
            "tz": "America/Los_Angeles",
            "tz_offset": -28800,
            "profile": {
                "email": email,
                "real_name": name,
                "display_name": name.split()[0].lower(),
                "status_text": self._generate_status(risk_level),
                "status_emoji": self._generate_status_emoji(risk_level)
            }
        }
        
        self.users[email] = user
        return user
    
    def _generate_status(self, risk_level: str) -> str:
        """Generate realistic status text based on risk level."""
        statuses = {
            "healthy": ["Working on feature", "In flow", "Available", "Coding", ""],
            "moderate": ["In meetings", "Busy", "Do not disturb", "Heads down", "OOO later"],
            "high": ["Firefighting", "On incident", "Very busy", "Do not disturb", "😴"]
        }
        return random.choice(statuses.get(risk_level, [""]))
    
    def _generate_status_emoji(self, risk_level: str) -> str:
        """Generate status emoji based on risk level."""
        emojis = {
            "healthy": [":computer:", ":coffee:", ":rocket:", ":sparkles:", ""],
            "moderate": [":fire:", ":warning:", ":clock1:", ":zzz:", ""],
            "high": [":fire:", ":rotating_light:", ":sob:", ":tired_face:", ":sos:"]
        }
        return random.choice(emojis.get(risk_level, [""]))
    
    def generate_messages(self, user: Dict[str, Any], days: int = 30) -> List[Dict[str, Any]]:
        """Generate mock Slack messages for a user over specified days."""
        messages = []
        pattern = self.patterns[user["risk_level"]]
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Select active channels for this user
        num_channels = random.randint(*pattern["channels_active"])
        active_channels = random.sample(self.channels, min(num_channels, len(self.channels)))
        
        current_date = start_date
        while current_date <= end_date:
            # Determine number of messages for this day
            is_weekend = current_date.weekday() >= 5
            
            if is_weekend and random.random() > pattern["weekend_ratio"]:
                # Skip most weekend days based on pattern
                current_date += timedelta(days=1)
                continue
            
            daily_messages = random.randint(*pattern["messages_per_day"])
            if is_weekend:
                daily_messages = int(daily_messages * 0.3)  # Fewer messages on weekends
            
            # Generate messages throughout the day
            for _ in range(daily_messages):
                # Determine message time
                if random.random() < pattern["after_hours_ratio"]:
                    # After hours message (before 9am or after 6pm)
                    if random.random() < 0.3:
                        hour = random.randint(6, 8)  # Early morning
                    else:
                        hour = random.randint(18, 23)  # Evening
                else:
                    # Business hours
                    hour = random.randint(9, 17)
                
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                
                timestamp = current_date.replace(hour=hour, minute=minute, second=second)
                
                # Select channel (or DM)
                if random.random() < pattern["dm_ratio"]:
                    # Direct message
                    channel = f"D{random.randint(100, 999)}ABCDE"
                    is_dm = True
                else:
                    channel = random.choice(active_channels)["id"]
                    is_dm = False
                
                # Generate message content
                message_type = self._get_message_type(hour, user["risk_level"], channel)
                text = self._generate_message_text(message_type, pattern)
                
                message = {
                    "type": "message",
                    "user": user["id"],
                    "text": text,
                    "ts": str(timestamp.timestamp()),
                    "channel": channel,
                    "team": self.workspace_id,
                    "thread_ts": self._maybe_thread(pattern["thread_participation"]),
                    "reply_count": 0 if random.random() > 0.2 else random.randint(1, 5),
                    "reactions": self._generate_reactions(pattern["emoji_usage"]),
                    "is_dm": is_dm,
                    "metadata": {
                        "is_after_hours": hour < 9 or hour >= 18,
                        "is_weekend": is_weekend,
                        "message_type": message_type,
                        "hour": hour
                    }
                }
                
                messages.append(message)
            
            current_date += timedelta(days=1)
        
        return messages
    
    def _get_message_type(self, hour: int, risk_level: str, channel: str) -> str:
        """Determine message type based on context."""
        if "incident" in channel.lower() or "alert" in channel.lower():
            return "incident"
        elif (hour < 9 or hour >= 18) and risk_level == "high":
            return "after_hours"
        elif risk_level == "high" and random.random() < 0.3:
            return "stressed"
        else:
            return "general"
    
    def _generate_message_text(self, message_type: str, pattern: Dict) -> str:
        """Generate realistic message text."""
        template = random.choice(self.message_templates[message_type])
        
        # Fill in placeholders
        placeholders = {
            "service": random.choice(["API", "database", "cache", "queue", "frontend"]),
            "metric": random.choice(["CPU", "memory", "latency", "error rate", "throughput"]),
            "issue": random.choice(["timeout", "spike", "outage", "degradation", "error"]),
            "team": random.choice(["SRE", "platform", "backend", "oncall", "security"]),
            "symptom": random.choice(["errors", "slow responses", "timeouts", "high load"]),
            "project": random.choice(["migration", "feature", "refactor", "optimization"]),
            "task": random.choice(["PR review", "deployment", "investigation", "update"]),
            "pr": random.choice(["PR #123", "the config change", "the hotfix", "my PR"]),
            "meeting": random.choice(["standup", "planning", "retro", "1:1", "all-hands"]),
            "topic": random.choice(["deployment", "architecture", "process", "tooling"]),
            "feature": random.choice(["auth", "API", "dashboard", "monitoring", "config"]),
            "work": random.choice(["incidents", "tickets", "reviews", "meetings"]),
            "bug": random.choice(["race condition", "memory leak", "NPE", "timeout"]),
            "fix": random.choice(["patch", "hotfix", "workaround", "solution"])
        }
        
        text = template
        for key, value in placeholders.items():
            text = text.replace(f"{{{key}}}", value)
        
        # Vary message length
        min_len, max_len = pattern["message_length"]
        if len(text) < min_len:
            text += " " + " ".join(random.choices(["Thanks!", "Let me know.", "PTAL.", "FYI.", "cc @team"], k=2))
        
        return text
    
    def _maybe_thread(self, participation_rate: float) -> Optional[str]:
        """Maybe make this message part of a thread."""
        if random.random() < participation_rate and random.random() < 0.3:
            # Part of a thread
            return f"{random.randint(1600000000, 1700000000)}.{random.randint(100000, 999999)}"
        return None
    
    def _generate_reactions(self, emoji_rate: float) -> List[Dict[str, Any]]:
        """Generate emoji reactions."""
        reactions = []
        if random.random() < emoji_rate:
            num_reactions = random.randint(1, 3)
            emojis = random.sample(["thumbsup", "eyes", "white_check_mark", "pray", "fire", 
                                   "rocket", "heart", "thinking_face", "100"], num_reactions)
            for emoji in emojis:
                reactions.append({
                    "name": emoji,
                    "count": random.randint(1, 5),
                    "users": [f"U{random.randint(100, 999)}TEST"]
                })
        return reactions
    
    def save_mock_data(self, output_dir: str = "mock_slack_data"):
        """Save generated mock data to files."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save users
        users_file = output_path / "users.json"
        with open(users_file, "w") as f:
            json.dump(list(self.users.values()), f, indent=2)
        
        # Save channels
        channels_file = output_path / "channels.json"
        with open(channels_file, "w") as f:
            json.dump(self.channels, f, indent=2)
        
        # Save messages by user
        messages_dir = output_path / "messages"
        messages_dir.mkdir(exist_ok=True)
        
        for email, user in self.users.items():
            user_messages = self.generate_messages(user)
            user_file = messages_dir / f"{user['id']}_messages.json"
            with open(user_file, "w") as f:
                json.dump(user_messages, f, indent=2)
            
            print(f"Generated {len(user_messages)} messages for {user['real_name']} ({user['risk_level']})")
        
        # Save summary
        summary = {
            "workspace_id": self.workspace_id,
            "total_users": len(self.users),
            "total_channels": len(self.channels),
            "generation_date": datetime.now().isoformat(),
            "risk_distribution": {
                "healthy": sum(1 for u in self.users.values() if u["risk_level"] == "healthy"),
                "moderate": sum(1 for u in self.users.values() if u["risk_level"] == "moderate"),
                "high": sum(1 for u in self.users.values() if u["risk_level"] == "high")
            }
        }
        
        summary_file = output_path / "summary.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)
        
        print(f"\nMock data saved to {output_path}/")
        return output_path


def generate_test_workspace(rootly_users: List[Dict[str, Any]]) -> SlackMockGenerator:
    """Generate a test Slack workspace matching Rootly users."""
    generator = SlackMockGenerator()
    
    # Assign risk levels based on some distribution
    risk_distribution = {
        "healthy": 0.6,
        "moderate": 0.3,
        "high": 0.1
    }
    
    for i, user in enumerate(rootly_users):
        # Determine risk level
        rand = random.random()
        if rand < risk_distribution["high"]:
            risk_level = "high"
        elif rand < risk_distribution["high"] + risk_distribution["moderate"]:
            risk_level = "moderate"
        else:
            risk_level = "healthy"
        
        generator.generate_user(
            email=user.get("email", f"user{i}@example.com"),
            name=user.get("name", f"Test User {i}"),
            risk_level=risk_level
        )
    
    return generator


if __name__ == "__main__":
    # Example usage
    print("Generating mock Slack data...")
    
    # Create test users
    test_users = [
        {"email": "alice@rootly.com", "name": "Alice Chen"},
        {"email": "bob@rootly.com", "name": "Bob Smith"},
        {"email": "charlie@rootly.com", "name": "Charlie Davis"},
        {"email": "dana@rootly.com", "name": "Dana Wilson"},
        {"email": "eve@rootly.com", "name": "Eve Johnson"},
    ]
    
    generator = generate_test_workspace(test_users)
    generator.save_mock_data()
    
    print("\nDone! You can now use this mock data to test Slack integration.")