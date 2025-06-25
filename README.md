# Rootly Burnout Detector

A data-driven burnout detection system for on-call engineers using Rootly's incident data and Christina Maslach's Burnout Inventory research. The system connects to Rootly's [MCP Server](https://github.com/Rootly-AI-Labs/Rootly-MCP-server/tree/main), enabling secure and efficient data retrieval.

![Rootly Burnout Analysis Dashboard](dashboard-screenshot.png)

## Requirements

- Python 3.12+
- uv package manager (`brew install uv` or see [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- Rootly API token

## Quick Start

1. **Setup Environment**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Tokens**
   ```bash
   cp secrets.env.example secrets.env
   ```
   
   Edit `secrets.env` and add your tokens:
   ```bash
   # Required
   ROOTLY_API_TOKEN=your-rootly-api-token-here
   
   # Optional - for GitHub integration
   GITHUB_TOKEN=ghp_your-github-personal-access-token
   
   # Optional - for interactive Q&A mode (add one)
   OPENAI_API_KEY=sk-your-openai-key-here      # GPT-4
   ANTHROPIC_API_KEY=sk-ant-your-anthropic-key # Claude
   HF_TOKEN=hf_your-huggingface-token          # Hugging Face (free)
   ```

3. **Run Analysis**
   ```bash
   # Standard analysis (incident data only)
   python main.py --days 30
   
   # Enhanced analysis with GitHub activity data
   python main.py --include-github --days 30
   ```

4. **Interactive Mode (Optional)**
   ```bash
   # Requires LLM API key configured in step 2
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

## GitHub Integration

The Rootly Burnout Detector can integrate GitHub activity data to provide a more comprehensive burnout assessment by analyzing both incident response patterns and coding work patterns.

### Setup GitHub Integration

1. **Create GitHub Personal Access Token**
   - Go to GitHub Settings → Developer Settings → Personal Access Tokens → Tokens (classic)
   - Generate a new token with these scopes:
     - `repo` (for private repositories)
     - `public_repo` (for public repositories)
     - `user:email` (for email correlation)

2. **Configure Token**
   ```bash
   # Add to secrets.env
   GITHUB_TOKEN=ghp_your-github-personal-access-token
   ```

3. **Configure Organizations**
   
   Edit `config/config.json` to specify your GitHub organizations:
   ```json
   {
     "github_integration": {
       "enabled": false,
       "organizations": ["your-org-1", "your-org-2"],
       "user_mappings": {
         "engineer@company.com": "github-username"
       }
     }
   }
   ```

### Usage

```bash
# Include GitHub data in burnout analysis
python main.py --include-github --days 30

# Refresh GitHub cache (forces new API calls)
python main.py --include-github --refresh-github-cache --days 30

# Standard analysis without GitHub data
python main.py --days 30
```

### How It Works

1. **User Correlation**: Automatically correlates Rootly users with GitHub accounts by:
   - Mining commit history for email addresses
   - Matching email patterns and usernames
   - Using manual mappings from configuration

2. **Activity Collection**: Gathers 30 days of GitHub activity:
   - Commits (with timestamp and repository info)
   - Pull requests (creation and collaboration patterns)
   - Issues (assignment and resolution)

3. **Burnout Analysis Integration**: Enhances the three Maslach dimensions:

   **Emotional Exhaustion** (+30% GitHub weight):
   - After-hours commits percentage
   - Weekend coding activity  
   - Commit clustering (rapid consecutive commits indicating stress)

   **Depersonalization** (+30% GitHub weight):
   - Repository switching patterns (scattered focus)
   - Pull request collaboration rates
   - Code review participation

   **Personal Accomplishment** (+30% GitHub weight):
   - Productive commit frequency (sweet spot: 3-8 commits/week)
   - Pull request creation rates
   - Repository contribution diversity

### Caching & Performance

- **Indefinite Caching**: GitHub data is cached in `.github_cache/` directory
- **Fast Subsequent Runs**: Uses cached data unless `--refresh-github-cache` is specified
- **Optimized API Usage**: Searches user activity directly instead of scanning repositories
- **Rate Limit Friendly**: Respects GitHub API limits (5000 requests/hour)

### User Correlation

The system automatically discovers user correlations by:
1. **Email Mining**: Extracts email addresses from commit history across organizations
2. **Pattern Matching**: Matches usernames and email patterns
3. **Manual Mappings**: Supports explicit user mappings in config for improved accuracy

Example correlation output:
```
✅ GitHub correlation: 15/40 users matched (37.5%)
📝 Add 25 users to config.json user_mappings for better coverage
```

### Benefits

- **Holistic View**: Combines incident stress with coding work patterns
- **Early Detection**: Identifies burnout patterns that incident data alone might miss
- **Work-Life Balance**: Detects after-hours and weekend work patterns
- **Productivity Insights**: Understands sustainable vs. excessive coding activity
- **Collaboration Patterns**: Identifies social withdrawal through reduced PR/review activity

### Data Storage

GitHub data is stored in:
- **Cache**: `.github_cache/activity_{username}_{dates}.json` (gitignored)
- **Analysis Results**: Integrated into `output/burnout_analysis.json`
- **Correlation Data**: Email mappings cached for fast subsequent runs

## Project Structure

```
rootly-burnout-detector/
├── config/
│   ├── config.json           # Default configuration
│   └── config.example.json   # Example configuration
├── src/
│   ├── mcp_client.py         # MCP server connection
│   ├── data_collector.py     # Data extraction from Rootly
│   ├── burnout_analyzer.py   # Risk calculation engine (with GitHub integration)
│   ├── dashboard.py          # HTML report generation
│   ├── github_correlator.py  # User correlation between Rootly and GitHub
│   ├── github_collector.py   # GitHub activity data collection
│   ├── interactive_analyzer.py # LLM-powered Q&A interface
│   └── burnout_tools.py      # Custom smolagents tools
├── output/
│   ├── burnout_analysis.json # Analysis results (includes GitHub data)
│   ├── dashboard.html        # Interactive dashboard
│   ├── summary_report.txt    # Text summary
│   └── individual_reports/   # Per-user detailed reports
├── .github_cache/            # GitHub data cache (git-ignored)
│   ├── activity_*.json       # Cached user activity data
│   └── email_mapping.json    # User correlation cache
├── secrets.env               # API tokens (git-ignored)
├── secrets.env.example       # Example secrets file
├── requirements.txt          # Python dependencies
└── main.py                  # Entry point
```

## Features

- **Timezone-aware after-hours detection** (9 AM - 5 PM per engineer's timezone)
- **Maslach Burnout Inventory inspired scoring** (Emotional Exhaustion, Depersonalization, Personal Accomplishment)
- **GitHub Integration** (optional) - Combines incident data with coding activity patterns
- **Automatic user correlation** between Rootly and GitHub accounts
- **Individual and team-level analysis**
- **Configurable thresholds and parameters**
- **Interactive HTML dashboard**
- **JSON export for further analysis**
- **Intelligent caching** for fast subsequent analysis runs


## Burnout Metrics

### Emotional Exhaustion Indicators
**Incident Data:**
- High incident frequency
- Extended incident durations  
- Frequent after-hours responses
- Short recovery time between incidents

**GitHub Data** (when `--include-github` is used):
- After-hours commits percentage
- Weekend coding activity
- Commit clustering (rapid consecutive commits)

### Depersonalization Indicators
**Incident Data:**
- Decreased collaboration
- Increased escalation rates
- Reduced post-incident participation

**GitHub Data** (when `--include-github` is used):
- Repository switching patterns (scattered focus)
- Reduced pull request creation
- Lower code review participation

### Personal Accomplishment Indicators
**Incident Data:**
- Resolution success rates
- Time to resolution improvements
- Knowledge sharing participation

**GitHub Data** (when `--include-github` is used):
- Productive commit frequency (optimal: 3-8 commits/week)
- Pull request collaboration rates
- Consistent repository contributions

## Output

- **Individual Risk Scores**: Per-engineer burnout risk (0-10 scale)
- **Team Aggregations**: Department/team level insights
- **Trend Analysis**: Changes over time
- **Actionable Recommendations**: Suggested interventions

## MCP Server

The tool uses uvx to automatically download and run the Rootly MCP server:

- **Automatic setup**: No manual installation required
- **Always latest**: Gets the most recent version automatically  
- **Clean environment**: Uses temporary isolated environment
- **No conflicts**: Doesn't interfere with your Python packages

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

**Standard Analysis** (incident data only):
```
Burnout Score = (Emotional Exhaustion × 0.4) + (Depersonalization × 0.3) + ((10 - Personal Accomplishment) × 0.3)
```

**Enhanced Analysis** (with `--include-github`):
```
Each Dimension = (Incident Component × 0.7) + (GitHub Component × 0.3)
Burnout Score = (Emotional Exhaustion × 0.4) + (Depersonalization × 0.3) + ((10 - Personal Accomplishment) × 0.3)
```

**Score Ranges:**
- **0-3.9**: Low risk - Healthy engagement levels
- **4.0-6.9**: Medium risk - Early warning signs, intervention recommended
- **7.0-10**: High risk - Immediate action needed

The scoring system identifies early burnout indicators through incident response patterns, enabling proactive interventions before burnout becomes severe.