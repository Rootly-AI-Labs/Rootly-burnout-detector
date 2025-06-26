"""
Slack communication pattern analyzer for burnout detection.
Analyzes Slack message patterns to identify burnout indicators.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import re
from collections import defaultdict
import statistics
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)


class SlackAnalyzer:
    """Analyzes Slack communication patterns for burnout indicators."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.slack_config = config.get('slack_integration', {})
        self.analysis_config = config.get('analysis', {})
        
        # Initialize VADER sentiment analyzer
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        
        # Burnout indicator weights for Slack data
        self.weights = {
            'emotional_exhaustion': 0.35,  # After-hours, message frequency, urgency
            'depersonalization': 0.30,     # Reduced collaboration, negative sentiment
            'personal_accomplishment': 0.35  # Response quality, helpfulness
        }
        
        # Stress/burnout keywords for sentiment analysis
        self.stress_keywords = {
            'high_stress': ['overwhelmed', 'exhausted', 'burned out', 'drowning', 'swamped', 
                           'can\'t keep up', 'too many', 'no time', 'urgent', 'fire', 'emergency'],
            'moderate_stress': ['busy', 'behind', 'catching up', 'pressure', 'stretched', 
                               'juggling', 'tight timeline', 'need help', 'struggling'],
            'negative_sentiment': ['sorry', 'failed', 'broken', 'down again', 'another', 
                                  'can\'t', 'won\'t', 'impossible', 'frustrated']
        }
        
        # Positive indicators
        self.positive_keywords = ['great', 'awesome', 'excellent', 'thanks', 'helpful', 
                                 'good work', 'nice', 'appreciate', 'well done', 'perfect']

    def analyze_user_slack_activity(self, slack_data: Dict[str, Any], days: int = 30) -> Dict[str, Any]:
        """
        Analyze a user's Slack activity for burnout indicators.
        
        Args:
            slack_data: User's Slack activity data from SlackCollector
            days: Analysis period in days
            
        Returns:
            Dict containing burnout analysis results
        """
        if not slack_data or not slack_data.get('metrics'):
            return self._create_empty_slack_analysis()
        
        metrics = slack_data['metrics']
        
        # Calculate the three Maslach dimensions for Slack data
        emotional_exhaustion = self._analyze_emotional_exhaustion(metrics, days)
        depersonalization = self._analyze_depersonalization(metrics, days)
        personal_accomplishment = self._analyze_personal_accomplishment(metrics, days)
        
        # Calculate overall Slack burnout score
        overall_score = (
            emotional_exhaustion['score'] * self.weights['emotional_exhaustion'] +
            depersonalization['score'] * self.weights['depersonalization'] +
            (10 - personal_accomplishment['score']) * self.weights['personal_accomplishment']
        )
        
        return {
            'overall_score': round(overall_score, 2),
            'emotional_exhaustion': emotional_exhaustion,
            'depersonalization': depersonalization,
            'personal_accomplishment': personal_accomplishment,
            'communication_health': self._assess_communication_health(metrics),
            'risk_factors': self._identify_slack_risk_factors(metrics),
            'recommendations': self._generate_slack_recommendations(overall_score, metrics)
        }

    def _analyze_emotional_exhaustion(self, metrics: Dict, days: int) -> Dict[str, Any]:
        """Analyze emotional exhaustion indicators from Slack data."""
        
        # Key indicators for emotional exhaustion
        total_messages = metrics.get('total_messages', 0)
        messages_per_day = metrics.get('messages_per_day', 0)
        after_hours_pct = metrics.get('after_hours_percentage', 0)
        weekend_pct = metrics.get('weekend_percentage', 0)
        peak_concentration = metrics.get('peak_hour_concentration', 0)
        
        # Sentiment indicators
        avg_sentiment = metrics.get('avg_sentiment', 0.0)
        negative_ratio = metrics.get('negative_sentiment_ratio', 0.0)
        stress_ratio = metrics.get('stress_indicator_ratio', 0.0)
        sentiment_volatility = metrics.get('sentiment_volatility', 0.0)
        
        # Scoring components (0-10 scale, higher = more exhausted)
        
        # 1. Message volume (high volume indicates overwork)
        if messages_per_day > 30:
            volume_score = 10
        elif messages_per_day > 20:
            volume_score = 7
        elif messages_per_day > 10:
            volume_score = 4
        else:
            volume_score = 1
        
        # 2. After-hours communication (boundary violations)
        after_hours_score = min(10, after_hours_pct * 25)  # 40% = score of 10
        
        # 3. Weekend work communication
        weekend_score = min(10, weekend_pct * 50)  # 20% = score of 10
        
        # 4. Peak hour concentration (indicates stress bursts)
        concentration_score = min(10, peak_concentration * 15)  # High concentration = stress
        
        # 5. Negative sentiment score (higher negative = more exhausted)
        sentiment_score = max(0, (-avg_sentiment + 1) * 5)  # Convert -1 to +1 range to 0-10
        
        # 6. Stress indicators
        stress_score = min(10, stress_ratio * 50)  # 20% stress indicators = score of 10
        
        # 7. Sentiment volatility (emotional instability)
        volatility_score = min(10, sentiment_volatility * 10)  # High volatility = stress
        
        # Combined emotional exhaustion score
        scores = [volume_score, after_hours_score, weekend_score, concentration_score, 
                 sentiment_score, stress_score, volatility_score]
        overall_score = statistics.mean(scores)
        
        return {
            'score': round(overall_score, 2),
            'indicators': {
                'messages_per_day': messages_per_day,
                'after_hours_percentage': round(after_hours_pct * 100, 1),
                'weekend_percentage': round(weekend_pct * 100, 1),
                'peak_concentration': round(peak_concentration, 2),
                'volume_score': round(volume_score, 1),
                'after_hours_score': round(after_hours_score, 1),
                'weekend_score': round(weekend_score, 1),
                'avg_sentiment': round(avg_sentiment, 2),
                'negative_sentiment_ratio': round(negative_ratio * 100, 1),
                'stress_indicator_ratio': round(stress_ratio * 100, 1),
                'sentiment_volatility': round(sentiment_volatility, 2),
                'sentiment_score': round(sentiment_score, 1),
                'stress_score': round(stress_score, 1),
                'volatility_score': round(volatility_score, 1)
            },
            'contributing_factors': self._identify_exhaustion_factors(
                volume_score, after_hours_score, weekend_score, concentration_score,
                sentiment_score, stress_score, volatility_score
            )
        }

    def _analyze_depersonalization(self, metrics: Dict, days: int) -> Dict[str, Any]:
        """Analyze depersonalization indicators from Slack data."""
        
        # Key indicators for depersonalization
        channel_diversity = metrics.get('channel_diversity', 0)
        dm_ratio = metrics.get('dm_ratio', 0)
        thread_participation = metrics.get('thread_participation_rate', 0)
        avg_message_length = metrics.get('avg_message_length', 0)
        
        # Sentiment indicators for depersonalization
        avg_sentiment = metrics.get('avg_sentiment', 0.0)
        negative_ratio = metrics.get('negative_sentiment_ratio', 0.0)
        
        # Scoring components (0-10 scale, higher = more depersonalized)
        
        # 1. Reduced collaboration (low thread participation)
        if thread_participation < 0.1:
            collaboration_score = 8
        elif thread_participation < 0.3:
            collaboration_score = 5
        elif thread_participation < 0.5:
            collaboration_score = 2
        else:
            collaboration_score = 0
        
        # 2. High DM ratio (avoiding public discussion)
        dm_score = min(10, dm_ratio * 20)  # 50% DMs = score of 10
        
        # 3. Context switching (too many channels)
        if channel_diversity > 15:
            context_score = 8
        elif channel_diversity > 10:
            context_score = 5
        elif channel_diversity > 5:
            context_score = 2
        else:
            context_score = 0
        
        # 4. Communication quality (very short messages indicate disengagement)
        if avg_message_length < 15:
            quality_score = 8
        elif avg_message_length < 30:
            quality_score = 4
        elif avg_message_length < 50:
            quality_score = 1
        else:
            quality_score = 0
        
        # 5. Negative sentiment (withdrawal and cynicism)
        negative_sentiment_score = min(10, negative_ratio * 25)  # 40% negative = score of 10
        
        # Combined depersonalization score
        scores = [collaboration_score, dm_score, context_score, quality_score, negative_sentiment_score]
        overall_score = statistics.mean(scores)
        
        return {
            'score': round(overall_score, 2),
            'indicators': {
                'thread_participation_rate': round(thread_participation, 2),
                'dm_ratio': round(dm_ratio, 2),
                'channel_diversity': channel_diversity,
                'avg_message_length': round(avg_message_length, 1),
                'collaboration_score': round(collaboration_score, 1),
                'dm_score': round(dm_score, 1),
                'context_switching_score': round(context_score, 1),
                'avg_sentiment': round(avg_sentiment, 2),
                'negative_sentiment_ratio': round(negative_ratio * 100, 1),
                'negative_sentiment_score': round(negative_sentiment_score, 1)
            },
            'contributing_factors': self._identify_depersonalization_factors(
                collaboration_score, dm_score, context_score, quality_score, negative_sentiment_score
            )
        }

    def _analyze_personal_accomplishment(self, metrics: Dict, days: int) -> Dict[str, Any]:
        """Analyze personal accomplishment indicators from Slack data."""
        
        # Key indicators for personal accomplishment (higher = better)
        response_pattern_score = metrics.get('response_pattern_score', 5)
        total_messages = metrics.get('total_messages', 0)
        messages_per_day = metrics.get('messages_per_day', 0)
        thread_participation = metrics.get('thread_participation_rate', 0)
        
        # Sentiment indicators for personal accomplishment
        avg_sentiment = metrics.get('avg_sentiment', 0.0)
        positive_ratio = metrics.get('positive_sentiment_ratio', 0.0)
        
        # Scoring components (0-10 scale, higher = better accomplishment)
        
        # 1. Healthy communication patterns
        pattern_score = response_pattern_score  # Already 0-10 scale
        
        # 2. Appropriate activity level (not too low, not too high)
        if 5 <= messages_per_day <= 15:
            activity_score = 8  # Sweet spot
        elif 3 <= messages_per_day <= 20:
            activity_score = 6  # Acceptable
        elif messages_per_day > 0:
            activity_score = 3  # Too low or too high
        else:
            activity_score = 0  # No activity
        
        # 3. Collaborative engagement
        if thread_participation > 0.5:
            engagement_score = 8
        elif thread_participation > 0.3:
            engagement_score = 6
        elif thread_participation > 0.1:
            engagement_score = 3
        else:
            engagement_score = 1
        
        # 4. Consistent presence (having some activity is good)
        if total_messages > 0:
            presence_score = min(8, total_messages / days * 2)  # Scale based on consistency
        else:
            presence_score = 0
        
        # 5. Positive communication sentiment (indicates satisfaction)
        positive_sentiment_score = min(10, (avg_sentiment + 1) * 5)  # Convert -1 to +1 range to 0-10
        
        # Combined personal accomplishment score
        scores = [pattern_score, activity_score, engagement_score, presence_score, positive_sentiment_score]
        overall_score = statistics.mean(scores)
        
        return {
            'score': round(overall_score, 2),
            'indicators': {
                'response_pattern_score': round(response_pattern_score, 2),
                'healthy_activity_level': round(activity_score, 1),
                'collaborative_engagement': round(engagement_score, 1),
                'consistent_presence': round(presence_score, 1),
                'positive_sentiment_score': round(positive_sentiment_score, 1),
                'avg_sentiment': round(avg_sentiment, 2),
                'positive_sentiment_ratio': round(positive_ratio * 100, 1),
                'total_messages': total_messages
            },
            'contributing_factors': self._identify_accomplishment_factors(
                pattern_score, activity_score, engagement_score, presence_score, positive_sentiment_score
            )
        }

    def _assess_communication_health(self, metrics: Dict) -> Dict[str, Any]:
        """Assess overall communication health indicators."""
        
        messages_per_day = metrics.get('messages_per_day', 0)
        after_hours_pct = metrics.get('after_hours_percentage', 0)
        weekend_pct = metrics.get('weekend_percentage', 0)
        thread_participation = metrics.get('thread_participation_rate', 0)
        
        # Overall health assessment
        health_factors = []
        
        # Work-life balance
        if after_hours_pct < 0.1 and weekend_pct < 0.05:
            health_factors.append("Excellent work-life boundaries")
        elif after_hours_pct < 0.2 and weekend_pct < 0.1:
            health_factors.append("Good work-life balance")
        else:
            health_factors.append("Poor work-life boundaries")
        
        # Communication volume
        if 5 <= messages_per_day <= 15:
            health_factors.append("Healthy communication volume")
        elif messages_per_day < 3:
            health_factors.append("Low communication activity")
        else:
            health_factors.append("High communication volume")
        
        # Collaboration
        if thread_participation > 0.4:
            health_factors.append("Strong collaborative engagement")
        elif thread_participation > 0.2:
            health_factors.append("Moderate collaboration")
        else:
            health_factors.append("Limited collaborative participation")
        
        # Overall health score (0-10)
        health_score = 10
        if after_hours_pct > 0.3: health_score -= 3
        if weekend_pct > 0.2: health_score -= 2
        if messages_per_day > 25: health_score -= 2
        if thread_participation < 0.2: health_score -= 2
        
        health_score = max(0, health_score)
        
        return {
            'health_score': health_score,
            'assessment': health_factors,
            'work_life_balance': 'Poor' if (after_hours_pct > 0.3 or weekend_pct > 0.2) else 'Good',
            'communication_pattern': 'Healthy' if 5 <= messages_per_day <= 15 else 'Concerning'
        }

    def _identify_slack_risk_factors(self, metrics: Dict) -> List[str]:
        """Identify specific risk factors from Slack communication patterns."""
        
        risk_factors = []
        
        messages_per_day = metrics.get('messages_per_day', 0)
        after_hours_pct = metrics.get('after_hours_percentage', 0)
        weekend_pct = metrics.get('weekend_percentage', 0)
        dm_ratio = metrics.get('dm_ratio', 0)
        thread_participation = metrics.get('thread_participation_rate', 0)
        channel_diversity = metrics.get('channel_diversity', 0)
        
        # High-volume communication
        if messages_per_day > 25:
            risk_factors.append("Excessive message volume indicating overwork")
        
        # Poor work-life boundaries
        if after_hours_pct > 0.3:
            risk_factors.append("High after-hours communication (>30%)")
        
        if weekend_pct > 0.2:
            risk_factors.append("Significant weekend work communication")
        
        # Social withdrawal indicators
        if dm_ratio > 0.4:
            risk_factors.append("High private message ratio - avoiding public channels")
        
        if thread_participation < 0.2:
            risk_factors.append("Low thread participation - reduced collaboration")
        
        # Context switching stress
        if channel_diversity > 12:
            risk_factors.append("High channel diversity indicating scattered focus")
        
        # Communication quality concerns
        avg_length = metrics.get('avg_message_length', 0)
        if avg_length < 20:
            risk_factors.append("Very short messages indicating stress or disengagement")
        
        return risk_factors

    def _generate_slack_recommendations(self, overall_score: float, metrics: Dict) -> List[str]:
        """Generate specific recommendations based on Slack analysis."""
        
        recommendations = []
        
        messages_per_day = metrics.get('messages_per_day', 0)
        after_hours_pct = metrics.get('after_hours_percentage', 0)
        weekend_pct = metrics.get('weekend_percentage', 0)
        thread_participation = metrics.get('thread_participation_rate', 0)
        
        # High-risk recommendations
        if overall_score >= 7:
            recommendations.append("🚨 High Slack burnout indicators detected - immediate intervention recommended")
            
            if after_hours_pct > 0.3:
                recommendations.append("Set strict boundaries for after-hours Slack usage")
            
            if messages_per_day > 25:
                recommendations.append("Reduce communication load - delegate or batch messages")
            
            if weekend_pct > 0.2:
                recommendations.append("Implement 'Slack-free weekends' policy")
        
        # Moderate-risk recommendations
        elif overall_score >= 4:
            recommendations.append("⚠️ Moderate Slack stress indicators - monitor and adjust")
            
            if after_hours_pct > 0.2:
                recommendations.append("Reduce after-hours Slack engagement")
            
            if thread_participation < 0.3:
                recommendations.append("Encourage more collaborative discussion participation")
        
        # General recommendations
        else:
            recommendations.append("✅ Healthy Slack communication patterns")
            
            if thread_participation > 0.5:
                recommendations.append("Excellent collaborative engagement - keep it up!")
        
        # Specific pattern recommendations
        if metrics.get('dm_ratio', 0) > 0.4:
            recommendations.append("Move more discussions to public channels for team visibility")
        
        if metrics.get('channel_diversity', 0) > 12:
            recommendations.append("Focus on fewer channels to reduce context switching")
        
        return recommendations

    def _identify_exhaustion_factors(self, volume: float, after_hours: float, 
                                   weekend: float, concentration: float,
                                   sentiment: float = 0, stress: float = 0, 
                                   volatility: float = 0) -> List[str]:
        """Identify specific exhaustion factors."""
        factors = []
        if volume >= 7: factors.append("High message volume")
        if after_hours >= 6: factors.append("Excessive after-hours communication")
        if weekend >= 6: factors.append("Weekend work communication")
        if concentration >= 6: factors.append("High-stress communication bursts")
        if sentiment >= 6: factors.append("Negative communication sentiment")
        if stress >= 6: factors.append("High stress language indicators")
        if volatility >= 6: factors.append("Emotional volatility in communication")
        return factors

    def _identify_depersonalization_factors(self, collaboration: float, dm: float, 
                                          context: float, quality: float, 
                                          negative_sentiment: float = 0) -> List[str]:
        """Identify specific depersonalization factors."""
        factors = []
        if collaboration >= 6: factors.append("Reduced collaborative participation")
        if dm >= 6: factors.append("High private message usage")
        if context >= 6: factors.append("Excessive context switching")
        if quality >= 6: factors.append("Declining communication quality")
        if negative_sentiment >= 6: factors.append("Negative communication sentiment")
        return factors

    def _identify_accomplishment_factors(self, pattern: float, activity: float, 
                                       engagement: float, presence: float,
                                       positive_sentiment: float = 5) -> List[str]:
        """Identify factors affecting personal accomplishment."""
        factors = []
        if pattern <= 3: factors.append("Poor communication response patterns")
        if activity <= 3: factors.append("Suboptimal activity levels")
        if engagement <= 3: factors.append("Low collaborative engagement")
        if presence <= 3: factors.append("Inconsistent communication presence")
        if positive_sentiment <= 3: factors.append("Low positive communication sentiment")
        return factors

    def _create_empty_slack_analysis(self) -> Dict[str, Any]:
        """Create empty analysis for users with no Slack data."""
        return {
            'overall_score': 0,
            'emotional_exhaustion': {'score': 0, 'indicators': {}, 'contributing_factors': []},
            'depersonalization': {'score': 0, 'indicators': {}, 'contributing_factors': []},
            'personal_accomplishment': {'score': 5, 'indicators': {}, 'contributing_factors': []},
            'communication_health': {
                'health_score': 5,
                'assessment': ['No Slack data available'],
                'work_life_balance': 'Unknown',
                'communication_pattern': 'Unknown'
            },
            'risk_factors': ['No Slack communication data available'],
            'recommendations': ['Enable Slack integration to analyze communication patterns']
        }


