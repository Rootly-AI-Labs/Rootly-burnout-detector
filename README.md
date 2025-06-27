# Rootly Burnout Detector

A comprehensive burnout detection system for on-call engineers using Rootly's incident data, enhanced with GitHub coding patterns and Slack communication analysis. Built on Christina Maslach's Burnout Inventory research and connects to Rootly's [MCP Server](https://github.com/Rootly-AI-Labs/Rootly-MCP-server/tree/main).

![Rootly Burnout Analysis Dashboard](dashboard-screenshot.png)

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Tokens**
   ```bash
   cp secrets.env.example secrets.env
   # Edit secrets.env with your tokens
   ```

3. **Run Analysis**
   ```bash
   # Standard analysis (incident data only)
   python main.py --days 30
   
   # Enhanced analysis with all integrations
   python main.py --include-github --include-slack --days 30
   ```

4. **View Results**
   ```bash
   open output/dashboard.html
   ```

## Configuration

### Required Setup

Edit `secrets.env`:
```bash
# Required
ROOTLY_API_TOKEN=your-rootly-api-token-here

# Optional integrations
GITHUB_TOKEN=ghp_your-github-personal-access-token
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token

# Optional - for interactive Q&A mode
OPENAI_API_KEY=sk-your-openai-key-here      # GPT-4
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key # Claude  
HF_TOKEN=hf_your-huggingface-token          # Hugging Face (free)
```

### Analysis Settings

Edit `config/config.json` to adjust:
- Analysis time period and thresholds
- GitHub organizations to analyze
- Slack user mappings
- Business hours and severity weights

## Features

### Core Analysis
- **Maslach Burnout Inventory** - Three-dimensional scoring system
- **Timezone-aware** after-hours detection (9 AM - 5 PM per timezone)
- **Individual and team-level** risk assessment
- **Interactive HTML dashboard** with detailed metrics
- **Configurable thresholds** and scoring parameters

### GitHub Integration (Optional)
Analyzes coding patterns to detect burnout indicators:

**Setup:**
1. Create GitHub Personal Access Token with `repo`, `public_repo`, `user:email` scopes
2. Add `GITHUB_TOKEN` to `secrets.env`
3. Configure organizations in `config.json`

**Usage:**
```bash
python main.py --include-github --days 30
```

**Metrics:**
- After-hours and weekend coding activity
- Commit clustering patterns (stress indicators)
- Repository context switching
- Pull request collaboration rates
- Productive coding frequency

### Slack Integration (Optional)
Analyzes communication patterns for early burnout detection:

**Setup:**
1. Create Slack App with bot permissions: `channels:read`, `channels:history`, `users:read`, `users:read.email`
2. Install to workspace and copy Bot Token
3. Add `SLACK_BOT_TOKEN` to `secrets.env`
4. Invite bot to channels: `/invite @YourBot`

**Usage:**
```bash
python main.py --include-slack --days 30
```

**Metrics:**
- Message timing and volume patterns
- After-hours communication indicators
- Thread participation and collaboration
- Sentiment analysis with VADER
- Stress keyword detection

### Interactive Mode (Optional)
LLM-powered Q&A interface for deeper analysis:

```bash
python main.py --days 30 --interactive
```

Requires one of: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `HF_TOKEN`

## Burnout Scoring System

Based on **Maslach's Burnout Assessment Inventory** with three dimensions:

> 📖 **[Detailed Calculation Methodology →](docs/burnout-calculation.md)**

### 1. Emotional Exhaustion (40% weight)
- **Incident Data**: Frequency, after-hours work, resolution time, clustering
- **GitHub Data**: After-hours commits, weekend coding, commit bursts
- **Slack Data**: Message volume, after-hours communication, stress indicators

### 2. Depersonalization (30% weight)
- **Incident Data**: Escalation rates, solo work, communication quality
- **GitHub Data**: Repository switching, reduced collaboration
- **Slack Data**: Thread participation, private messaging patterns

