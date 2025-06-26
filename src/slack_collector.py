"""
Slack data collector for burnout analysis.
Supports both real Slack API and mock data for testing.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import requests
from collections import defaultdict
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)


class SlackCollector:
    """Collect and analyze Slack communication patterns for burnout detection."""
    
    def __init__(self, token: Optional[str] = None, config: Dict[str, Any] = None):
        self.token = token
        self.config = config or {}
        self.mock_mode = self.config.get('slack_integration', {}).get('mock_mode', False)
        self.mock_data_dir = Path(self.config.get('slack_integration', {}).get('mock_data_dir', 'mock_slack_data'))
        
        if not self.mock_mode and not self.token:
            raise ValueError("Slack token required for API mode. Use mock_mode=True for testing.")
        
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        } if self.token else {}
        
        # Cache for API responses
        self.cache_dir = Path('.slack_cache')
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize sentiment analyzer
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
    
    def collect_slack_data(self, user_mappings: Dict[str, str], days: int = 30) -> Dict[str, Any]:
        """
        Collect Slack activity data for users.
        
        Args:
            user_mappings: Dict mapping Rootly email to Slack user ID
            days: Number of days to analyze
            
        Returns:
            Dict mapping Slack user ID to activity metrics
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        slack_activity = {}
        
        for rootly_email, slack_user_id in user_mappings.items():
            if not slack_user_id:
                continue
            
            logger.info(f"Collecting Slack data for {rootly_email} (Slack: {slack_user_id})")
            
            if self.mock_mode:
                user_activity = self._collect_mock_data(slack_user_id, start_date, end_date)
            else:
                user_activity = self._collect_api_data(slack_user_id, start_date, end_date)
            
            if user_activity:
                slack_activity[slack_user_id] = {
                    'user_id': slack_user_id,
                    'email': rootly_email,
                    'metrics': self._calculate_metrics(user_activity, days),
                    'raw_stats': user_activity
                }
        
        return slack_activity
    
    def _collect_mock_data(self, user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Collect data from mock files."""
        messages_file = self.mock_data_dir / "messages" / f"{user_id}_messages.json"
        
        if not messages_file.exists():
            logger.warning(f"No mock data found for user {user_id}")
            return {}
        
        with open(messages_file) as f:
            all_messages = json.load(f)
        
        # Filter messages within date range
        messages = []
        for msg in all_messages:
            msg_time = datetime.fromtimestamp(float(msg['ts']))
            if start_date <= msg_time <= end_date:
                messages.append(msg)
        
        return self._aggregate_messages(messages)
    
    def _collect_api_data(self, user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Collect data from Slack API."""
        # Check cache first
        cache_key = f"{user_id}_{start_date.date()}_{end_date.date()}"
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists() and not self.config.get('_refresh_slack_cache', False):
            logger.info(f"Using cached data for {user_id}")
            with open(cache_file) as f:
                return json.load(f)
        
        try:
            # Get user's messages using conversations.history for each channel they're in
            # First, get channels the user is member of
            channels_response = requests.get(
                'https://slack.com/api/users.conversations',
                headers=self.headers,
                params={
                    'user': user_id,
                    'types': 'public_channel,private_channel',
                    'limit': 100
                }
            )
            
            if channels_response.status_code != 200 or not channels_response.json().get('ok'):
                logger.error(f"Failed to get channels for user {user_id}")
                return {}
            
            channels = channels_response.json().get('channels', [])
            all_messages = []
            
            # Collect messages from each channel
            for channel in channels[:20]:  # Limit to prevent rate limiting
                messages = self._get_channel_messages(
                    channel['id'], 
                    user_id,
                    int(start_date.timestamp()),
                    int(end_date.timestamp())
                )
                all_messages.extend(messages)
            
            # Also get DMs
            dm_messages = self._get_dm_messages(user_id, start_date, end_date)
            all_messages.extend(dm_messages)
            
            result = self._aggregate_messages(all_messages)
            
            # Cache the result
            with open(cache_file, 'w') as f:
                json.dump(result, f)
            
            return result
            
        except Exception as e:
            logger.error(f"Error collecting Slack data for {user_id}: {e}")
            return {}
    
    def _get_channel_messages(self, channel_id: str, user_id: str, start_ts: int, end_ts: int) -> List[Dict]:
        """Get messages from a specific channel for a user."""
        try:
            response = requests.get(
                'https://slack.com/api/conversations.history',
                headers=self.headers,
                params={
                    'channel': channel_id,
                    'oldest': start_ts,
                    'latest': end_ts,
                    'limit': 100
                }
            )
            
            if response.status_code == 200 and response.json().get('ok'):
                messages = response.json().get('messages', [])
                # Filter for user's messages
                return [msg for msg in messages if msg.get('user') == user_id]
            
        except Exception as e:
            logger.debug(f"Error getting messages from channel {channel_id}: {e}")
        
        return []
    
    def _get_dm_messages(self, user_id: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get direct messages for a user."""
        # This is simplified - in reality you'd need to enumerate DM conversations
        # and fetch history from each
        return []
    
    def _aggregate_messages(self, messages: List[Dict]) -> Dict[str, Any]:
        """Aggregate message statistics."""
        stats = {
            'total_messages': len(messages),
            'messages_by_hour': defaultdict(int),
            'messages_by_day': defaultdict(int),
            'channels_active': set(),
            'thread_messages': 0,
            'dm_messages': 0,
            'after_hours_messages': 0,
            'weekend_messages': 0,
            'response_times': [],
            'message_lengths': [],
            'emoji_reactions_given': 0,
            'emoji_reactions_received': 0,
            # Sentiment tracking
            'sentiment_scores': [],
            'negative_messages': 0,
            'positive_messages': 0,
            'neutral_messages': 0,
            'stress_indicators': 0,
            'sentiment_by_hour': defaultdict(list),
            'sentiment_by_day': defaultdict(list)
        }
        
        for msg in messages:
            # Parse timestamp
            ts = datetime.fromtimestamp(float(msg['ts']))
            hour = ts.hour
            day = ts.weekday()
            
            stats['messages_by_hour'][hour] += 1
            stats['messages_by_day'][day] += 1
            
            # Channel activity
            channel = msg.get('channel', '')
            if channel:
                stats['channels_active'].add(channel)
            
            # Thread participation
            if msg.get('thread_ts') and msg['thread_ts'] != msg['ts']:
                stats['thread_messages'] += 1
            
            # DM detection
            if channel.startswith('D'):
                stats['dm_messages'] += 1
            
            # After hours (before 9am or after 6pm)
            if hour < 9 or hour >= 18:
                stats['after_hours_messages'] += 1
            
            # Weekend
            if day >= 5:  # Saturday = 5, Sunday = 6
                stats['weekend_messages'] += 1
            
            # Message length and sentiment analysis
            text = msg.get('text', '')
            if text:
                stats['message_lengths'].append(len(text))
                
                # Perform sentiment analysis
                sentiment = self.sentiment_analyzer.polarity_scores(text)
                compound_score = sentiment['compound']
                stats['sentiment_scores'].append(compound_score)
                stats['sentiment_by_hour'][hour].append(compound_score)
                stats['sentiment_by_day'][day].append(compound_score)
                
                # Categorize sentiment
                if compound_score <= -0.05:
                    stats['negative_messages'] += 1
                elif compound_score >= 0.05:
                    stats['positive_messages'] += 1
                else:
                    stats['neutral_messages'] += 1
                
                # Check for stress indicators
                stress_keywords = [
                    'overwhelmed', 'exhausted', 'burned out', 'burnt out', 'swamped', 'drowning',
                    'stressed', 'urgent', 'asap', 'emergency', 'crisis', 'help', 'stuck',
                    'frustrated', 'tired', 'deadline', 'overloaded', 'pressure'
                ]
                
                text_lower = text.lower()
                if any(keyword in text_lower for keyword in stress_keywords):
                    stats['stress_indicators'] += 1
            
            # Reactions
            reactions = msg.get('reactions', [])
            stats['emoji_reactions_received'] += sum(r.get('count', 0) for r in reactions)
        
        # Convert sets to lists for JSON serialization
        stats['channels_active'] = list(stats['channels_active'])
        stats['messages_by_hour'] = dict(stats['messages_by_hour'])
        stats['messages_by_day'] = dict(stats['messages_by_day'])
        stats['sentiment_by_hour'] = dict(stats['sentiment_by_hour'])
        stats['sentiment_by_day'] = dict(stats['sentiment_by_day'])
        
        return stats
    
    def _calculate_metrics(self, stats: Dict[str, Any], days: int) -> Dict[str, Any]:
        """Calculate burnout-relevant metrics from raw statistics."""
        total_messages = stats.get('total_messages', 0)
        
        if total_messages == 0:
            return {
                'total_messages': 0,
                'messages_per_day': 0,
                'after_hours_percentage': 0,
                'weekend_percentage': 0,
                'channel_diversity': 0,
                'dm_ratio': 0,
                'thread_participation_rate': 0,
                'avg_message_length': 0,
                'peak_hour_concentration': 0,
                'response_pattern_score': 5.0,
                'avg_sentiment': 0.0,
                'negative_sentiment_ratio': 0.0,
                'positive_sentiment_ratio': 0.0,
                'stress_indicator_ratio': 0.0,
                'sentiment_volatility': 0.0
            }
        
        # Calculate sentiment metrics
        sentiment_scores = stats.get('sentiment_scores', [])
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
        sentiment_volatility = self._calculate_sentiment_volatility(sentiment_scores)
        
        metrics = {
            'total_messages': total_messages,
            'messages_per_day': total_messages / days,
            'after_hours_percentage': stats.get('after_hours_messages', 0) / total_messages,
            'weekend_percentage': stats.get('weekend_messages', 0) / total_messages,
            'channel_diversity': len(stats.get('channels_active', [])),
            'dm_ratio': stats.get('dm_messages', 0) / total_messages,
            'thread_participation_rate': stats.get('thread_messages', 0) / total_messages,
            'avg_message_length': sum(stats.get('message_lengths', [])) / len(stats.get('message_lengths', [1])),
            'peak_hour_concentration': self._calculate_peak_concentration(stats.get('messages_by_hour', {})),
            'response_pattern_score': self._calculate_response_pattern_score(stats),
            # Sentiment metrics
            'avg_sentiment': avg_sentiment,
            'negative_sentiment_ratio': stats.get('negative_messages', 0) / total_messages,
            'positive_sentiment_ratio': stats.get('positive_messages', 0) / total_messages,
            'stress_indicator_ratio': stats.get('stress_indicators', 0) / total_messages,
            'sentiment_volatility': sentiment_volatility
        }
        
        return metrics
    
    def _calculate_peak_concentration(self, hourly_messages: Dict[int, int]) -> float:
        """Calculate how concentrated messages are in peak hours."""
        if not hourly_messages:
            return 0.0
        
        total = sum(hourly_messages.values())
        if total == 0:
            return 0.0
        
        # Find top 3 hours
        sorted_hours = sorted(hourly_messages.items(), key=lambda x: x[1], reverse=True)
        top_3_total = sum(count for _, count in sorted_hours[:3])
        
        return top_3_total / total
    
    def _calculate_response_pattern_score(self, stats: Dict[str, Any]) -> float:
        """
        Calculate a score (0-10) for response patterns.
        Lower score = more concerning patterns.
        """
        score = 5.0  # Start neutral
        
        # Factors that decrease score (concerning)
        if stats.get('after_hours_messages', 0) > stats.get('total_messages', 1) * 0.3:
            score -= 2.0
        
        if stats.get('weekend_messages', 0) > stats.get('total_messages', 1) * 0.2:
            score -= 1.5
        
        # Very short messages might indicate stress
        avg_length = sum(stats.get('message_lengths', [50])) / len(stats.get('message_lengths', [1]))
        if avg_length < 20:
            score -= 1.0
        
        # High DM ratio might indicate escalations or private concerns
        dm_ratio = stats.get('dm_messages', 0) / max(stats.get('total_messages', 1), 1)
        if dm_ratio > 0.4:
            score -= 1.0
        
        # Factors that increase score (healthy)
        if stats.get('thread_messages', 0) > stats.get('total_messages', 1) * 0.3:
            score += 1.0  # Good thread participation
        
        if stats.get('emoji_reactions_given', 0) > 0:
            score += 0.5  # Engagement with others
        
        return max(0.0, min(10.0, score))
    
    def _calculate_sentiment_volatility(self, sentiment_scores: List[float]) -> float:
        """
        Calculate sentiment volatility (standard deviation).
        Higher volatility indicates emotional instability.
        """
        if len(sentiment_scores) < 2:
            return 0.0
            
        import statistics
        try:
            return statistics.stdev(sentiment_scores)
        except statistics.StatisticsError:
            return 0.0


def test_mock_collector():
    """Test the Slack collector with mock data."""
    # First generate some mock data
    from slack_mock_generator import SlackMockGenerator
    
    print("Generating mock Slack data...")
    generator = SlackMockGenerator()
    
    # Create test users with different risk levels
    generator.generate_user("alice@test.com", "Alice Chen", "healthy")
    generator.generate_user("bob@test.com", "Bob Smith", "moderate") 
    generator.generate_user("charlie@test.com", "Charlie Davis", "high")
    
    generator.save_mock_data()
    
    # Now test the collector
    config = {
        'slack_integration': {
            'mock_mode': True,
            'mock_data_dir': 'mock_slack_data'
        }
    }
    
    collector = SlackCollector(config=config)
    
    # Create user mappings (email -> Slack ID)
    user_mappings = {
        "alice@test.com": "U000ALI",
        "bob@test.com": "U001BOB", 
        "charlie@test.com": "U002CHA"
    }
    
    # Collect data
    print("\nCollecting Slack activity data...")
    slack_data = collector.collect_slack_data(user_mappings, days=30)
    
    # Display results
    print("\nSlack Activity Analysis:")
    print("-" * 50)
    
    for user_id, data in slack_data.items():
        metrics = data['metrics']
        print(f"\nUser: {data['email']}")
        print(f"  Total messages: {metrics['total_messages']}")
        print(f"  Messages/day: {metrics['messages_per_day']:.1f}")
        print(f"  After-hours: {metrics['after_hours_percentage']*100:.1f}%")
        print(f"  Weekend: {metrics['weekend_percentage']*100:.1f}%")
        print(f"  Channels active: {metrics['channel_diversity']}")
        print(f"  Response pattern score: {metrics['response_pattern_score']:.1f}/10")


if __name__ == "__main__":
    test_mock_collector()