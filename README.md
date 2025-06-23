# Rootly Burnout Detector

A data-driven burnout detection system for on-call engineers using Rootly's incident data and Christina Maslach's Burnout Inventory research.

## Quick Start

1. **Setup Environment**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Rootly API Token** (choose one method):
   
   **Option A: Environment Variable (Recommended)**
   ```bash
   export ROOTLY_API_TOKEN="your-rootly-api-token"
   ```
   
   **Option B: secrets.env File (Secure)**
   ```bash
   cp secrets.env.example secrets.env
   # Edit secrets.env with your token
   ```
   
   **Option C: Command Line**
   ```bash
   python main.py --token "your-rootly-api-token" --days 30
   ```

3. **Configure Analysis**
   ```bash
   cp config/config.example.json config/config.json
   # Edit config.json with your thresholds
   ```

4. **Run Analysis**
   ```bash
   python main.py --days 30
   ```

5. **Interactive Mode (Optional)**
   ```bash
   # Set LLM API key for Q&A mode
   export OPENAI_API_KEY="your-openai-key"  # or ANTHROPIC_API_KEY, HF_TOKEN
   python main.py --days 30 --interactive
   ```

6. **View Results**
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

### Token Management

**Security Levels (Best → Worst):**
1. **Environment Variable** - Most secure, not stored in files
2. **secrets.env File** - Git-ignored, team-friendly
3. **Command Line** - Convenient but visible in process lists

**Token Precedence:**
1. `--token` command line flag (highest priority)
2. `ROOTLY_API_TOKEN` environment variable  
3. `secrets.env` file
4. `.env` file (lowest priority)

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

## Requirements

- Python 3.12+
- Access to Rootly MCP server
- Rootly API token