"""
Dashboard generator for burnout analysis results.
"""

import json
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime


class BurnoutDashboard:
    """Generates HTML dashboard from burnout analysis results."""
    
    def __init__(self, results: Dict[str, Any]):
        self.results = results
        self.template_dir = Path(__file__).parent / "templates"
    
    def generate_dashboard(self, output_path: str):
        """Generate complete HTML dashboard."""
        html_content = self._generate_html()
        
        with open(output_path, 'w') as f:
            f.write(html_content)
    
    def _generate_html(self) -> str:
        """Generate the complete HTML content."""
        individual_analyses = self.results.get("individual_analyses", [])
        metadata = self.results.get("metadata", {})
        
        # Format timestamp for display
        timestamp = metadata.get('analysis_timestamp', 'N/A')
        if timestamp != 'N/A':
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_timestamp = dt.strftime('%B %d, %Y at %I:%M %p')
            except:
                formatted_timestamp = timestamp
        else:
            formatted_timestamp = timestamp
        
        # Prepare data for JavaScript
        chart_data = self._prepare_chart_data(individual_analyses)
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rootly Burnout Analysis Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .metric-label {{
            color: #666;
            font-size: 0.9em;
        }}
        .risk-high {{ color: #dc3545; }}
        .risk-medium {{ color: #ffc107; }}
        .risk-low {{ color: #28a745; }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            height: 350px;
        }}
        .user-list {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .user-item {{
            padding: 15px 20px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .user-item:last-child {{
            border-bottom: none;
        }}
        .user-name {{
            font-weight: 500;
        }}
        .expand-arrow {{
            cursor: pointer;
            margin-right: 8px;
            color: #007bff;
            font-size: 12px;
            transition: transform 0.2s ease;
            display: inline-block;
        }}
        .expand-arrow:hover {{
            color: #0056b3;
        }}
        .expand-arrow.expanded {{
            transform: rotate(90deg);
        }}
        .user-details {{
            display: none;
            margin-top: 15px;
            padding: 20px;
            margin-left: 15px;
            margin-right: 15px;
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
            border-radius: 12px;
            border: 1px solid #e9ecef;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }}
        .user-details.show {{
            display: block;
        }}
        .detail-section {{
            margin-bottom: 20px;
            padding: 16px;
            background-color: rgba(255,255,255,0.7);
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }}
        .detail-section:last-child {{
            margin-bottom: 0;
        }}
        .detail-label {{
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 8px;
            font-size: 1em;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .detail-value {{
            font-size: 0.9em;
            color: #495057;
            margin-left: 0;
            line-height: 1.5;
        }}
        .metric-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
            padding: 8px 12px;
            background-color: rgba(248,249,250,0.8);
            border-radius: 6px;
        }}
        .metric-row:last-child {{
            margin-bottom: 0;
        }}
        .metric-row span:first-child {{
            color: #6c757d;
            font-weight: 500;
        }}
        .metric-row span:last-child {{
            color: #2c3e50;
            font-weight: 600;
        }}
        .user-score {{
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 4px;
            color: white;
        }}
        .recommendations {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .rec-item {{
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }}
        .rec-item:last-child {{
            border-bottom: none;
        }}
        h1, h2, h3 {{
            margin-top: 0;
        }}
        .timestamp {{
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Rootly Burnout Analysis Dashboard</h1>
            <p class="timestamp">Analysis completed: {formatted_timestamp}</p>
            <p>Period: {metadata.get('days_analyzed', 'N/A')} days | 
               Users: {metadata.get('total_users_analyzed', 'N/A')} | 
               Incidents: {metadata.get('total_incidents', 'N/A')}{self._get_github_integration_status(metadata)}</p>
            
            <div style="margin-top: 15px; padding: 15px; background-color: #f8f9fa; border-radius: 5px; border-left: 4px solid #007bff;">
                <h4 style="margin: 0 0 10px 0; color: #495057;">How Burnout Scores Are Calculated</h4>
                <p style="margin: 0; color: #6c757d; font-size: 0.9em;">
                    Scores (0-10) are based on the <strong>Maslach Burnout Inventory</strong> using three dimensions:
                    <strong>Emotional Exhaustion</strong> (incident frequency, after-hours work, resolution time),
                    <strong>Depersonalization</strong> (escalation rates, collaboration patterns), and
                    <strong>Personal Accomplishment</strong> (resolution success, response effectiveness).
                    Higher scores indicate greater burnout risk.
                </p>
            </div>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value risk-high">{self._count_risk_level(individual_analyses, 'high')}</div>
                <div class="metric-label">High Risk Users</div>
            </div>
            <div class="metric-card">
                <div class="metric-value risk-medium">{self._count_risk_level(individual_analyses, 'medium')}</div>
                <div class="metric-label">Medium Risk Users</div>
            </div>
            <div class="metric-card">
                <div class="metric-value risk-low">{self._count_risk_level(individual_analyses, 'low')}</div>
                <div class="metric-label">Low Risk Users</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{self._calculate_average_score(individual_analyses)}/10</div>
                <div class="metric-label">Average Score</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h3>Burnout Scores by User</h3>
            <canvas id="scoresChart" width="400" height="150"></canvas>
        </div>
        
        <div class="user-list">
            <h3 style="padding: 20px 20px 0 20px;">Individual Analysis</h3>
            {self._generate_user_list(individual_analyses)}
        </div>
    </div>
    
    <script>
        // Burnout scores bar chart
        const scoresCtx = document.getElementById('scoresChart').getContext('2d');
        new Chart(scoresCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(chart_data['user_names'])},
                datasets: [{{
                    label: 'Burnout Score',
                    data: {json.dumps(chart_data['scores'])},
                    backgroundColor: {json.dumps(chart_data['colors'])}
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 10,
                        ticks: {{
                            stepSize: 2
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                layout: {{
                    padding: {{
                        top: 10,
                        bottom: 10
                    }}
                }}
            }}
        }});
        
        // Toggle user details dropdown
        function toggleUserDetails(userId) {{
            const detailsElement = document.getElementById('details-' + userId);
            const arrowElement = event.target;
            if (detailsElement) {{
                detailsElement.classList.toggle('show');
                arrowElement.classList.toggle('expanded');
            }}
        }}
    </script>
</body>
</html>
        """
        
        return html
    
    def _prepare_chart_data(self, individual_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare data for JavaScript charts."""
        user_names = []
        scores = []
        colors = []
        
        # User scores data (sorted by score, descending)
        sorted_analyses = sorted(
            individual_analyses, 
            key=lambda x: x.get('burnout_score', 0), 
            reverse=True
        )
        
        for analysis in sorted_analyses:
            user_names.append(analysis.get('user_name', 'Unknown'))
            score = analysis.get('burnout_score', 0)
            scores.append(score)
            
            # Color based on risk level
            risk_level = analysis.get('risk_level', 'low')
            if risk_level == 'high':
                colors.append('#dc3545')
            elif risk_level == 'medium':
                colors.append('#ffc107')
            else:
                colors.append('#28a745')
        
        return {
            'user_names': user_names,
            'scores': scores,
            'colors': colors
        }
    
    def _generate_user_list(self, individual_analyses: List[Dict[str, Any]]) -> str:
        """Generate HTML for user list."""
        html = ""
        
        # Sort by burnout score (highest first)
        sorted_analyses = sorted(
            individual_analyses,
            key=lambda x: x.get('burnout_score', 0),
            reverse=True
        )
        
        for analysis in sorted_analyses:
            user_name = analysis.get('user_name', 'Unknown')
            score = analysis.get('burnout_score', 0)
            risk_level = analysis.get('risk_level', 'low')
            
            # Determine background color for score
            if risk_level == 'high':
                score_class = 'risk-high'
                bg_color = '#dc3545'
            elif risk_level == 'medium':
                score_class = 'risk-medium'  
                bg_color = '#ffc107'
            else:
                score_class = 'risk-low'
                bg_color = '#28a745'
            
            # Get top recommendation
            recommendations = analysis.get('recommendations', [])
            top_rec = recommendations[0] if recommendations else "No specific recommendations"
            
            # Generate detailed metrics display
            user_details = self._generate_user_details(analysis)
            
            html += f"""
            <div class="user-item">
                <div style="flex: 1;">
                    <div style="display: flex; align-items: center;">
                        <span class="expand-arrow" onclick="toggleUserDetails('{analysis.get('user_id', '')}')">▶</span>
                        <div class="user-name">{user_name}</div>
                    </div>
                    <div style="font-size: 0.8em; color: #666; margin-top: 4px;">{top_rec}</div>
                    <div id="details-{analysis.get('user_id', '')}" class="user-details">
                        {user_details}
                    </div>
                </div>
                <div class="user-score" style="background-color: {bg_color}">{score}</div>
            </div>
            """
        
        return html
    
    def _generate_user_details(self, analysis: Dict[str, Any]) -> str:
        """Generate detailed metrics for a user."""
        user_id = analysis.get('user_id', '')
        user_email = analysis.get('user_email', '')
        key_metrics = analysis.get('key_metrics', {})
        dimensions = analysis.get('dimensions', {})
        
        # Format key metrics
        total_incidents = key_metrics.get('total_incidents', 0)
        incidents_per_week = key_metrics.get('incidents_per_week', 0)
        after_hours_incidents = key_metrics.get('after_hours_incidents', 0)
        avg_resolution_time = key_metrics.get('avg_resolution_time_hours', 0)
        resolution_success_rate = key_metrics.get('resolution_success_rate', 0)
        
        # Format resolution time as hours and minutes
        if avg_resolution_time >= 1:
            hours = int(avg_resolution_time)
            minutes = int((avg_resolution_time - hours) * 60)
            if minutes > 0:
                resolution_time_display = f"{hours}h {minutes}m"
            else:
                resolution_time_display = f"{hours}h"
        else:
            minutes = int(avg_resolution_time * 60)
            resolution_time_display = f"{minutes}m"
        
        # Format dimension scores
        emotional_exhaustion = dimensions.get('emotional_exhaustion', {}).get('score', 0)
        depersonalization = dimensions.get('depersonalization', {}).get('score', 0)
        personal_accomplishment = dimensions.get('personal_accomplishment', {}).get('score', 0)
        
        
        details_html = f"""
        <div class="detail-section">
            <div class="detail-label">📧 Contact</div>
            <div class="detail-value">User ID: {user_id}</div>
            <div class="detail-value">Email: {user_email}</div>
        </div>
        
        <div class="detail-section">
            <div class="detail-label">📊 Key Metrics (Last 30 Days)</div>
            <div class="metric-row">
                <span>Total Incidents:</span>
                <span><strong>{total_incidents}</strong></span>
            </div>
            <div class="metric-row">
                <span>Incidents/Week:</span>
                <span><strong>{incidents_per_week:.2f}</strong></span>
            </div>
            <div class="metric-row">
                <span>After-Hours Incidents:</span>
                <span><strong>{after_hours_incidents}</strong></span>
            </div>
            <div class="metric-row">
                <span>Avg Resolution Time:</span>
                <span><strong>{resolution_time_display}</strong></span>
            </div>
            <div class="metric-row">
                <span>Resolution Success Rate:</span>
                <span><strong>{resolution_success_rate:.1%}</strong></span>
            </div>
        </div>
        
        <div class="detail-section">
            <div class="detail-label">🧠 Burnout Dimensions</div>
            <div class="metric-row">
                <span>Emotional Exhaustion:</span>
                <span><strong>{emotional_exhaustion:.2f}/10</strong></span>
            </div>
            <div class="metric-row">
                <span>Depersonalization:</span>
                <span><strong>{depersonalization:.2f}/10</strong></span>
            </div>
            <div class="metric-row">
                <span>Personal Accomplishment:</span>
                <span><strong>{personal_accomplishment:.2f}/10</strong></span>
            </div>
        </div>
        
        {self._generate_github_metrics_section(dimensions)}
        """
        
        return details_html
    
    def _count_risk_level(self, analyses: List[Dict[str, Any]], risk_level: str) -> int:
        """Count users at a specific risk level."""
        return sum(1 for analysis in analyses if analysis.get('risk_level') == risk_level)
    
    def _calculate_average_score(self, analyses: List[Dict[str, Any]]) -> float:
        """Calculate average burnout score across all users."""
        if not analyses:
            return 0.0
        scores = [analysis.get('burnout_score', 0) for analysis in analyses]
        return round(sum(scores) / len(scores), 2)
    
    def _get_github_integration_status(self, metadata: Dict[str, Any]) -> str:
        """Get GitHub integration status display text."""
        config = metadata.get('config_used', {})
        github_config = config.get('github_integration', {})
        
        if github_config.get('enabled', False):
            return ' | <span style="color: #28a745;">✓ GitHub Integration Enabled</span>'
        else:
            return ''
    
    def _generate_github_metrics_section(self, dimensions: Dict[str, Any]) -> str:
        """Generate GitHub metrics section if GitHub data is available."""
        # Check if any dimension has GitHub indicators
        has_github_data = False
        github_metrics = {}
        
        for dimension_name, dimension_data in dimensions.items():
            indicators = dimension_data.get('indicators', {})
            for key, value in indicators.items():
                if key.startswith('github_') and value is not None:
                    has_github_data = True
                    github_metrics[key] = value
        
        if not has_github_data:
            return ""
        
        # Format GitHub metrics for display
        html = """
        <div class="detail-section">
            <div class="detail-label">💻 GitHub Activity Metrics</div>"""
        
        # Add relevant GitHub metrics
        if 'github_total_commits' in github_metrics:
            html += f"""
            <div class="metric-row">
                <span>Total Commits:</span>
                <span><strong>{github_metrics['github_total_commits']}</strong></span>
            </div>"""
        
        if 'github_after_hours_percentage' in github_metrics:
            percentage = github_metrics['github_after_hours_percentage'] * 100 if github_metrics['github_after_hours_percentage'] else 0
            html += f"""
            <div class="metric-row">
                <span>After-Hours Commits:</span>
                <span><strong>{percentage:.1f}%</strong></span>
            </div>"""
        
        if 'github_weekend_percentage' in github_metrics:
            percentage = github_metrics['github_weekend_percentage'] * 100 if github_metrics['github_weekend_percentage'] else 0
            html += f"""
            <div class="metric-row">
                <span>Weekend Commits:</span>
                <span><strong>{percentage:.1f}%</strong></span>
            </div>"""
        
        if 'github_commits_per_week' in github_metrics:
            html += f"""
            <div class="metric-row">
                <span>Commits/Week:</span>
                <span><strong>{github_metrics['github_commits_per_week']:.1f}</strong></span>
            </div>"""
        
        if 'github_prs_per_week' in github_metrics:
            html += f"""
            <div class="metric-row">
                <span>PRs/Week:</span>
                <span><strong>{github_metrics['github_prs_per_week']:.1f}</strong></span>
            </div>"""
        
        if 'github_repositories_touched' in github_metrics:
            html += f"""
            <div class="metric-row">
                <span>Repositories Worked On:</span>
                <span><strong>{github_metrics['github_repositories_touched']}</strong></span>
            </div>"""
        
        html += """
        </div>"""
        
        return html


def generate_dashboard_from_file(results_file: str, output_file: str):
    """Generate dashboard from saved results file."""
    with open(results_file) as f:
        results = json.load(f)
    
    dashboard = BurnoutDashboard(results)
    dashboard.generate_dashboard(output_file)
    
    print(f"Dashboard generated: {output_file}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python dashboard.py <results.json> <output.html>")
        sys.exit(1)
    
    generate_dashboard_from_file(sys.argv[1], sys.argv[2])