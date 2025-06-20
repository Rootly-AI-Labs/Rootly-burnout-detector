"""
Vercel Serverless Function for Burnout Analysis
Endpoint: /api/analyze?days=30
"""

from http.server import BaseHTTPRequestHandler
import json
import asyncio
import os
from urllib.parse import parse_qs, urlparse
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import our detector
sys.path.append(str(Path(__file__).parent.parent))

from vercel_burnout_detector import VercelBurnoutDetector
        


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Parse query parameters
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            # Get days parameter, default to 30
            days = int(query_params.get('days', ['30'])[0])
            
            # Validate days parameter
            if days < 1 or days > 365:
                days = 30
            
            # Run comprehensive analysis
            detector = VercelBurnoutDetector()
            result = asyncio.run(detector.run_analysis(days))
            
            # Set response headers
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            # Send response
            response_json = json.dumps(result, indent=2)
            self.wfile.write(response_json.encode('utf-8'))
            
        except ValueError as e:
            self._send_error(400, f"Invalid parameter: {str(e)}")
        except Exception as e:
            self._send_error(500, f"Internal server error: {str(e)}")
    
    def do_OPTIONS(self):
        # Handle CORS preflight requests
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _send_error(self, status_code, message):
        """Send error response in JSON format."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        error_response = {
            "error": True,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        self.wfile.write(json.dumps(error_response).encode('utf-8'))