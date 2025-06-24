"""
Custom smolagents tools for burnout analysis data access.
"""

from typing import Any, Dict, List, Optional
from smolagents import Tool
import json


class BurnoutDataTool(Tool):
    name = "burnout_data"
    description = "Get burnout analysis data for users, including risk scores and detailed metrics"
    inputs = {
        "query": {
            "type": "string", 
            "description": "Query to search burnout data (e.g., 'high risk users', 'user John Smith', 'statistics')",
            "nullable": True
        }
    }
    output_type = "string"
    
    def __init__(self, analysis_results: Dict[str, Any]):
        super().__init__()
        self.results = analysis_results
    
    def forward(self, query: str = "") -> str:
        """Return burnout analysis data based on query."""
        try:
            if not query or query.lower() in ["all", "summary"]:
                return self._get_summary()
            elif "high risk" in query.lower() or "high-risk" in query.lower():
                return self._get_high_risk_users()
            elif ("medium risk" in query.lower() or "medium-risk" in query.lower() or 
                  ("medium" in query.lower() and "risk" in query.lower())):
                return self._get_medium_risk_users()
            elif ("low risk" in query.lower() or "low-risk" in query.lower() or
                  ("low" in query.lower() and "risk" in query.lower())):
                return self._get_low_risk_users()
            elif "user" in query.lower():
                return self._search_users(query)
            elif "stats" in query.lower() or "statistics" in query.lower():
                return self._get_statistics()
            else:
                return self._search_general(query)
        except Exception as e:
            return f"Error accessing burnout data: {str(e)}"
    
    def _get_summary(self) -> str:
        """Get overall analysis summary."""
        individual = self.results.get("individual_analyses", [])
        if not individual:
            return "No burnout analysis data available."
        
        high_count = sum(1 for a in individual if a.get("risk_level") == "high")
        medium_count = sum(1 for a in individual if a.get("risk_level") == "medium")
        low_count = sum(1 for a in individual if a.get("risk_level") == "low")
        
        scores = [a.get("burnout_score", 0) for a in individual]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        metadata = self.results.get("metadata", {})
        
        return f"""Burnout Analysis Summary:
- Total users analyzed: {len(individual)}
- Analysis period: {metadata.get('days_analyzed', 'N/A')} days
- High risk users: {high_count}
- Medium risk users: {medium_count}
- Low risk users: {low_count}
- Average burnout score: {avg_score:.2f}/10
- Total incidents: {metadata.get('total_incidents', 'N/A')}"""
    
    def _get_high_risk_users(self) -> str:
        """Get details of high-risk users."""
        individual = self.results.get("individual_analyses", [])
        high_risk = [a for a in individual if a.get("risk_level") == "high"]
        
        if not high_risk:
            return "No high-risk users found."
        
        result = "High Risk Users:\n"
        for user in high_risk:
            key_metrics = user.get('key_metrics', {})
            result += f"\n- {user.get('user_name', 'Unknown')} (Score: {user.get('burnout_score', 0)}/10)\n"
            result += f"  Incidents: {key_metrics.get('total_incidents', 0)}\n"
            result += f"  After-hours %: {key_metrics.get('after_hours_incidents', 0) / max(key_metrics.get('total_incidents', 1), 1) * 100:.1f}%\n"
            
            recommendations = user.get("recommendations", [])[:2]
            if recommendations:
                result += f"  Top recommendations: {', '.join(recommendations)}\n"
        
        return result
    
    def _get_medium_risk_users(self) -> str:
        """Get details of medium-risk users."""
        individual = self.results.get("individual_analyses", [])
        medium_risk = [a for a in individual if a.get("risk_level") == "medium"]
        
        if not medium_risk:
            return "No medium-risk users found."
        
        result = "Medium Risk Users:\n"
        for user in medium_risk:
            key_metrics = user.get('key_metrics', {})
            result += f"\n- {user.get('user_name', 'Unknown')} (Score: {user.get('burnout_score', 0)}/10)\n"
            result += f"  Incidents: {key_metrics.get('total_incidents', 0)}\n"
            result += f"  After-hours %: {key_metrics.get('after_hours_incidents', 0) / max(key_metrics.get('total_incidents', 1), 1) * 100:.1f}%\n"
            
            recommendations = user.get("recommendations", [])[:2]
            if recommendations:
                result += f"  Top recommendations: {', '.join(recommendations)}\n"
        
        return result
    
    def _get_low_risk_users(self) -> str:
        """Get details of low-risk users."""
        individual = self.results.get("individual_analyses", [])
        low_risk = [a for a in individual if a.get("risk_level") == "low"]
        
        if not low_risk:
            return "No low-risk users found."
        
        # Only show first 10 to avoid overwhelming output
        result = f"Low Risk Users (showing first 10 of {len(low_risk)}):\n"
        for user in low_risk[:10]:
            key_metrics = user.get('key_metrics', {})
            result += f"\n- {user.get('user_name', 'Unknown')} (Score: {user.get('burnout_score', 0)}/10)\n"
            result += f"  Incidents: {key_metrics.get('total_incidents', 0)}\n"
            result += f"  After-hours %: {key_metrics.get('after_hours_incidents', 0) / max(key_metrics.get('total_incidents', 1), 1) * 100:.1f}%\n"
        
        if len(low_risk) > 10:
            result += f"\n... and {len(low_risk) - 10} more low-risk users."
        
        return result
    
    def _search_users(self, query: str) -> str:
        """Search for specific users in the analysis."""
        individual = self.results.get("individual_analyses", [])
        query_lower = query.lower()
        
        # Extract potential user name from query
        words = query_lower.split()
        user_names = []
        for word in words:
            if len(word) > 2 and word not in ["user", "for", "about", "show", "get"]:
                user_names.append(word)
        
        matching_users = []
        for analysis in individual:
            user_name = analysis.get("user_name", "").lower()
            if any(name in user_name for name in user_names):
                matching_users.append(analysis)
        
        if not matching_users:
            return f"No users found matching query: {query}"
        
        result = f"Found {len(matching_users)} matching user(s):\n"
        for user in matching_users:
            key_metrics = user.get('key_metrics', {})
            result += f"\n{user.get('user_name', 'Unknown')}:\n"
            result += f"  Risk Level: {user.get('risk_level', 'unknown')}\n"
            result += f"  Burnout Score: {user.get('burnout_score', 0)}/10\n"
            result += f"  Total Incidents: {key_metrics.get('total_incidents', 0)}\n"
            result += f"  After Hours %: {key_metrics.get('after_hours_incidents', 0) / max(key_metrics.get('total_incidents', 1), 1) * 100:.1f}%\n"
            result += f"  Avg Resolution Time: {key_metrics.get('avg_resolution_time_hours', 0):.1f} hours\n"
        
        return result
    
    def _get_statistics(self) -> str:
        """Get detailed statistics."""
        individual = self.results.get("individual_analyses", [])
        if not individual:
            return "No statistical data available."
        
        scores = [a.get("burnout_score", 0) for a in individual]
        incidents = [a.get("total_incidents", 0) for a in individual]
        after_hours = [a.get("after_hours_percentage", 0) for a in individual]
        
        return f"""Detailed Statistics:
- Burnout Scores: min={min(scores):.1f}, max={max(scores):.1f}, avg={sum(scores)/len(scores):.1f}
- Incidents per user: min={min(incidents)}, max={max(incidents)}, avg={sum(incidents)/len(incidents):.1f}
- After-hours %: min={min(after_hours)*100:.1f}%, max={max(after_hours)*100:.1f}%, avg={sum(after_hours)/len(after_hours)*100:.1f}%
- Users by risk level: {self._get_risk_distribution()}"""
    
    def _get_risk_distribution(self) -> str:
        """Get risk level distribution."""
        individual = self.results.get("individual_analyses", [])
        high = sum(1 for a in individual if a.get("risk_level") == "high")
        medium = sum(1 for a in individual if a.get("risk_level") == "medium")
        low = sum(1 for a in individual if a.get("risk_level") == "low")
        return f"High={high}, Medium={medium}, Low={low}"
    
    def _search_general(self, query: str) -> str:
        """Handle general queries about the data."""
        return f"I can help with burnout analysis data. Try asking about:\n- 'summary' or 'all' for overview\n- 'high risk' for high-risk users\n- 'medium risk' for medium-risk users\n- 'low risk' for low-risk users\n- 'user [name]' for specific users\n- 'statistics' for detailed stats\n\nYour query: '{query}'"


