#!/usr/bin/env python3
"""
Rootly Burnout Detector - Main entry point
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Load environment variables from multiple sources
def load_environment_variables():
    """Load environment variables from .env, secrets.env, etc."""
    env_files = [".env", "secrets.env"]
    
    # Try using python-dotenv first
    try:
        from dotenv import load_dotenv
        for env_file in env_files:
            env_path = Path(__file__).parent / env_file
            if env_path.exists():
                # Use override=True to ensure variables are set in os.environ
                # This ensures subprocesses inherit them
                load_dotenv(env_path, override=True)
                print(f"Loaded environment from {env_file}")
    except ImportError:
        # Manual loading if python-dotenv not available
        for env_file in env_files:
            env_path = Path(__file__).parent / env_file
            if env_path.exists():
                with open(env_path) as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.strip().split('=', 1)
                                # Remove quotes if present
                                value = value.strip('"\'')
                                os.environ[key] = value
                print(f"Loaded environment from {env_file}")

load_environment_variables()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data_collector import RootlyDataCollector
from burnout_analyzer import BurnoutAnalyzer
from dashboard import BurnoutDashboard
from github_correlator import GitHubCorrelator
from github_collector import GitHubCollector
from slack_collector import SlackCollector


def setup_logging(debug: bool = False):
    """Configure logging."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    if not os.path.exists(config_path):
        print(f"Config file not found: {config_path}")
        print("Create config.json from config.example.json")
        sys.exit(1)
    
    try:
        with open(config_path) as f:
            config = json.load(f)
        
        # Validate required environment variables
        required_env = ["ROOTLY_API_TOKEN"]
        missing_env = []
        
        for env_var in required_env:
            if not os.getenv(env_var):
                missing_env.append(env_var)
        
        if missing_env:
            print(f"Missing required environment variables: {', '.join(missing_env)}")
            print("Set them with: export ROOTLY_API_TOKEN='your-token'")
            sys.exit(1)
        
        return config
        
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in config file: {e}")
        sys.exit(1)


