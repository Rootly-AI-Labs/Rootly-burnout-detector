"""
GitHub user correlation module for matching Rootly users with GitHub accounts.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
import requests
from functools import lru_cache

logger = logging.getLogger(__name__)


class GitHubCorrelator:
    """Correlates Rootly users with GitHub accounts using multiple strategies."""
    
    def __init__(self, github_token: str, config: Dict):
        self.token = github_token
        self.headers = {'Authorization': f'token {github_token}'}
        self.config = config
        self.github_config = config.get('github_integration', {})
        self.organizations = self.github_config.get('organizations', ['Rootly-AI-Labs', 'rootlyhq'])
        self.manual_mappings = self.github_config.get('user_mappings', {})
        # Check for refresh flag in config (will be set by main.py)
        self.refresh_cache = config.get('_refresh_github_cache', False)
        self.cache_dir = Path('.github_cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache for API calls during this session
        self._org_members_cache = {}
        self._user_emails_cache = {}
        self._user_names_cache = {}
        
    def correlate_users(self, rootly_users: List[Dict]) -> Dict[str, Optional[str]]:
        """
        Correlate Rootly users with GitHub accounts.
        
        Returns:
            Dict mapping rootly_email -> github_username (or None if not found)
        """
        logger.info(f"Starting user correlation for {len(rootly_users)} Rootly users")
        
        # First, get all GitHub users from both organizations
        github_users = self._get_all_github_users()
        logger.info(f"Found {len(github_users)} unique GitHub users across organizations")
        
        # Build email to GitHub username mapping
        email_to_github = self._build_email_mapping(github_users)
        
        # Correlate each Rootly user
        correlations = {}
        unmatched = []
        
        for user in rootly_users:
            rootly_email = user.get('email', '').lower()
            if not rootly_email:
                continue
                
            # Check manual mapping first
            if rootly_email in self.manual_mappings:
                correlations[rootly_email] = self.manual_mappings[rootly_email]
                logger.debug(f"Matched {rootly_email} via manual mapping")
                continue
            
            # Check email mapping
            if rootly_email in email_to_github:
                correlations[rootly_email] = email_to_github[rootly_email]
                logger.debug(f"Matched {rootly_email} via email discovery")
                continue
                
            # Try name-based matching as fallback
            github_username = self._try_name_matching(user, github_users)
            if github_username:
                correlations[rootly_email] = github_username
                logger.debug(f"Matched {rootly_email} via name matching")
            else:
                correlations[rootly_email] = None
                unmatched.append(user)
        
        # Report results
        matched_count = sum(1 for v in correlations.values() if v is not None)
        logger.info(f"Correlation complete: {matched_count}/{len(rootly_users)} users matched")
        logger.info(f"Total GitHub emails discovered: {len(email_to_github)}")
        
        if unmatched:
            logger.warning(f"Unable to match {len(unmatched)} users:")
            for user in unmatched[:5]:  # Show first 5
                logger.warning(f"  - {user.get('name')} ({user.get('email')})")
            if len(unmatched) > 5:
                logger.warning(f"  ... and {len(unmatched) - 5} more")
            logger.info("Add manual mappings to config.json to improve match rate")
        
        return correlations
    
    def _get_all_github_users(self) -> Set[str]:
        """Get all unique GitHub usernames from configured organizations."""
        all_users = set()
        
        for org in self.organizations:
            members = self._get_org_members(org)
            all_users.update(members)
            
        return all_users
    
    @lru_cache(maxsize=10)
    def _get_org_members(self, org: str) -> List[str]:
        """Get all members of a GitHub organization."""
        if org in self._org_members_cache:
            return self._org_members_cache[org]
            
        members = []
        page = 1
        
        while True:
            try:
                response = requests.get(
                    f'https://api.github.com/orgs/{org}/members',
                    headers=self.headers,
                    params={'per_page': 100, 'page': page}
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to get members for {org}: {response.status_code}")
                    break
                    
                data = response.json()
                if not data:
                    break
                    
                members.extend(user['login'] for user in data)
                page += 1
                
            except Exception as e:
                logger.error(f"Error fetching members for {org}: {e}")
                break
        
        self._org_members_cache[org] = members
        return members
    
    def _build_email_mapping(self, github_users: Set[str]) -> Dict[str, str]:
        """
        Build mapping of email addresses to GitHub usernames by mining commits.
        """
        email_to_user = {}
        
        # Check cache first (unless refresh requested)
        cache_file = self.cache_dir / "email_mapping.json"
        if cache_file.exists() and not self.refresh_cache:
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    logger.info(f"Loaded email mapping from cache: {len(cached_data)} mappings")
                    return cached_data
            except Exception as e:
                logger.warning(f"Failed to load email cache: {e}, rebuilding...")
        
        if self.refresh_cache:
            logger.info("Refreshing email mapping cache...")
        
        # Build fresh mapping
        logger.info("Building email mapping from GitHub commits...")
        
        for username in github_users:
            emails = self._get_user_emails(username)
            for email in emails:
                email_lower = email.lower()
                if email_lower not in email_to_user:
                    email_to_user[email_lower] = username
        
        # Save to cache (always save, no expiration)
        try:
            with open(cache_file, 'w') as f:
                json.dump(email_to_user, f, indent=2)
            logger.info(f"Saved email mapping to cache: {len(email_to_user)} mappings")
        except Exception as e:
            logger.warning(f"Failed to save email cache: {e}")
        
        return email_to_user
    
    def _get_user_emails(self, username: str) -> Set[str]:
        """Get all email addresses used by a GitHub user in commits."""
        if username in self._user_emails_cache:
            return self._user_emails_cache[username]
            
        emails = set()
        
        # First try to get public email from user profile
        try:
            response = requests.get(
                f'https://api.github.com/users/{username}',
                headers=self.headers
            )
            if response.status_code == 200:
                user_data = response.json()
                if user_data.get('email'):
                    emails.add(user_data['email'])
                # Also get the name for better matching
                self._user_names_cache[username] = user_data.get('name', '')
        except:
            pass
        
        # Get emails from recent commits across all org repos
        for org in self.organizations:
            # Get user's recent events to find repos they've contributed to
            try:
                response = requests.get(
                    f'https://api.github.com/users/{username}/events',
                    headers=self.headers,
                    params={'per_page': 100}
                )
                
                if response.status_code != 200:
                    continue
                    
                events = response.json()
                repos_to_check = set()
                
                for event in events:
                    if event['type'] in ['PushEvent', 'PullRequestEvent']:
                        repo = event.get('repo', {}).get('name', '')
                        if repo and (f'{org}/' in repo):
                            repos_to_check.add(repo)
                
                # Check commits in those repos
                for repo in list(repos_to_check)[:5]:  # Limit to 5 repos per user
                    try:
                        response = requests.get(
                            f'https://api.github.com/repos/{repo}/commits',
                            headers=self.headers,
                            params={'author': username, 'per_page': 10}
                        )
                        
                        if response.status_code == 200:
                            commits = response.json()
                            for commit in commits:
                                author = commit.get('commit', {}).get('author', {})
                                if author.get('email'):
                                    emails.add(author['email'])
                    except:
                        continue
                        
            except Exception as e:
                logger.debug(f"Error getting emails for {username}: {e}")
        
        self._user_emails_cache[username] = emails
        return emails
    
    def _try_name_matching(self, rootly_user: Dict, github_users: Set[str]) -> Optional[str]:
        """Try to match a Rootly user to GitHub by name patterns."""
        name = rootly_user.get('name', '').lower()
        email_prefix = rootly_user.get('email', '').split('@')[0].lower()
        
        if not name:
            return None
        
        # Common username patterns
        name_parts = name.split()
        if len(name_parts) >= 2:
            first = name_parts[0]
            last = name_parts[-1]
            
            patterns = [
                f"{first}{last}",          # johnsmith
                f"{first}.{last}",         # john.smith
                f"{first}-{last}",         # john-smith
                f"{first[0]}{last}",       # jsmith
                f"{first}{last[0]}",       # johns
                email_prefix               # from email
            ]
            
            for pattern in patterns:
                if pattern in github_users:
                    return pattern
                    
            # Try case-insensitive match
            github_users_lower = {u.lower(): u for u in github_users}
            for pattern in patterns:
                if pattern in github_users_lower:
                    return github_users_lower[pattern]
        
        return None
    
    def get_correlation_report(self, correlations: Dict[str, Optional[str]]) -> Dict:
        """Generate a report of correlation results."""
        total = len(correlations)
        matched = sum(1 for v in correlations.values() if v is not None)
        unmatched = total - matched
        
        return {
            'summary': {
                'total_users': total,
                'matched': matched,
                'unmatched': unmatched,
                'match_rate': f"{(matched/total*100):.1f}%" if total > 0 else "0%"
            },
            'unmatched_users': [
                email for email, github in correlations.items() if github is None
            ],
            'correlations': correlations
        }
    
    def clear_cache(self):
        """Clear all cached GitHub data."""
        cache_files = list(self.cache_dir.glob("*.json"))
        for cache_file in cache_files:
            try:
                cache_file.unlink()
                logger.info(f"Deleted cache file: {cache_file.name}")
            except Exception as e:
                logger.warning(f"Failed to delete {cache_file.name}: {e}")
        
        if cache_files:
            logger.info(f"Cleared {len(cache_files)} cache files")
        else:
            logger.info("No cache files to clear")
    
    def get_cache_info(self) -> Dict:
        """Get information about cached data."""
        cache_files = list(self.cache_dir.glob("*.json"))
        info = {
            'cache_dir': str(self.cache_dir),
            'files': [],
            'total_size_bytes': 0
        }
        
        for cache_file in cache_files:
            try:
                stat = cache_file.stat()
                info['files'].append({
                    'name': cache_file.name,
                    'size_bytes': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
                info['total_size_bytes'] += stat.st_size
            except:
                pass
        
        return info