### 3. Personal Accomplishment (30% weight, inverted)
- **Incident Data**: Resolution success, improvement trends, knowledge sharing
- **GitHub Data**: Productive commit frequency, PR collaboration
- **Slack Data**: Healthy communication patterns, consistent presence

### Scoring Formula

**Standard Analysis:**
```
Burnout Score = (Emotional Exhaustion × 0.4) + (Depersonalization × 0.3) + ((10 - Personal Accomplishment) × 0.3)
```

**Enhanced Analysis (with integrations):**
```
Each Dimension = (Incident Component × 70%) + (GitHub Component × 15%) + (Slack Component × 15%)
```

**Risk Levels:**
- **0-3.9**: Low risk - Healthy engagement
- **4.0-6.9**: Medium risk - Early warning signs
- **7.0-10**: High risk - Immediate intervention needed

## Command Line Options

```bash
# Core options
python main.py --days 30                    # Standard analysis
python main.py --config custom.json        # Custom configuration

# Integration options  
python main.py --include-github             # Add GitHub analysis
python main.py --include-slack              # Add Slack analysis
python main.py --include-github --include-slack  # Full analysis

# Cache management
python main.py --refresh-github-cache       # Force GitHub data refresh
python main.py --refresh-slack-cache        # Force Slack data refresh

# Advanced options
python main.py --interactive                # Enable Q&A mode
python main.py --output-dir custom/         # Custom output directory
```

## Project Structure

```
rootly-burnout-detector/
├── config/
│   └── config.json              # Configuration settings
├── src/
│   ├── mcp_client.py           # MCP server connection
│   ├── data_collector.py       # Rootly data extraction  
│   ├── burnout_analyzer.py     # Risk calculation engine
│   ├── dashboard.py            # HTML dashboard generation
│   ├── github_correlator.py    # GitHub user correlation
│   ├── github_collector.py     # GitHub activity collection
│   ├── slack_analyzer.py       # Slack pattern analysis
│   ├── slack_collector.py      # Slack data collection
│   └── interactive_analyzer.py # LLM Q&A interface
├── output/
│   ├── burnout_analysis.json   # Complete analysis results
│   ├── dashboard.html          # Interactive dashboard
│   └── summary_report.txt      # Executive summary
├── .github_cache/              # GitHub data cache (git-ignored)
├── .slack_cache/               # Slack data cache (git-ignored)
├── secrets.env                 # API tokens (git-ignored)
└── main.py                     # Entry point
```

## Output Files

- **`dashboard.html`** - Interactive dashboard with charts and user details
- **`burnout_analysis.json`** - Complete analysis data in JSON format
- **`summary_report.txt`** - Executive summary with key metrics
- **`individual_reports/`** - Detailed per-user analysis reports

## Performance & Caching

- **Smart Caching**: GitHub and Slack data cached locally for fast re-runs
- **Rate Limit Friendly**: Respects API limits across all integrations
- **Optimized Queries**: Direct user activity searches, not repository scanning
- **Cache Management**: Use `--refresh-*-cache` flags to update data

## Requirements

- Python 3.12+
- uv package manager (`brew install uv`)
- Rootly API token
- Optional: GitHub Personal Access Token
- Optional: Slack Bot Token
- Optional: LLM API key (OpenAI, Anthropic, or Hugging Face)

## Testing

Mock data generators available for testing without real API access:
```bash
# Generate test Slack conversations
python src/slack_mock_generator.py

# Test with mock mode
python main.py --include-slack --days 30
```

## Privacy & Security

- **Local Processing**: All analysis performed locally
- **No Message Content**: Slack integration analyzes patterns, not message text
- **Aggregate Metrics**: Focuses on timing and behavioral patterns
- **Secure Storage**: API tokens in git-ignored `secrets.env` file
- **Optional Integrations**: All enhanced features are opt-in