def save_results(results: Dict[str, Any], output_dir: str):
    """Save analysis results to files."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Save main results
    results_path = os.path.join(output_dir, "burnout_analysis.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to {results_path}")
    
    # Save individual user reports
    if "individual_analyses" in results:
        individual_dir = os.path.join(output_dir, "individual_reports")
        os.makedirs(individual_dir, exist_ok=True)
        
        for analysis in results["individual_analyses"]:
            user_file = f"{analysis['user_id']}.json"
            user_path = os.path.join(individual_dir, user_file)
            with open(user_path, "w") as f:
                json.dump(analysis, f, indent=2)
    
    # Generate summary report
    generate_summary_report(results, output_dir)


def generate_summary_report(results: Dict[str, Any], output_dir: str):
    """Generate a human-readable summary report."""
    summary_path = os.path.join(output_dir, "summary_report.txt")
    
    with open(summary_path, "w") as f:
        f.write("ROOTLY BURNOUT ANALYSIS SUMMARY\n")
        f.write("=" * 40 + "\n\n")
        
        # Overall statistics
        metadata = results.get("metadata", {})
        f.write(f"Analysis Period: {metadata.get('days_analyzed', 'N/A')} days\n")
        f.write(f"Total Users Analyzed: {metadata.get('total_users_analyzed', 'N/A')}\n")
        f.write(f"Total Incidents: {metadata.get('total_incidents', 'N/A')}\n")
        f.write(f"Analysis Date: {metadata.get('analysis_timestamp', 'N/A')}\n\n")
        
        # Risk distribution
        individual_analyses = results.get("individual_analyses", [])
        if individual_analyses:
            f.write("RISK DISTRIBUTION\n")
            f.write("-" * 20 + "\n")
            high_count = sum(1 for a in individual_analyses if a.get("risk_level") == "high")
            medium_count = sum(1 for a in individual_analyses if a.get("risk_level") == "medium")
            low_count = sum(1 for a in individual_analyses if a.get("risk_level") == "low")
            
            # Separate active on-call users from all users
            active_users = [a for a in individual_analyses if a.get("analysis_period", {}).get("incident_count", 0) > 0]
            all_scores = [a.get("burnout_score", 0) for a in individual_analyses]
            active_scores = [a.get("burnout_score", 0) for a in active_users]
            
            avg_score_all = sum(all_scores) / len(all_scores) if all_scores else 0
            avg_score_active = sum(active_scores) / len(active_scores) if active_scores else 0
            
            f.write(f"High Risk: {high_count} users\n")
            f.write(f"Medium Risk: {medium_count} users\n")
            f.write(f"Low Risk: {low_count} users\n")
            f.write(f"Average Score (All Users): {avg_score_all:.2f}/10\n")
            f.write(f"Average Score (Active On-Call): {avg_score_active:.2f}/10 ({len(active_users)} users)\n")
            f.write(f"Users with Zero Incidents: {len(individual_analyses) - len(active_users)} users\n\n")
        
        # High-risk users
        high_risk_users = [
            analysis for analysis in results.get("individual_analyses", [])
            if analysis.get("risk_level") == "high"
        ]
        
        if high_risk_users:
            f.write("HIGH RISK USERS\n")
            f.write("-" * 20 + "\n")
            for user in high_risk_users:
                f.write(f"- {user['user_name']} (Score: {user['burnout_score']}/10)\n")
                for rec in user.get("recommendations", [])[:2]:  # Top 2 recommendations
                    f.write(f"  - {rec}\n")
                f.write("\n")
        
        
    print(f"Summary report saved to {summary_path}")


async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Analyze burnout risk for Rootly on-call engineers")
    parser.add_argument(
        "--config", 
        default="config/config.json",
        help="Path to configuration file (default: config/config.json)"
    )
    parser.add_argument(
        "--days", 
        type=int, 
        help="Number of days to analyze (overrides config)"
    )
    parser.add_argument(
        "--output", 
        default="output",
        help="Output directory (default: output)"
    )
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Test connection without running analysis"
    )
    parser.add_argument(
        "--interactive", 
        action="store_true",
        help="Start interactive analysis mode after completing analysis"
    )
    parser.add_argument(
        "--token",
        type=str,
        help="Rootly API token (overrides environment variables)"
    )
    parser.add_argument(
        "--include-github",
        action="store_true",
        help="Include GitHub activity data in burnout analysis"
    )
    parser.add_argument(
        "--refresh-github-cache",
        action="store_true",
        help="Refresh GitHub data cache (forces API calls)"
    )
    parser.add_argument(
        "--include-slack",
        action="store_true",
        help="Include Slack communication data in burnout analysis"
    )
    parser.add_argument(
        "--refresh-slack-cache",
        action="store_true",
        help="Refresh Slack data cache (forces API calls)"
    )
    
    args = parser.parse_args()
    
    # Setup
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)
    
    print("Rootly Burnout Detector")
    print("=" * 30)
    
    # Handle token from command line
    if args.token:
        os.environ["ROOTLY_API_TOKEN"] = args.token
        print("Using token from command line")
    
    # Set up authentication for MCP server
    if os.environ.get("ROOTLY_API_TOKEN"):
        print("✓ Rootly authentication configured")
    
    # Load configuration
    config = load_config(args.config)
    
    # Override days if specified
    if args.days:
        config["analysis"]["days_to_analyze"] = args.days
    
    # Test connection if dry run
    if args.dry_run:
        print("Testing MCP connection...")
        from mcp_client import test_connection
        success = await test_connection(config)
        if success:
            print("Connection test successful!")
        else:
            print("Connection test failed!")
        return
    
    try:
        # Data collection
        print("Collecting data from Rootly...")
        collector = RootlyDataCollector(config)
        
        try:
            raw_data = await collector.collect_all_data()
        except (RuntimeError, Exception) as e:
            # Extract the root cause from nested exception groups
            error_msg = str(e)
            if "Failed to fetch users from Rootly" in error_msg:
                print(f"\n❌ Failed to fetch users from Rootly. Check your API token and MCP server connection.")
            elif "TaskGroup" in error_msg and "401" in error_msg:
                print(f"\n❌ Authentication failed (401 Unauthorized). Your Rootly API token is invalid or expired.")
            elif "TaskGroup" in error_msg:
                print(f"\n❌ Connection to Rootly failed. Check your network connection and API token.")
            else:
                print(f"\n❌ Error: {error_msg}")
            
            print("\nPossible solutions:")
            print("- Check your ROOTLY_API_TOKEN is valid")
            print("- Verify you have access to the Rootly organization")
            print("- Check your network connection")
            print("- Try running with --debug for more details")
            sys.exit(1)
        
        print(f"Collected {len(raw_data['users'])} users and {len(raw_data['incidents'])} incidents")
        
        # GitHub integration
        if args.include_github:
            print("Integrating GitHub activity data...")
            
            # Check GitHub token
            github_token = os.getenv('GITHUB_TOKEN')
            if not github_token:
                print("❌ GitHub integration requires GITHUB_TOKEN in secrets.env")
                print("Run without --include-github or add your GitHub token")
                sys.exit(1)
            
            # Set refresh flag in config
            if args.refresh_github_cache:
                config['_refresh_github_cache'] = True
                print("🔄 Refreshing GitHub cache...")
            
            # Enable GitHub integration in config
            config['github_integration']['enabled'] = True
            
            # Correlate Rootly users with GitHub accounts
            correlator = GitHubCorrelator(github_token, config)
            github_correlations = correlator.correlate_users(raw_data['users'])
            
            # Add correlation results to raw_data for analysis
            raw_data['github_correlations'] = github_correlations
            
            # Report correlation results
            matched_count = sum(1 for v in github_correlations.values() if v is not None)
            total_count = len(github_correlations)
            match_rate = (matched_count / total_count * 100) if total_count > 0 else 0
            
            print(f"✅ GitHub correlation: {matched_count}/{total_count} users matched ({match_rate:.1f}%)")
            
            if matched_count < total_count:
                unmatched = [email for email, github in github_correlations.items() if github is None]
                print(f"   📝 Add {len(unmatched)} users to config.json user_mappings for better coverage")
            
            # Collect GitHub activity data
            if matched_count > 0:
                print("📊 Collecting GitHub activity data...")
                github_collector = GitHubCollector(github_token, config)
                github_activity = github_collector.collect_github_data(
                    github_correlations, 
                    config['analysis']['days_to_analyze']
                )
                
                # Add GitHub activity to raw_data
                raw_data['github_activity'] = github_activity
                print(f"✅ GitHub activity collected for {len(github_activity)} users")
            else:
                print("⚠️  No matched users found, skipping GitHub activity collection")
        
        # Slack integration
        if args.include_slack:
            print("Integrating Slack communication data...")
            
            # Check Slack token
            slack_token = os.getenv('SLACK_BOT_TOKEN')
            if not slack_token:
                print("❌ Slack integration requires SLACK_BOT_TOKEN in secrets.env")
                print("Run without --include-slack or add your Slack token")
                sys.exit(1)
            
            # Set refresh flag in config
            if args.refresh_slack_cache:
                config['_refresh_slack_cache'] = True
                print("🔄 Refreshing Slack cache...")
            
            # Enable Slack integration in config
            if 'slack_integration' not in config:
                config['slack_integration'] = {}
            config['slack_integration']['enabled'] = True
            
            # Create user mappings for Slack (email -> slack user ID)
            # Use configured mappings from config.json
            configured_mappings = config.get('slack_integration', {}).get('user_mappings', {})
            slack_mappings = {}
            
            for user in raw_data['users']:
                user_email = user['email']
                if user_email in configured_mappings:
                    slack_mappings[user_email] = configured_mappings[user_email]
            
            # Collect Slack activity data
            print("📊 Collecting Slack communication data...")
            slack_collector = SlackCollector(slack_token, config)
            slack_activity = slack_collector.collect_slack_data(
                slack_mappings, 
                config['analysis']['days_to_analyze']
            )
            
            # Add Slack activity to raw_data
            raw_data['slack_activity'] = slack_activity
            print(f"✅ Slack activity collected for {len(slack_activity)} users")
        
        # Burnout analysis
        print("Analyzing burnout risk...")
        analyzer = BurnoutAnalyzer(config)
        
        individual_analyses = []
        user_incident_mapping = raw_data["user_incident_mapping"]
        
        for user in raw_data["users"]:
            user_id = user["id"]
            user_incidents = user_incident_mapping.get(user_id, [])
            
            # Get GitHub activity for this user if available
            github_activity_for_user = None
            if args.include_github and 'github_activity' in raw_data:
                # Find GitHub username for this user
                github_correlations = raw_data.get('github_correlations', {})
                github_username = github_correlations.get(user["email"])
                if github_username and github_username in raw_data['github_activity']:
                    github_activity_for_user = raw_data['github_activity'][github_username]
            
            # Get Slack activity for this user if available
            slack_activity_for_user = None
            if args.include_slack and 'slack_activity' in raw_data:
                # Find Slack user ID for this user from configured mappings
                configured_mappings = config.get('slack_integration', {}).get('user_mappings', {})
                slack_user_id = configured_mappings.get(user["email"])
                if slack_user_id and slack_user_id in raw_data['slack_activity']:
                    slack_activity_for_user = raw_data['slack_activity'][slack_user_id]
            
            analysis = analyzer.analyze_user_burnout(
                user, user_incidents, raw_data["incidents"], github_activity_for_user, slack_activity_for_user
            )
            individual_analyses.append(analysis)
        
        
        # Compile results
        results = {
            "metadata": {
                "analysis_timestamp": raw_data["collection_metadata"]["timestamp"],
                "days_analyzed": config["analysis"]["days_to_analyze"],
                "total_users_analyzed": len(individual_analyses),
                "total_incidents": len(raw_data["incidents"]),
                "config_used": config
            },
            "individual_analyses": individual_analyses,
            "raw_data_summary": {
                "users_count": len(raw_data["users"]),
                "incidents_count": len(raw_data["incidents"]),
                "teams_count": 0
            }
        }
        
        # Save results
        print("Saving results...")
        save_results(results, args.output)
        
        # Generate dashboard
        if config.get("output", {}).get("create_dashboard", True):
            print("Generating dashboard...")
            dashboard = BurnoutDashboard(results)
            dashboard_path = os.path.join(args.output, "dashboard.html")
            dashboard.generate_dashboard(dashboard_path)
            print(f"Dashboard saved to {dashboard_path}")
        
        # Print summary
        print("\nANALYSIS SUMMARY")
        print("-" * 20)
        print(f"Users analyzed: {len(individual_analyses)}")
        if individual_analyses:
            high_count = sum(1 for a in individual_analyses if a.get("risk_level") == "high")
            medium_count = sum(1 for a in individual_analyses if a.get("risk_level") == "medium")
            low_count = sum(1 for a in individual_analyses if a.get("risk_level") == "low")
            
            # Separate active on-call users from all users
            active_users = [a for a in individual_analyses if a.get("analysis_period", {}).get("incident_count", 0) > 0]
            all_scores = [a.get("burnout_score", 0) for a in individual_analyses]
            active_scores = [a.get("burnout_score", 0) for a in active_users]
            
            avg_score_all = sum(all_scores) / len(all_scores) if all_scores else 0
            avg_score_active = sum(active_scores) / len(active_scores) if active_scores else 0
            
            print(f"High risk: {high_count}")
            print(f"Medium risk: {medium_count}")
            print(f"Low risk: {low_count}")
            print(f"Average score (all): {avg_score_all:.2f}/10")
            print(f"Average score (active on-call): {avg_score_active:.2f}/10 ({len(active_users)} users)")
        else:
            print("No users analyzed")
        
        # Show high-risk users
        high_risk = [a for a in individual_analyses if a["risk_level"] == "high"]
        if high_risk:
            print(f"\nHIGH RISK USERS:")
            for user in high_risk[:5]:  # Show top 5
                print(f"  - {user['user_name']}: {user['burnout_score']}/10")
        
        print(f"\nAnalysis complete! Check {args.output}/ for detailed results.")
        
        # Start interactive mode if requested
        if args.interactive:
            try:
                from src.interactive_analyzer import InteractiveAnalyzer, check_interactive_requirements
                
                # Check if interactive mode is available
                available, message = check_interactive_requirements()
                if not available:
                    print(f"\nInteractive mode not available: {message}")
                else:
                    print(f"\n{message}")
                    analyzer = InteractiveAnalyzer(results)
                    analyzer.start_session()
                    
            except ImportError as e:
                print(f"\nInteractive mode not available: {e}")
                print("Install interactive dependencies with: pip install smolagents>=0.1.0 rich>=13.0.0")
            except Exception as e:
                logger.error(f"Interactive mode failed: {e}", exc_info=True)
                print(f"Interactive mode failed: {e}")
        
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        print(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())