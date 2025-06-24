# Rootly Burnout Detector

A data-driven burnout detection system for on-call engineers using Rootly's incident data and Christina Maslach's Burnout Inventory research. The system connects to Rootly via the [Model Context Protocol (MCP)](https://github.com/Rootly-AI-Labs/Rootly-MCP-server/tree/main), enabling secure and efficient data retrieval.

## Requirements

- Python 3.12+
- Rootly API token
- [rootly-mcp-server](https://github.com/Rootly-AI-Labs/Rootly-MCP-server/tree/main) (for local mode)

## Quick Start

1. **Setup Environment**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Rootly API Token**
   ```bash
   cp secrets.env.example secrets.env
   # Edit secrets.env with your token
   ```

3. **Install Local MCP Server**
   ```bash
   pip install rootly-mcp-server
   ```

4. **Run Analysis**
   
   **Option A: Local MCP Server (Recommended)**
   ```bash
   python main.py --config config/config.local-pip.json --days 30
   ```
   
   **Option B: uvx MCP Server (Remote)**
   ```bash
   python main.py --days 30
   ```

5. **Interactive Mode (Optional)**
   ```bash
   # Set LLM API key for Q&A mode
   export OPENAI_API_KEY="your-openai-key"  # or ANTHROPIC_API_KEY, HF_TOKEN
   python main.py --config config/config.local-pip.json --days 30 --interactive
   ```

6. **View Results**
   ```bash
   open output/dashboard.html
   ```

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

## Configuration

### Token Management

Add your Rootly API token to the `secrets.env` file:
```bash
ROOTLY_API_TOKEN=your-rootly-api-token-here
```

The token can also be provided via environment variable or command line flag if needed.

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

### Local MCP Server (Recommended)
- Faster and more reliable
- Requires `pip install rootly-mcp-server`
- Use: `--config config/config.local-pip.json`

### uvx MCP Server (Remote)
- Uses uvx to connect to remotely hosted MCP server
- Default configuration
- May have parameter compatibility issues