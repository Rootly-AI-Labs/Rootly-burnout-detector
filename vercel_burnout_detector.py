#!/usr/bin/env python3
"""
Vercel-Compatible Burnout Detector
Uses direct HTTP calls to Rootly's hosted MCP server instead of stdio_client.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path
import httpx

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import main modules
from burnout_analyzer import BurnoutAnalyzer


class VercelBurnoutDetector:
    """
    Burnout detector optimized for Vercel serverless functions.
    Connects directly to Rootly's hosted MCP server via HTTP.
    """
    
    def __init__(self, config=None):
        self.mcp_base_url = "https://mcp.rootly.com"
        self.api_token = os.getenv("ROOTLY_API_TOKEN")
        if not self.api_token:
            raise ValueError("ROOTLY_API_TOKEN environment variable is required")
        
        # Default config for Vercel environment
        self.config = config or {
            "analysis": {
                "days_to_analyze": 30,
                "business_hours": {"start": 9, "end": 17},
                "severity_weights": {"sev1": 3.0, "sev2": 2.0, "sev3": 1.5, "sev4": 1.0}
            },
            "burnout_thresholds": {
                "incidents_per_week_high": 10,
                "incidents_per_week_medium": 6,
                "after_hours_percentage_high": 0.3,
                "after_hours_percentage_medium": 0.15,
                "avg_resolution_time_hours_high": 4,
                "avg_resolution_time_hours_medium": 2,
                "escalation_rate_high": 0.4,
                "escalation_rate_medium": 0.2
            },
            "scoring": {
                "emotional_exhaustion_weight": 0.4,
                "depersonalization_weight": 0.3,
                "personal_accomplishment_weight": 0.3,
                "max_score": 10.0
            }
        }
        
        self.analyzer = BurnoutAnalyzer(self.config)
    
    async def get_rootly_data(self):
        """Get data from Rootly's hosted MCP server via HTTP."""
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Call users_get tool
                users_response = await client.post(
                    f"{self.mcp_base_url}/tools/call",
                    headers=headers,
                    json={
                        "name": "users_get",
                        "arguments": {}
                    }
                )
                users_response.raise_for_status()
                
                # Call incidents_get tool
                incidents_response = await client.post(
                    f"{self.mcp_base_url}/tools/call",
                    headers=headers,
                    json={
                        "name": "incidents_get", 
                        "arguments": {}
                    }
                )
                incidents_response.raise_for_status()
                
                # Parse responses
                users_data = users_response.json()
                incidents_data = incidents_response.json()
                
                # Extract the actual data from MCP response format
                users = self._extract_mcp_data(users_data)
                incidents = self._extract_mcp_data(incidents_data)
                
                return users, incidents
                
            except httpx.HTTPStatusError as e:
                raise Exception(f"HTTP error calling Rootly MCP server: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                raise Exception(f"Error connecting to Rootly MCP server: {str(e)}")
    
    def _extract_mcp_data(self, mcp_response):
        """Extract data from MCP response format."""
        if isinstance(mcp_response, dict):
            # Handle different possible MCP response formats
            if "content" in mcp_response and isinstance(mcp_response["content"], list):
                # Format: {"content": [{"text": "..."}]}
                if mcp_response["content"] and "text" in mcp_response["content"][0]:
                    data = json.loads(mcp_response["content"][0]["text"])
                    return data.get("data", data)
            elif "data" in mcp_response:
                # Format: {"data": [...]}
                return mcp_response["data"]
            elif "result" in mcp_response:
                # Format: {"result": {...}}
                result = mcp_response["result"]
                if isinstance(result, dict) and "data" in result:
                    return result["data"]
                return result
        
        # Fallback - return as is
        return mcp_response
    
    def analyze_burnout(self, users, incidents, days=30):
        """Analyze burnout risk using the sophisticated BurnoutAnalyzer."""
        # Process raw data into the format expected by our analyzer
        processed_users = self._process_users(users)
        processed_incidents = self._process_incidents(incidents)
        user_incident_mapping = self._map_users_to_incidents(processed_users, processed_incidents)
        
        # Filter recent incidents
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_incidents = []
        for incident in processed_incidents:
            created_at = incident.get("created_at")
            if created_at:
                try:
                    incident_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    if incident_date >= cutoff_date:
                        recent_incidents.append(incident)
                except:
                    continue
        
        # Run comprehensive analysis for each user
        results = []
        for user in processed_users:
            user_id = user["id"]
            user_incidents = user_incident_mapping.get(user_id, [])
            
            # Filter to recent incident IDs only
            recent_incident_ids = [inc["id"] for inc in recent_incidents]
            user_recent_incidents = [inc_id for inc_id in user_incidents if inc_id in recent_incident_ids]
            
            analysis = self.analyzer.analyze_user_burnout(
                user, user_recent_incidents, recent_incidents
            )
            results.append(analysis)
        
        return results
    
    def _process_users(self, users):
        """Process raw user data into expected format."""
        processed = []
        for user in users:
            attrs = user.get("attributes", {})
            processed_user = {
                "id": user.get("id"),
                "name": attrs.get("full_name", attrs.get("name", "Unknown")),
                "email": attrs.get("email"),
                "timezone": attrs.get("time_zone", "UTC"),
                "first_name": attrs.get("first_name"),
                "last_name": attrs.get("last_name"),
                "slack_id": attrs.get("slack_id"),
                "created_at": attrs.get("created_at"),
                "updated_at": attrs.get("updated_at")
            }
            processed.append(processed_user)
        return processed
    
    def _process_incidents(self, incidents):
        """Process raw incident data into expected format."""
        processed = []
        for incident in incidents:
            attrs = incident.get("attributes", {})
            
            # Extract severity information
            severity_info = attrs.get("severity", {})
            if isinstance(severity_info, dict) and "data" in severity_info:
                severity_data = severity_info["data"]
                severity_name = severity_data.get("attributes", {}).get("name", "Unknown")
                severity_level = severity_data.get("attributes", {}).get("severity", "low")
            else:
                severity_name = "Unknown"
                severity_level = "low"
            
            processed_incident = {
                "id": incident.get("id"),
                "title": attrs.get("title"),
                "summary": attrs.get("summary"),
                "status": attrs.get("status"),
                "severity_name": severity_name,
                "severity_level": severity_level,
                "created_at": attrs.get("created_at"),
                "started_at": attrs.get("started_at"),
                "resolved_at": attrs.get("resolved_at"),
                "mitigated_at": attrs.get("mitigated_at"),
                "acknowledged_at": attrs.get("acknowledged_at"),
                "resolution_message": attrs.get("resolution_message"),
                
                # Extract user involvement
                "created_by": self._extract_user_info(attrs.get("user")),
                "started_by": self._extract_user_info(attrs.get("started_by")),
                "resolved_by": self._extract_user_info(attrs.get("resolved_by")),
                
                # Calculate durations
                "duration_minutes": self._calculate_duration(
                    attrs.get("started_at"), 
                    attrs.get("resolved_at")
                ),
                "time_to_acknowledge_minutes": self._calculate_duration(
                    attrs.get("created_at"), 
                    attrs.get("acknowledged_at")
                ),
                
                # Relationship data
                "roles": self._extract_relationship_data(incident, "roles"),
                "services": self._extract_relationship_data(incident, "services")
            }
            processed.append(processed_incident)
        return processed
    
    def _extract_user_info(self, user_data):
        """Extract user information from nested user data."""
        if not user_data or "data" not in user_data:
            return None
        
        user = user_data["data"]
        attrs = user.get("attributes", {})
        
        return {
            "id": user.get("id"),
            "name": attrs.get("full_name", attrs.get("name")),
            "email": attrs.get("email"),
            "slack_id": attrs.get("slack_id")
        }
    
    def _calculate_duration(self, start_time, end_time):
        """Calculate duration in minutes between two timestamps."""
        if not start_time or not end_time:
            return None
        
        try:
            start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            return (end - start).total_seconds() / 60
        except Exception:
            return None
    
    def _extract_relationship_data(self, incident, relationship_name):
        """Extract relationship IDs from incident data."""
        relationships = incident.get("relationships", {})
        relationship = relationships.get(relationship_name, {})
        
        if "data" in relationship:
            data = relationship["data"]
            if isinstance(data, list):
                return [item.get("id") for item in data if item.get("id")]
            elif isinstance(data, dict):
                return [data.get("id")] if data.get("id") else []
        
        return []
    
    def _map_users_to_incidents(self, users, incidents):
        """Create mapping of user IDs to incident IDs they were involved in."""
        user_incidents = {}
        
        # Initialize mapping for all users
        for user in users:
            user_id = user.get("id")
            if user_id:
                user_incidents[user_id] = []
        
        # Map incidents to users based on involvement
        for incident in incidents:
            incident_id = incident.get("id")
            if not incident_id:
                continue
            
            # Check user involvement
            for field in ["created_by", "started_by", "resolved_by"]:
                user_info = incident.get(field)
                if user_info and user_info.get("id"):
                    user_id = user_info["id"]
                    if user_id in user_incidents:
                        if incident_id not in user_incidents[user_id]:
                            user_incidents[user_id].append(incident_id)
        
        return user_incidents
    
    def generate_basic_insights(self, results):
        """Generate basic insights about individual burnout analysis."""
        high_risk = [r for r in results if r.get("risk_level") == "high"]
        medium_risk = [r for r in results if r.get("risk_level") == "medium"]
        low_risk = [r for r in results if r.get("risk_level") == "low"]
        
        total_users = len(results)
        high_risk_percentage = (len(high_risk) / total_users * 100) if total_users > 0 else 0
        
        # Determine overall status
        if len(high_risk) >= 3 or high_risk_percentage > 25:
            status = "CRITICAL"
            message = f"CRITICAL: {len(high_risk)} users at high burnout risk"
        elif len(high_risk) > 0:
            status = "HIGH_RISK"
            message = f"HIGH RISK: {len(high_risk)} users need immediate attention"
        elif len(medium_risk) > total_users * 0.4:
            status = "MEDIUM_RISK"
            message = f"MEDIUM RISK: Monitor {len(medium_risk)} users closely"
        else:
            status = "HEALTHY"
            message = "Individual health appears normal - continued monitoring"
        
        # Format high-risk users for API response
        high_risk_users = []
        for user in high_risk[:5]:  # Top 5 high-risk users
            high_risk_users.append({
                "name": user.get("user_name"),
                "user_id": user.get("user_id"),
                "score": user.get("burnout_score"),
                "risk_level": user.get("risk_level"),
                "incidents": user.get("analysis_period", {}).get("incident_count", 0),
                "key_factors": user.get("dimensions", {}).get("emotional_exhaustion", {}).get("contributing_factors", [])[:2]
            })
        
        return {
            "status": status,
            "message": message,
            "summary": {
                "total_users": total_users,
                "high_risk_count": len(high_risk),
                "medium_risk_count": len(medium_risk),
                "low_risk_count": len(low_risk),
                "high_risk_percentage": round(high_risk_percentage, 1),
                "average_score": round(sum(r.get("burnout_score", 0) for r in results) / total_users, 2) if total_users > 0 else 0
            },
            "high_risk_users": high_risk_users,
            "recommendations": self._generate_recommendations(status, high_risk, medium_risk)
        }
    
    def _generate_recommendations(self, status, high_risk, medium_risk):
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        if status == "CRITICAL":
            recommendations.extend([
                "Immediate action required - schedule emergency review",
                "Create workload redistribution plan for high-risk users",
                "Consider mandatory time off for highest-risk individuals",
                "Evaluate capacity and consider additional support"
            ])
        elif status == "HIGH_RISK":
            recommendations.extend([
                "Schedule 1-on-1s with high-risk users within 24 hours",
                "Review and adjust on-call rotation schedules",
                "Redistribute incident assignments from overloaded users"
            ])
        elif status == "MEDIUM_RISK":
            recommendations.extend([
                "Monitor medium-risk users for escalation",
                "Review incident trends and identify patterns",
                "Consider process improvements to reduce incident load"
            ])
        else:
            recommendations.extend([
                "Continue regular monitoring",
                "Maintain current incident response processes",
                "Focus on preventive measures and wellness"
            ])
        
        return recommendations
    
    async def run_analysis(self, days=30):
        """Run complete burnout analysis using sophisticated analyzer."""
        try:
            # Get data from Rootly
            users, incidents = await self.get_rootly_data()
            
            # Analyze burnout patterns using comprehensive analyzer
            individual_analyses = self.analyze_burnout(users, incidents, days)
            
            # Generate insights
            insights = self.generate_basic_insights(individual_analyses)
            
            # Compile final report
            report = {
                "timestamp": datetime.now().isoformat(),
                "analysis_period_days": days,
                "total_users_analyzed": len(users),
                "total_incidents_analyzed": len(incidents),
                "individual_analyses": individual_analyses,
                "insights": insights,
                "metadata": {
                    "analyzer_version": "comprehensive",
                    "dimensions": ["emotional_exhaustion", "depersonalization", "personal_accomplishment"],
                    "based_on": "Maslach Burnout Inventory principles"
                }
            }
            
            return report
            
        except Exception as e:
            return {
                "error": True,
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }


# For testing locally
async def main():
    """Test the detector locally."""
    print("Comprehensive Burnout Detector (Vercel Compatible)")
    print("=" * 50)
    
    detector = VercelBurnoutDetector()
    report = await detector.run_analysis(30)
    
    if report.get("error"):
        print(f"Error: {report['message']}")
        return
    
    insights = report["insights"]
    print(f"Analysis: {report['total_users_analyzed']} users, {report['total_incidents_analyzed']} incidents")
    print(f"Status: {insights['message']}")
    
    summary = insights["summary"]
    print(f"Risk Distribution: {summary['high_risk_count']} HIGH | {summary['medium_risk_count']} MEDIUM | {summary['low_risk_count']} LOW")
    print(f"Average Score: {summary['average_score']}/10")
    
    if insights["high_risk_users"]:
        print(f"\nHIGH RISK USERS:")
        for user in insights["high_risk_users"]:
            print(f"  - {user['name']}: {user['score']}/10 ({user['incidents']} incidents)")
            if user['key_factors']:
                print(f"    Factors: {', '.join(user['key_factors'])}")
    
    print(f"\nRECOMMENDATIONS:")
    for rec in insights["recommendations"]:
        print(f"  - {rec}")
    
    print(f"\nANALYSIS DETAILS:")
    print(f"  - Analyzer: {report['metadata']['analyzer_version']}")
    print(f"  - Dimensions: {', '.join(report['metadata']['dimensions'])}")
    print(f"  - Based on: {report['metadata']['based_on']}")
    
    # Save report
    with open("vercel_burnout_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to vercel_burnout_report.json")


if __name__ == "__main__":
    asyncio.run(main())