def analyze_slack_sentiment(message_text: str) -> Dict[str, Any]:
    """
    Analyze sentiment and stress indicators in a Slack message.
    This is a helper function for more detailed message analysis.
    """
    text_lower = message_text.lower()
    
    # Stress indicators
    stress_keywords = ['overwhelmed', 'exhausted', 'burned out', 'drowning', 'swamped', 
                      'urgent', 'fire', 'emergency', 'can\'t keep up', 'too many']
    
    positive_keywords = ['great', 'awesome', 'excellent', 'thanks', 'helpful', 
                        'good work', 'appreciate', 'well done']
    
    stress_count = sum(1 for keyword in stress_keywords if keyword in text_lower)
    positive_count = sum(1 for keyword in positive_keywords if keyword in text_lower)
    
    # Time indicators
    time_indicators = ['late', 'early', 'weekend', 'night', 'am', 'pm']
    has_time_ref = any(indicator in text_lower for indicator in time_indicators)
    
    # Length and urgency
    is_short = len(message_text) < 30
    has_urgency = any(word in text_lower for word in ['urgent', 'asap', 'now', 'immediately'])
    
    return {
        'stress_score': stress_count,
        'positive_score': positive_count,
        'has_time_reference': has_time_ref,
        'is_short_message': is_short,
        'has_urgency_indicators': has_urgency,
        'overall_sentiment': 'negative' if stress_count > positive_count else 
                           'positive' if positive_count > 0 else 'neutral'
    }