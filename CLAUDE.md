# Rootly Burnout Detector - GitHub Integration Plan

## Overview
This document outlines the plan for integrating GitHub activity data into the Rootly Burnout Detector to provide a more comprehensive view of engineer burnout by combining incident response patterns with code contribution patterns.

## Current State
- The burnout detector analyzes Rootly incident data using Maslach's Burnout Assessment model
- It tracks emotional exhaustion, depersonalization, and personal accomplishment
- Currently only uses incident response data from Rootly

## GitHub Integration Goals
1. Track code contribution patterns that indicate burnout
2. Correlate incident load with development workload
3. Identify after-hours coding patterns
4. Monitor collaboration health through PR reviews
5. Detect context switching and cognitive overload

## Implementation Plan

### Phase 1: User Correlation
**Goal**: Match Rootly users with their GitHub accounts

**Approach**:
1. **Organization Member Discovery**: Query both GitHub orgs (Rootly-AI-Labs, rootlyhq) for members
2. **Email Mining from Commits**: Search commit history to find all emails used by each GitHub user
3. **Multi-Email Matching**: Match Rootly email against all discovered GitHub user emails
4. **Manual Mapping Fallback**: Use config.json for any remaining unmapped users

**Implementation**:
- Create `src/github_correlator.py` with multi-email discovery
- Mine commits across both organizations for email addresses
- Build email mapping: rootly_email → [github_emails] → github_username
- Only include users who exist in Rootly (ignore GitHub-only contractors)
- Cache successful mappings to reduce API calls

### Phase 2: GitHub Data Collection
**Goal**: Collect relevant GitHub activity metrics

**Scope**:
- Organizations: `Rootly-AI-Labs` and `rootlyhq`
- Time window: Same 30-day period as incident data
- Focus: Correlation between incidents and GitHub activity

**Metrics to Track**:
- Commit frequency and timing (9-5 vs after-hours)
- PR creation and review turnaround times
- Code complexity (lines changed, files touched)
- Repository context switching between orgs
- Issue assignment and resolution patterns
- Review quality (comment depth, engagement)
- **Post-incident activity**: Changes in commit patterns after incidents

**Implementation**:
- Create `src/github_collector.py` extending the collector pattern
- Use GitHub REST API v3 with Personal Access Token
- Implement caching to avoid rate limits on repeated runs
- Store GitHub token in `secrets.env` file
- Separate command flag: `--include-github`

### Phase 3: Enhanced Burnout Analysis
**Goal**: Incorporate GitHub metrics into burnout scoring

**Scoring Weights**:
- Incident response: 70% (primary indicator)
- GitHub activity: 30% (supporting indicator)

**New Burnout Indicators**:

**Emotional Exhaustion**:
- After-hours commits (9-5 business hours)
- Commit clustering (multiple commits in short timeframes)
- Weekend coding activity
- Total lines of code changed (velocity indicator)
- **Post-incident commits**: Rushed fixes after incidents

**Depersonalization**:
- Declining PR review quality (shorter reviews, less feedback)
- Reduced collaboration (solo work vs team PRs)
- Decreased participation in discussions
- Response time to review requests increasing

**Personal Accomplishment**:
- PR acceptance rates
- **Activity Type Weighting**:
  - Bug fixes/hotfixes: Higher exhaustion weight
  - Features/improvements: Normal weight
  - Documentation: Positive accomplishment indicator
- Knowledge sharing (PR reviews given, docs contributed)

**Implementation**:
- Extend `BurnoutAnalyzer` class with GitHub metrics
- Weight incident data more heavily than GitHub data
- Track correlation between incidents and subsequent GitHub activity
- Add new risk factors and recommendations specific to code burnout

### Phase 4: Configuration & Setup
**Goal**: Make GitHub integration configurable and optional

**Configuration Options**:
```json
{
  "github_integration": {
    "enabled": false,  // Set to true when using --include-github flag
    "organizations": ["Rootly-AI-Labs", "rootlyhq"],
    "cache_ttl_hours": 24,  // Cache GitHub data for 24 hours
    "user_mappings": {
      // Manual mappings for users that can't be auto-correlated
      "john.doe@rootly.com": "jdoe-github",
      "jane.smith@rootly.com": "janesmith"
    }
  }
}
```

**Token Storage** (in `secrets.env`):
```
ROOTLY_API_TOKEN=your-rootly-token
GITHUB_TOKEN=your-github-pat-token
```

### Phase 5: Testing & Validation
**Goal**: Ensure accurate correlation and meaningful insights

**Testing Strategy**:
1. Unit tests for correlation logic
2. Integration tests with GitHub API
3. Validation of burnout score adjustments
4. Privacy and security review
5. Performance testing with large datasets

## Technical Architecture

### New Components:
```
src/
├── github_correlator.py    # User matching logic
├── github_collector.py     # GitHub API data collection
├── github_analyzer.py      # GitHub-specific burnout metrics
└── integrations/
    └── github_client.py    # GitHub API wrapper
```

### Data Flow:
1. Collect Rootly users and incidents (existing)
2. Correlate users with GitHub accounts
3. Collect GitHub activity for matched users
4. Combine metrics in burnout analysis
5. Generate unified burnout report

## Privacy & Compliance Considerations
- Only collect aggregate metrics, not code content
- Respect GitHub API rate limits (5000/hour for authenticated requests)
- Store GitHub usernames, not personal data
- No opt-out for now (all Rootly users included if found on GitHub)
- Cache GitHub data with 24-hour TTL to minimize API calls
- Only analyze users who exist in both Rootly and GitHub

## Success Metrics
- % of Rootly users successfully matched to GitHub
- Correlation between incident load and code velocity
- Improved early detection of burnout patterns
- More actionable recommendations based on full workload

## Future Enhancements
- Slack integration for communication patterns
- JIRA integration for project workload
- Calendar integration for meeting load
- IDE metrics for focus time analysis

## Implementation Details

### Email Discovery Strategy
Since Rootly emails may not match GitHub signup emails:

1. **Get Organization Members**:
   ```python
   # GET /orgs/Rootly-AI-Labs/members
   # GET /orgs/rootlyhq/members
   ```

2. **Mine Commit Emails**:
   ```python
   # For each member, get recent commits
   # GET /repos/{owner}/{repo}/commits?author={username}
   # Extract all unique emails from commit.author.email
   ```

3. **Build Correlation Map**:
   ```python
   user_email_map = {
       "github_username": ["email1@rootly.com", "personal@gmail.com", ...],
       ...
   }
   ```

### Caching Strategy
- Cache GitHub data indefinitely in `.github_cache/` (gitignored)
- Cache structure: `email_mapping.json`
- No automatic expiration - cache persists until manually refreshed
- Use `--refresh-github-cache` flag to force refresh of cached data

## Commands to Run
When implementing:
```bash
# Run with GitHub integration
python main.py --include-github

# Run with fresh GitHub data (refresh cache)
python main.py --include-github --refresh-github-cache

# Clear GitHub cache manually
python -c "import sys; sys.path.append('src'); from github_correlator import GitHubCorrelator; c=GitHubCorrelator('',{}); c.clear_cache()"

# Run tests
python -m pytest tests/

# Check type safety
mypy src/

# Format code
black src/
```

## test
- test
- test