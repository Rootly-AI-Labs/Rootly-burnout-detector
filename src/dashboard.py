"""
Dashboard generator for burnout analysis results.
"""

import json
import os
from typing import Dict, Any, List
from pathlib import Path


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
            <p class="timestamp">Analysis completed: {metadata.get('analysis_timestamp', 'N/A')}</p>
            <p>Period: {metadata.get('days_analyzed', 'N/A')} days | 
               Users: {metadata.get('total_users_analyzed', 'N/A')} | 
               Incidents: {metadata.get('total_incidents', 'N/A')}</p>
            
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
            <canvas id="scoresChart" width="400" height="200"></canvas>
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
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 10
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }}
            }}
        }});
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
            
            html += f"""
            <div class="user-item">
                <div>
                    <div class="user-name">{user_name}</div>
                    <div style="font-size: 0.8em; color: #666; margin-top: 4px;">{top_rec}</div>
                </div>
                <div class="user-score" style="background-color: {bg_color}">{score}</div>
            </div>
            """
        
        return html
    
    def _count_risk_level(self, analyses: List[Dict[str, Any]], risk_level: str) -> int:
        """Count users at a specific risk level."""
        return sum(1 for analysis in analyses if analysis.get('risk_level') == risk_level)
    
    def _calculate_average_score(self, analyses: List[Dict[str, Any]]) -> float:
        """Calculate average burnout score across all users."""
        if not analyses:
            return 0.0
        scores = [analysis.get('burnout_score', 0) for analysis in analyses]
        return round(sum(scores) / len(scores), 2)


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