class TrendAnalysisTool(Tool):
    name = "trend_analysis"
    description = "Analyze trends and patterns in burnout data over time"
    inputs = {
        "query": {
            "type": "string",
            "description": "Query about trends (e.g., 'incident patterns', 'risk factors', 'team patterns')",
            "nullable": True
        }
    }
    output_type = "string"
    
    def __init__(self, analysis_results: Dict[str, Any]):
        super().__init__()
        self.results = analysis_results
    
    def forward(self, query: str = "") -> str:
        """Analyze trends based on query."""
        try:
            individual = self.results.get("individual_analyses", [])
            if not individual:
                return "No trend data available."
            
            if "correlation" in query.lower():
                return self._analyze_correlations()
            elif "pattern" in query.lower():
                return self._identify_patterns()
            elif "risk factor" in query.lower():
                return self._analyze_risk_factors()
            else:
                return self._general_trends()
        except Exception as e:
            return f"Error analyzing trends: {str(e)}"
    
    def _analyze_correlations(self) -> str:
        """Analyze correlations between different metrics."""
        individual = self.results.get("individual_analyses", [])
        
        # Simple correlation analysis
        high_risk_users = [a for a in individual if a.get("risk_level") == "high"]
        
        if not high_risk_users:
            return "No high-risk users to analyze correlations."
        
        avg_incidents = sum(u.get("total_incidents", 0) for u in high_risk_users) / len(high_risk_users)
        avg_after_hours = sum(u.get("after_hours_percentage", 0) for u in high_risk_users) / len(high_risk_users)
        avg_resolution = sum(u.get("avg_resolution_time_hours", 0) for u in high_risk_users) / len(high_risk_users)
        
        return f"""Correlation Analysis (High-Risk Users):
- Average incidents: {avg_incidents:.1f}
- Average after-hours work: {avg_after_hours*100:.1f}%
- Average resolution time: {avg_resolution:.1f} hours

High-risk users tend to have more incidents and longer resolution times."""
    
    def _identify_patterns(self) -> str:
        """Identify common patterns in the data."""
        individual = self.results.get("individual_analyses", [])
        
        # Analyze patterns by risk level
        patterns = {}
        for level in ["high", "medium", "low"]:
            users_at_level = [a for a in individual if a.get("risk_level") == level]
            if users_at_level:
                avg_incidents = sum(u.get("total_incidents", 0) for u in users_at_level) / len(users_at_level)
                avg_after_hours = sum(u.get("after_hours_percentage", 0) for u in users_at_level) / len(users_at_level)
                patterns[level] = {
                    "count": len(users_at_level),
                    "avg_incidents": avg_incidents,
                    "avg_after_hours": avg_after_hours
                }
        
        result = "Burnout Patterns by Risk Level:\n"
        for level, data in patterns.items():
            result += f"\n{level.upper()} Risk ({data['count']} users):\n"
            result += f"  - Avg incidents: {data['avg_incidents']:.1f}\n"
            result += f"  - Avg after-hours: {data['avg_after_hours']*100:.1f}%\n"
        
        return result
    
    def _analyze_risk_factors(self) -> str:
        """Analyze what factors contribute most to burnout risk."""
        individual = self.results.get("individual_analyses", [])
        high_risk = [a for a in individual if a.get("risk_level") == "high"]
        
        if not high_risk:
            return "No high-risk users to analyze risk factors."
        
        # Analyze common characteristics
        total_users = len(individual)
        high_risk_count = len(high_risk)
        
        # Calculate thresholds that separate high-risk users
        all_incidents = [a.get("total_incidents", 0) for a in individual]
        all_after_hours = [a.get("after_hours_percentage", 0) for a in individual]
        
        high_incidents = [a.get("total_incidents", 0) for a in high_risk]
        high_after_hours = [a.get("after_hours_percentage", 0) for a in high_risk]
        
        return f"""Risk Factor Analysis:
- {high_risk_count}/{total_users} users are high-risk ({high_risk_count/total_users*100:.1f}%)

Key Risk Factors:
- High incident volume: {sum(high_incidents)/len(high_incidents):.1f} avg vs {sum(all_incidents)/len(all_incidents):.1f} overall
- Excessive after-hours work: {sum(high_after_hours)/len(high_after_hours)*100:.1f}% avg vs {sum(all_after_hours)/len(all_after_hours)*100:.1f}% overall

Users with >10 incidents or >30% after-hours work are at highest risk."""
    
    def _general_trends(self) -> str:
        """Provide general trend overview."""
        return """General Trend Analysis:
Ask me about:
- 'correlation' - relationships between metrics
- 'patterns' - common characteristics by risk level  
- 'risk factors' - what drives high burnout risk

Current data shows incident volume and after-hours work are key burnout drivers."""


