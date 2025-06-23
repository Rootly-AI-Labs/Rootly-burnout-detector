#!/usr/bin/env python3
"""
Test interactive mode with demo data
"""

import json
import sys
import os

# Add src to path
sys.path.insert(0, "src")

def test_interactive_mode():
    """Test interactive mode with demo data."""
    
    # Load demo data
    with open("demo_burnout_report.json") as f:
        demo_data = json.load(f)
    
    # Convert to the format expected by InteractiveAnalyzer
    results = {
        "metadata": {
            "analysis_timestamp": demo_data["timestamp"],
            "days_analyzed": demo_data["analysis_period_days"],
            "total_users_analyzed": demo_data["total_users_analyzed"],
            "total_incidents": demo_data["total_incidents_analyzed"],
        },
        "individual_analyses": demo_data["individual_analyses"]
    }
    
    # Check interactive requirements
    from interactive_analyzer import check_interactive_requirements
    
    available, message = check_interactive_requirements()
    print(f"Interactive mode status: {message}")
    
    if not available:
        print("\nTo test interactive mode, set an API key:")
        print("export OPENAI_API_KEY='your-key'")
        print("export ANTHROPIC_API_KEY='your-key'")  
        print("export HF_TOKEN='your-token'")
        return
    
    # Start interactive mode
    from interactive_analyzer import InteractiveAnalyzer
    
    print("\n" + "="*50)
    print("TESTING INTERACTIVE MODE WITH DEMO DATA")
    print("="*50)
    
    analyzer = InteractiveAnalyzer(results)
    analyzer.start_session()

if __name__ == "__main__":
    test_interactive_mode()