# Rootly Burnout Detector

A data-driven burnout detection system for on-call engineers using Rootly's incident data and Christina Maslach's Burnout Inventory research.

## Quick Start

1. **Setup Environment**
   ```bash
   pip install -r requirements.txt
   export ROOTLY_API_TOKEN="your-rootly-api-token"
   ```

2. **Configure Analysis**
   ```bash
   cp config/config.example.json config/config.json
   # Edit config.json with your thresholds
   ```

3. **Run Analysis**
   ```bash
   python main.py --days 30
   ```

4. **View Results**
   ```bash
   open output/dashboard.html
   ```

## Project Structure

```
rootly-burnout-detector/
├── config/
│   ├── config.json           # Analysis configuration
│   └── config.example.json   # Example configuration
├── src/
│   ├── mcp_client.py         # MCP server connection
│   ├── data_collector.py     # Data extraction from Rootly
│   ├── burnout_analyzer.py   # Risk calculation engine
│   └── dashboard.py          # HTML report generation
├── output/
│   ├── burnout_data.json     # Analysis results
│   └── dashboard.html        # Interactive dashboard
├── tests/
│   └── test_*.py            # Unit tests
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

Edit `config/config.json` to adjust:
- Analysis time period (default: 30 days)
- Burnout risk thresholds
- Business hours definition
- Severity weights
- Output options

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

## Requirements

- Python 3.12+
- Access to Rootly MCP server
- Rootly API token