class RecommendationTool(Tool):
    name = "recommendations"
    description = "Generate actionable recommendations for reducing burnout risk"
    inputs = {
        "query": {
            "type": "string",
            "description": "Query for recommendations (e.g., 'high risk users', 'team level', 'preventive measures')",
            "nullable": True
        }
    }
    output_type = "string"
    
    def __init__(self, analysis_results: Dict[str, Any]):
        super().__init__()
        self.results = analysis_results
    
    def forward(self, query: str = "") -> str:
        """Generate recommendations based on query."""
        try:
            if "user" in query.lower():
                return self._user_recommendations(query)
            elif "team" in query.lower():
                return self._team_recommendations()
            elif "immediate" in query.lower() or "urgent" in query.lower():
                return self._immediate_actions()
            else:
                return self._general_recommendations()
        except Exception as e:
            return f"Error generating recommendations: {str(e)}"
    
    def _user_recommendations(self, query: str) -> str:
        """Get recommendations for specific users."""
        individual = self.results.get("individual_analyses", [])
        high_risk = [a for a in individual if a.get("risk_level") == "high"]
        
        if not high_risk:
            return "No high-risk users requiring immediate recommendations."
        
        result = "User-Specific Recommendations:\n"
        for user in high_risk[:3]:  # Top 3 high-risk users
            result += f"\n{user.get('user_name', 'Unknown')} (Score: {user.get('burnout_score')}/10):\n"
            recommendations = user.get("recommendations", [])
            for i, rec in enumerate(recommendations[:3], 1):
                result += f"  {i}. {rec}\n"
        
        return result
    
    def _team_recommendations(self) -> str:
        """Get team-level recommendations."""
        individual = self.results.get("individual_analyses", [])
        high_count = sum(1 for a in individual if a.get("risk_level") == "high")
        total_count = len(individual)
        
        if high_count / total_count > 0.3:  # >30% high risk
            priority = "CRITICAL"
        elif high_count / total_count > 0.15:  # >15% high risk
            priority = "HIGH"
        else:
            priority = "MEDIUM"
        
        return f"""Team-Level Recommendations ({priority} Priority):

Immediate Actions:
1. Review on-call rotation - {high_count}/{total_count} users at high risk
2. Implement incident response load balancing
3. Establish after-hours coverage limits (max 30% of incidents)

Medium-term:
1. Cross-train team members to distribute expertise
2. Automate common incident responses
3. Improve monitoring to catch issues earlier

Long-term:
1. Invest in system reliability to reduce incident volume
2. Create incident response playbooks
3. Regular burnout risk assessment (monthly)"""
    
    def _immediate_actions(self) -> str:
        """Get immediate/urgent actions needed."""
        individual = self.results.get("individual_analyses", [])
        critical_users = [a for a in individual 
                         if a.get("burnout_score", 0) >= 8]  # Score 8+ is critical
        
        if not critical_users:
            return "No users requiring immediate intervention."
        
        result = f"IMMEDIATE ACTIONS REQUIRED - {len(critical_users)} users at critical risk:\n"
        for user in critical_users:
            result += f"\n• {user.get('user_name', 'Unknown')} (Score: {user.get('burnout_score')}/10)\n"
            result += f"  - Reduce on-call load immediately\n"
            result += f"  - Manager check-in within 24 hours\n"
            result += f"  - Consider temporary rotation off high-severity incidents\n"
        
        return result
    
    def _general_recommendations(self) -> str:
        """Get general recommendations."""
        return """General Burnout Prevention Recommendations:

Prevention:
- Limit after-hours work to <20% of total incidents
- Rotate high-severity incident assignments
- Ensure adequate recovery time between major incidents

Monitoring:
- Track individual incident loads weekly
- Monitor after-hours response patterns
- Regular team burnout surveys

Support:
- Provide mental health resources
- Offer flexible work arrangements
- Recognize and reward incident response efforts

Ask for 'user', 'team', or 'immediate' recommendations for specific guidance."""