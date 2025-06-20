#!/usr/bin/env python3
"""
Demo script showing what the burnout detector output would look like
"""

import json
from datetime import datetime

# Mock analysis results (what you'd get from real API)
mock_results = {
    "timestamp": datetime.now().isoformat(),
    "analysis_period_days": 30,
    "total_users_analyzed": 5,
    "total_incidents_analyzed": 15,
    "individual_analyses": [
        {
            "user_name": "Alice Johnson",
            "user_id": "user_1",
            "burnout_score": 7.2,
            "risk_level": "high",
            "analysis_period": {"incident_count": 8},
            "dimensions": {
                "emotional_exhaustion": {"score": 8.1, "contributing_factors": ["High incident frequency", "Long resolution times"]},
                "depersonalization": {"score": 6.8, "contributing_factors": ["High escalation rate"]},
                "personal_accomplishment": {"score": 4.2, "contributing_factors": ["Low resolution success rate"]}
            },
            "recommendations": ["High workload detected. Consider redistributing incidents", "Frequent after-hours work detected"]
        },
        {
            "user_name": "Bob Smith", 
            "user_id": "user_2",
            "burnout_score": 4.1,
            "risk_level": "medium",
            "analysis_period": {"incident_count": 4},
            "dimensions": {
                "emotional_exhaustion": {"score": 3.8, "contributing_factors": ["Incident clustering"]},
                "depersonalization": {"score": 4.2, "contributing_factors": []},
                "personal_accomplishment": {"score": 6.8, "contributing_factors": []}
            },
            "recommendations": ["Monitor medium-risk users for escalation"]
        },
        {
            "user_name": "Carol Davis",
            "user_id": "user_3", 
            "burnout_score": 1.8,
            "risk_level": "low",
            "analysis_period": {"incident_count": 2},
            "dimensions": {
                "emotional_exhaustion": {"score": 1.2, "contributing_factors": []},
                "depersonalization": {"score": 2.1, "contributing_factors": []},
                "personal_accomplishment": {"score": 8.4, "contributing_factors": []}
            },
            "recommendations": ["Overall burnout risk appears manageable"]
        }
    ]
}

def display_results(results):
    """Display analysis results in a readable format."""
    print("Comprehensive Burnout Detector (Demo Output)")
    print("=" * 50)
    
    print(f"Analysis: {results['total_users_analyzed']} users, {results['total_incidents_analyzed']} incidents")
    
    # Calculate summary
    analyses = results['individual_analyses']
    high_risk = [a for a in analyses if a['risk_level'] == 'high']
    medium_risk = [a for a in analyses if a['risk_level'] == 'medium']
    low_risk = [a for a in analyses if a['risk_level'] == 'low']
    avg_score = sum(a['burnout_score'] for a in analyses) / len(analyses)
    
    if len(high_risk) >= 2:
        status = "CRITICAL: Multiple users at high burnout risk"
    elif len(high_risk) > 0:
        status = "HIGH RISK: Users need immediate attention"
    elif len(medium_risk) > len(analyses) * 0.4:
        status = "MEDIUM RISK: Monitor users closely"
    else:
        status = "HEALTHY: Individual health appears normal"
    
    print(f"Status: {status}")
    print(f"Risk Distribution: {len(high_risk)} HIGH | {len(medium_risk)} MEDIUM | {len(low_risk)} LOW")
    print(f"Average Score: {avg_score:.2f}/10")
    
    if high_risk:
        print(f"\nHIGH RISK USERS:")
        for user in high_risk:
            print(f"  - {user['user_name']}: {user['burnout_score']}/10 ({user['analysis_period']['incident_count']} incidents)")
            factors = user['dimensions']['emotional_exhaustion']['contributing_factors'][:2]
            if factors:
                print(f"    Factors: {', '.join(factors)}")
    
    print(f"\nRECOMMENDATIONS:")
    all_recs = set()
    for user in analyses:
        all_recs.update(user['recommendations'][:1])  # Top recommendation per user
    
    for rec in list(all_recs)[:5]:
        print(f"  - {rec}")
    
    print(f"\nANALYSIS DETAILS:")
    print(f"  - Analyzer: comprehensive")
    print(f"  - Dimensions: emotional_exhaustion, depersonalization, personal_accomplishment")
    print(f"  - Based on: Maslach Burnout Inventory principles")
    
    # Show individual details
    print(f"\nINDIVIDUAL ANALYSIS:")
    for user in sorted(analyses, key=lambda x: x['burnout_score'], reverse=True):
        risk_color = user['risk_level'].upper()
        print(f"  {user['user_name']}: {user['burnout_score']}/10 ({risk_color})")
        print(f"    Emotional Exhaustion: {user['dimensions']['emotional_exhaustion']['score']}/10")
        print(f"    Depersonalization: {user['dimensions']['depersonalization']['score']}/10") 
        print(f"    Personal Accomplishment: {user['dimensions']['personal_accomplishment']['score']}/10")
        print(f"    Incidents: {user['analysis_period']['incident_count']}")
        print()

if __name__ == "__main__":
    print("Demo: Rootly Burnout Detection Output")
    print("(This shows what real analysis results would look like)")
    print()
    
    display_results(mock_results)
    
    # Save demo output
    with open("demo_burnout_report.json", "w") as f:
        json.dump(mock_results, f, indent=2)
    
    print("Demo report saved to demo_burnout_report.json")