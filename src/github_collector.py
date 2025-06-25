"""
GitHub data collector for fetching code activity metrics.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import requests
import time

logger = logging.getLogger(__name__)


class GitHubCollector:
    """Collects GitHub activity data for burnout analysis."""
    
    def __init__(self, github_token: str, config: Dict):
        self.token = github_token
        self.headers = {'Authorization': f'token {github_token}'}
        self.config = config
        self.github_config = config.get('github_integration', {})
        self.organizations = self.github_config.get('organizations', ['Rootly-AI-Labs', 'rootlyhq'])
        self.refresh_cache = config.get('_refresh_github_cache', False)
        self.cache_dir = Path('.github_cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Business hours configuration
        self.business_hours = config.get('analysis', {}).get('business_hours', {'start': 9, 'end': 17})
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
    def collect_github_data(self, github_correlations: Dict[str, str], days: int = 30) -> Dict[str, Dict]:
        """
        Collect GitHub activity data for matched users.
        
        Args:
            github_correlations: Dict mapping rootly_email -> github_username
            days: Number of days to analyze
            
        Returns:
            Dict mapping github_username -> activity_data
        """
        logger.info(f"Starting GitHub data collection for {len(github_correlations)} matched users")
        
        # Filter to only matched users
        matched_users = {email: github_user for email, github_user in github_correlations.items() 
                        if github_user is not None}
        
        if not matched_users:
            logger.warning("No matched users found for GitHub data collection")
            return {}
        
        # Set up date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        logger.info(f"Collecting GitHub data from {start_date.date()} to {end_date.date()}")
        
        # Collect data for each user
        github_data = {}
        
        for i, (rootly_email, github_username) in enumerate(matched_users.items(), 1):
            logger.info(f"[{i}/{len(matched_users)}] Collecting data for {github_username}")
            
            try:
                user_data = self._collect_user_activity(
                    github_username, start_date, end_date, rootly_email
                )
                github_data[github_username] = user_data
                
            except Exception as e:
                logger.error(f"Failed to collect data for {github_username}: {e}")
                github_data[github_username] = self._empty_user_data()
        
        logger.info(f"GitHub data collection complete for {len(github_data)} users")
        return github_data
    
    def _collect_user_activity(self, username: str, start_date: datetime, end_date: datetime, rootly_email: str) -> Dict:
        """Collect all activity data for a single user."""
        
        # Check cache first
        cache_file = self.cache_dir / f"activity_{username}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json"
        
        if cache_file.exists() and not self.refresh_cache:
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    logger.debug(f"Loaded cached GitHub data for {username}")
                    return cached_data
            except Exception as e:
                logger.warning(f"Failed to load cache for {username}: {e}")
        
        # Collect fresh data
        user_data = {
            'username': username,
            'rootly_email': rootly_email,
            'analysis_period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': (end_date - start_date).days
            },
            'commits': [],
            'pull_requests': [],
            'reviews': [],
            'issues': [],
            'metrics': {}
        }
        
        # Collect commits
        commits = self._get_user_commits(username, start_date, end_date)
        user_data['commits'] = commits
        
        # Collect pull requests
        pull_requests = self._get_user_pull_requests(username, start_date, end_date)
        user_data['pull_requests'] = pull_requests
        
        # Collect PR reviews
        reviews = self._get_user_reviews(username, start_date, end_date)
        user_data['reviews'] = reviews
        
        # Collect assigned issues
        issues = self._get_user_issues(username, start_date, end_date)
        user_data['issues'] = issues
        
        # Calculate metrics
        user_data['metrics'] = self._calculate_metrics(user_data)
        
        # Cache the results
        try:
            with open(cache_file, 'w') as f:
                json.dump(user_data, f, indent=2)
            logger.debug(f"Cached GitHub data for {username}")
        except Exception as e:
            logger.warning(f"Failed to cache data for {username}: {e}")
        
        return user_data
    
    def _get_user_commits(self, username: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get all commits by user using GitHub's search API (much faster)."""
        commits = []
        
        # Search each organization separately to avoid complex query issues
        for org in self.organizations:
            org_query = f'author:{username} org:{org} committer-date:{start_date.strftime("%Y-%m-%d")}..{end_date.strftime("%Y-%m-%d")}'
            
            self._rate_limit()
            
            try:
                response = requests.get(
                    'https://api.github.com/search/commits',
                    headers={**self.headers, 'Accept': 'application/vnd.github.cloak-preview'},
                    params={'q': org_query, 'per_page': 100, 'sort': 'committer-date', 'order': 'asc'}
                )
                
                if response.status_code != 200:
                    logger.warning(f"Failed to search commits for {username} in {org}: {response.status_code}")
                    continue
                
                data = response.json()
                
                for commit_item in data.get('items', []):
                    commit = commit_item['commit']
                    repo_name = commit_item['repository']['full_name']
                    
                    commit_data = {
                        'sha': commit_item['sha'],
                        'date': commit['author']['date'],
                        'message': commit['message'],
                        'repository': repo_name,
                        'additions': 0,  # Search API doesn't include stats
                        'deletions': 0,
                        'changed_files': 0
                    }
                    
                    # Parse date and check if it's in business hours
                    commit_dt = datetime.fromisoformat(commit_data['date'].replace('Z', '+00:00'))
                    commit_data['is_business_hours'] = self._is_business_hours(commit_dt)
                    commit_data['is_weekend'] = commit_dt.weekday() >= 5
                    
                    commits.append(commit_data)
                    
            except Exception as e:
                logger.error(f"Error searching commits for {username} in {org}: {e}")
        
        return commits
    
    def _get_user_pull_requests(self, username: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get pull requests created by user using search API."""
        pull_requests = []
        
        # Search each organization separately
        for org in self.organizations:
            query = f'author:{username} type:pr org:{org} created:{start_date.strftime("%Y-%m-%d")}..{end_date.strftime("%Y-%m-%d")}'
            
            self._rate_limit()
            
            try:
                response = requests.get(
                    'https://api.github.com/search/issues',
                    headers=self.headers,
                    params={'q': query, 'per_page': 100}
                )
                
                if response.status_code != 200:
                    logger.warning(f"Failed to search PRs for {username} in {org}: {response.status_code}")
                    continue
                
                data = response.json()
                
                for pr in data.get('items', []):
                    pr_data = {
                        'number': pr['number'],
                        'title': pr['title'],
                        'state': pr['state'],
                        'created_at': pr['created_at'],
                        'updated_at': pr['updated_at'],
                        'closed_at': pr['closed_at'],
                        'repository': pr['repository_url'].split('/')[-1],
                        'labels': [label['name'] for label in pr.get('labels', [])],
                        'draft': pr.get('draft', False)
                    }
                    
                    # Parse date and check business hours
                    created_dt = datetime.fromisoformat(pr_data['created_at'].replace('Z', '+00:00'))
                    pr_data['is_business_hours'] = self._is_business_hours(created_dt)
                    pr_data['is_weekend'] = created_dt.weekday() >= 5
                    
                    pull_requests.append(pr_data)
                    
            except Exception as e:
                logger.error(f"Error searching PRs for {username} in {org}: {e}")
        
        return pull_requests
    
    def _get_user_reviews(self, username: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get PR reviews by user."""
        reviews = []
        
        # Note: GitHub search API doesn't support searching reviews directly
        # Reviews would need to be collected via PR endpoints for specific repositories
        # For now, return empty list to avoid errors
        logger.debug(f"Review collection not implemented for {username}")
        
        return reviews
    
    def _get_user_issues(self, username: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get issues assigned to user using search API."""
        issues = []
        
        # Search each organization separately
        for org in self.organizations:
            query = f'assignee:{username} type:issue org:{org} created:{start_date.strftime("%Y-%m-%d")}..{end_date.strftime("%Y-%m-%d")}'
            
            self._rate_limit()
            
            try:
                response = requests.get(
                    'https://api.github.com/search/issues',
                    headers=self.headers,
                    params={'q': query, 'per_page': 100}
                )
                
                if response.status_code != 200:
                    logger.warning(f"Failed to search issues for {username} in {org}: {response.status_code}")
                    continue
                
                data = response.json()
                
                for issue in data.get('items', []):
                    issue_data = {
                        'number': issue['number'],
                        'title': issue['title'],
                        'state': issue['state'],
                        'created_at': issue['created_at'],
                        'updated_at': issue['updated_at'],
                        'closed_at': issue['closed_at'],
                        'repository': issue['repository_url'].split('/')[-1],
                        'labels': [label['name'] for label in issue.get('labels', [])],
                    }
                    
                    issues.append(issue_data)
                    
            except Exception as e:
                logger.error(f"Error searching issues for {username} in {org}: {e}")
        
        return issues
    
    
    def _calculate_metrics(self, user_data: Dict) -> Dict:
        """Calculate burnout-relevant metrics from GitHub activity."""
        commits = user_data['commits']
        pull_requests = user_data['pull_requests']
        issues = user_data['issues']
        
        # Basic counts
        total_commits = len(commits)
        total_prs = len(pull_requests)
        total_issues = len(issues)
        
        # Time-based analysis
        after_hours_commits = len([c for c in commits if not c['is_business_hours']])
        weekend_commits = len([c for c in commits if c['is_weekend']])
        after_hours_prs = len([pr for pr in pull_requests if not pr['is_business_hours']])
        
        # Patterns
        repositories_touched = len(set(c['repository'] for c in commits))
        
        # Calculate percentages
        after_hours_commit_percentage = (after_hours_commits / total_commits) if total_commits > 0 else 0
        after_hours_pr_percentage = (after_hours_prs / total_prs) if total_prs > 0 else 0
        weekend_commit_percentage = (weekend_commits / total_commits) if total_commits > 0 else 0
        
        # Commit clustering (commits within 4 hours of each other)
        clustered_commits = self._detect_commit_clustering(commits)
        
        # Weekly averages
        days_analyzed = user_data['analysis_period']['days']
        weeks = days_analyzed / 7.0
        
        metrics = {
            'total_commits': total_commits,
            'total_pull_requests': total_prs,
            'total_issues': total_issues,
            'commits_per_week': total_commits / weeks if weeks > 0 else 0,
            'prs_per_week': total_prs / weeks if weeks > 0 else 0,
            'after_hours_commits': after_hours_commits,
            'after_hours_commit_percentage': after_hours_commit_percentage,
            'weekend_commits': weekend_commits,
            'weekend_commit_percentage': weekend_commit_percentage,
            'after_hours_prs': after_hours_prs,
            'after_hours_pr_percentage': after_hours_pr_percentage,
            'repositories_touched': repositories_touched,
            'clustered_commits': clustered_commits,
            'avg_commits_per_day': total_commits / days_analyzed if days_analyzed > 0 else 0,
        }
        
        return metrics
    
    def _detect_commit_clustering(self, commits: List[Dict]) -> int:
        """Detect commits that are clustered within 4 hours of each other."""
        if len(commits) < 2:
            return 0
        
        clustered = 0
        cluster_window = timedelta(hours=4)
        
        for i in range(1, len(commits)):
            current_time = datetime.fromisoformat(commits[i]['date'].replace('Z', '+00:00'))
            previous_time = datetime.fromisoformat(commits[i-1]['date'].replace('Z', '+00:00'))
            
            if current_time - previous_time <= cluster_window:
                clustered += 1
        
        return clustered
    
    def _is_business_hours(self, dt: datetime) -> bool:
        """Check if datetime is within business hours (assumes UTC for simplicity)."""
        # Convert to local time (this is simplified - in reality we'd want user timezone)
        hour = dt.hour
        is_weekday = dt.weekday() < 5
        
        return (is_weekday and 
                self.business_hours['start'] <= hour < self.business_hours['end'])
    
    def _rate_limit(self):
        """Simple rate limiting to avoid hitting GitHub API limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    def _empty_user_data(self) -> Dict:
        """Return empty user data structure."""
        return {
            'username': '',
            'rootly_email': '',
            'commits': [],
            'pull_requests': [],
            'reviews': [],
            'issues': [],
            'metrics': {
                'total_commits': 0,
                'total_pull_requests': 0,
                'total_issues': 0,
                'commits_per_week': 0,
                'prs_per_week': 0,
                'after_hours_commits': 0,
                'after_hours_commit_percentage': 0,
                'weekend_commits': 0,
                'weekend_commit_percentage': 0,
                'after_hours_prs': 0,
                'after_hours_pr_percentage': 0,
                'repositories_touched': 0,
                'clustered_commits': 0,
                'avg_commits_per_day': 0,
            }
        }