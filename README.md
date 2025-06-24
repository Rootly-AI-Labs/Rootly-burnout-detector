# Rootly Burnout Detector

A data-driven burnout detection system for on-call engineers using Rootly's incident data and Christina Maslach's Burnout Inventory research. The system connects to Rootly's [MCP Server](https://github.com/Rootly-AI-Labs/Rootly-MCP-server/tree/main), enabling secure and efficient data retrieval.

## Requirements

- Python 3.12+
- Rootly API token

## Quick Start

1. **Setup Environment**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Rootly API Token**
   ```bash
   cp secrets.env.example secrets.env
   ```
   
   Edit `secrets.env` and add your Rootly API token:
   ```bash
   ROOTLY_API_TOKEN=your-rootly-api-token-here
   ```

3. **Run Analysis**
   
   **Remote MCP Server (Recommended)**
   ```bash
   python main.py --days 30
   ```
   
   **Local MCP Server (Optional)**
   ```bash
   # Install local server first
   pip install rootly-mcp-server
   python main.py --config config/config.local-pip.json --days 30
   ```

4. **Interactive Mode (Optional)**
   ```bash
   # Set LLM API key for Q&A mode
   export OPENAI_API_KEY="your-openai-key"  # or ANTHROPIC_API_KEY, HF_TOKEN
   python main.py --days 30 --interactive
   ```

5. **View Results**
   ```bash
   open output/dashboard.html
   ```

## Configuration

### Token Management

The Rootly API token is configured in the `secrets.env` file as shown in the Quick Start section above. The token can also be provided via environment variable or command line flag if needed.

### Analysis Settings

Edit `config/config.json` to adjust:
- Analysis time period (default: 30 days)
- Burnout risk thresholds
- Business hours definition
- Severity weights
- Output options

### Interactive Mode

For interactive Q&A mode, set one LLM API key:
- `OPENAI_API_KEY` - GPT-4 (paid, high quality)
- `ANTHROPIC_API_KEY` - Claude (paid, high quality)  
- `HF_TOKEN` - Hugging Face (free tier available)

## Project Structure

```
rootly-burnout-detector/
├── config/
│   ├── config.json           # Default (uvx/remote) configuration
│   ├── config.local-pip.json # Local MCP server configuration
│   └── config.example.json   # Example configuration
├── src/
│   ├── mcp_client.py         # MCP server connection
│   ├── data_collector.py     # Data extraction from Rootly
│   ├── burnout_analyzer.py   # Risk calculation engine
│   ├── dashboard.py          # HTML report generation
│   ├── interactive_analyzer.py # LLM-powered Q&A interface
│   └── burnout_tools.py      # Custom smolagents tools
├── output/
│   ├── burnout_analysis.json # Analysis results
│   ├── dashboard.html        # Interactive dashboard
│   ├── summary_report.txt    # Text summary
│   └── individual_reports/   # Per-user detailed reports
├── secrets.env               # API tokens (git-ignored)
├── secrets.env.example       # Example secrets file
├── requirements.txt          # Python dependencies
└── main.py                  # Entry point
```

## Features

- **Timezone-aware after-hours detection** (9 AM - 5 PM per engineer's timezone)
- **Maslach Burnout Inventory inspired scoring** (Emotional Exhaustion, Depersonalization, Personal Accomplishment)
- **Individual and team-level analysis**
- **Configurable thresholds and parameters**
- **Interactive HTML dashboard**
- **JSON export for further analysis**


## Burnout Metrics

### Emotional Exhaustion Indicators
- High incident frequency
- Extended incident durations  
- Frequent after-hours responses
- Short recovery time between incidents

### Depersonalization Indicators
- Decreased collaboration
- Increased escalation rates
- Reduced post-incident participation

### Personal Accomplishment Indicators
- Resolution success rates
- Time to resolution improvements
- Knowledge sharing participation

## Output

- **Individual Risk Scores**: Per-engineer burnout risk (0-10 scale)
- **Team Aggregations**: Department/team level insights
- **Trend Analysis**: Changes over time
- **Actionable Recommendations**: Suggested interventions

## MCP Server Options

The tool supports two MCP server configurations:

### Remote MCP Server (Recommended)
- Uses uvx to connect to remotely hosted MCP server
- Default configuration
- No additional installation required

### Local MCP Server (Optional)
- Faster and more reliable for heavy usage
- Requires `pip install rootly-mcp-server`
- Use: `--config config/config.local-pip.json`

## How Burnout Scores Are Calculated

This tool uses **Christina Maslach's Burnout Assessment Inventory**, adapted for on-call engineering work. The system analyzes three dimensions:

### 1. **Emotional Exhaustion (40% weight)**
Measures physical and emotional depletion from work demands:
- Incident frequency relative to team norms
- After-hours work percentage  
- Average incident resolution time
- Incident clustering (multiple incidents within 4 hours)

### 2. **Depersonalization (30% weight)**  
Measures cynicism and detachment from work:
- Escalation frequency (inability to resolve alone)
- Solo incident handling rate
- Response time trends (are you getting slower to respond over time?)
- Communication quality (resolution message length)

### 3. **Personal Accomplishment (30% weight, inverted)**
Measures sense of achievement and competence:
- Incident resolution success rate
- Resolution time improvement trends
- Handling of complex/high-severity incidents  
- Knowledge sharing and documentation quality

### Overall Score
```
Burnout Score = (Emotional Exhaustion × 0.4) + (Depersonalization × 0.3) + ((10 - Personal Accomplishment) × 0.3)
```

**Score Ranges:**
- **0-3.9**: Low risk - Healthy engagement levels
- **4.0-6.9**: Medium risk - Early warning signs, intervention recommended
- **7.0-10**: High risk - Immediate action needed

The scoring system identifies early burnout indicators through incident response patterns, enabling proactive interventions before burnout becomes severe.