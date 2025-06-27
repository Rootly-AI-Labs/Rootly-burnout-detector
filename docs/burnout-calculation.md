# Burnout Score Calculation Methodology

## Overview

Burnout scores are calculated using the Maslach Burnout Inventory framework, analyzing three dimensions weighted by their contribution to overall burnout risk.

## Dimension Weights

- **Emotional Exhaustion**: 40% (0.4)
- **Depersonalization**: 30% (0.3)  
- **Personal Accomplishment**: 30% (0.3) - Inverted

## Data Source Weights

When multiple data sources are enabled:

- **Incident Data**: 70% (0.7) of each dimension
- **GitHub Data**: 15% (0.15) of each dimension
- **Slack Data**: 15% (0.15) of each dimension

## Emotional Exhaustion Calculation

### Incident Component (0-10 scale)
```
incident_frequency_score = min(10, (incidents_per_week / 3) * 10)
after_hours_score = min(10, after_hours_percentage * 20)
resolution_time_score = min(10, avg_resolution_hours * 2.5)
clustering_score = min(10, (clustered_incidents / total_incidents) * 15)

incident_exhaustion = mean([incident_frequency_score, after_hours_score, 
                           resolution_time_score, clustering_score])
```

### GitHub Component (0-10 scale)
```
after_hours_commits_score = min(10, after_hours_commit_ratio * 25)
weekend_commits_score = min(10, weekend_commit_ratio * 50)
commit_clustering_score = min(10, clustered_commits_ratio * 12.5)

github_exhaustion = mean([after_hours_commits_score, weekend_commits_score,
                         commit_clustering_score])
```

### Slack Component (0-10 scale)
```
volume_score = 10 if messages_per_day > 30 else
               7 if messages_per_day > 20 else
               4 if messages_per_day > 10 else 1

after_hours_msg_score = min(10, after_hours_percentage * 25)
weekend_msg_score = min(10, weekend_percentage * 50)
sentiment_score = max(0, (-avg_sentiment + 1) * 5)
stress_score = min(10, stress_indicator_ratio * 50)
volatility_score = min(10, sentiment_volatility * 10)

slack_exhaustion = mean([volume_score, after_hours_msg_score, weekend_msg_score,
                        sentiment_score, stress_score, volatility_score])
```

### Combined Emotional Exhaustion
```
emotional_exhaustion = (incident_exhaustion * 0.7) + 
                      (github_exhaustion * 0.15) + 
                      (slack_exhaustion * 0.15)
```

## Depersonalization Calculation

### Incident Component (0-10 scale)
```
escalation_score = min(10, escalation_rate * 10)
solo_work_score = min(10, solo_incident_rate * 10)
response_trend_score = 5 if response_time_increasing else 0
communication_score = 10 if avg_message_length < 50 else
                     5 if avg_message_length < 100 else 0

incident_depersonalization = mean([escalation_score, solo_work_score,
                                  response_trend_score, communication_score])
```

### GitHub Component (0-10 scale)
```
repo_switching_score = 10 if repo_switch_ratio > 0.5 else
                      5 if repo_switch_ratio > 0.3 else 0
pr_collaboration_score = 10 - min(10, pr_to_commit_ratio * 20)
review_participation_score = 10 - min(10, review_comments_per_pr * 2)

github_depersonalization = mean([repo_switching_score, pr_collaboration_score,
                                review_participation_score])
```

### Slack Component (0-10 scale)
```
collaboration_score = 8 if thread_participation < 0.1 else
                     5 if thread_participation < 0.3 else
                     2 if thread_participation < 0.5 else 0

dm_score = min(10, dm_ratio * 20)
context_score = 8 if channel_diversity > 15 else
                5 if channel_diversity > 10 else
                2 if channel_diversity > 5 else 0

quality_score = 8 if avg_message_length < 15 else
                4 if avg_message_length < 30 else
                1 if avg_message_length < 50 else 0

negative_sentiment_score = min(10, negative_ratio * 25)

slack_depersonalization = mean([collaboration_score, dm_score, context_score,
                               quality_score, negative_sentiment_score])
```

### Combined Depersonalization
```
depersonalization = (incident_depersonalization * 0.7) + 
                   (github_depersonalization * 0.15) + 
                   (slack_depersonalization * 0.15)
```

## Personal Accomplishment Calculation

### Incident Component (0-10 scale)
```
resolution_success_score = resolution_success_rate * 10
improvement_score = 10 if resolution_time_improving else 5
complexity_score = (high_severity_success_rate * 10)
knowledge_sharing_score = min(10, (postmortems_written / incidents) * 20)

incident_accomplishment = mean([resolution_success_score, improvement_score,
                               complexity_score, knowledge_sharing_score])
```

### GitHub Component (0-10 scale)
```
commit_frequency_score = 10 if 3 <= commits_per_week <= 8 else
                        7 if 1 <= commits_per_week <= 12 else
                        3 if commits_per_week > 0 else 0

pr_creation_score = min(10, prs_per_week * 2.5)
consistency_score = 10 if active_days_per_week >= 4 else
                   5 if active_days_per_week >= 2 else 0

github_accomplishment = mean([commit_frequency_score, pr_creation_score,
                             consistency_score])
```

### Slack Component (0-10 scale)
```
pattern_score = response_pattern_score  # Pre-calculated 0-10
activity_score = 8 if 5 <= messages_per_day <= 15 else
                6 if 3 <= messages_per_day <= 20 else
                3 if messages_per_day > 0 else 0

engagement_score = 8 if thread_participation > 0.5 else
                  6 if thread_participation > 0.3 else
                  3 if thread_participation > 0.1 else 1

presence_score = min(8, total_messages / days * 2)
positive_sentiment_score = min(10, (avg_sentiment + 1) * 5)

slack_accomplishment = mean([pattern_score, activity_score, engagement_score,
                            presence_score, positive_sentiment_score])
```

### Combined Personal Accomplishment
```
personal_accomplishment = (incident_accomplishment * 0.7) + 
                         (github_accomplishment * 0.15) + 
                         (slack_accomplishment * 0.15)
```

## Final Burnout Score Calculation

```
burnout_score = (emotional_exhaustion * 0.4) + 
                (depersonalization * 0.3) + 
                ((10 - personal_accomplishment) * 0.3)
```

## Risk Level Thresholds

```
if burnout_score >= 7.0:
    risk_level = "high"
elif burnout_score >= 4.0:
    risk_level = "medium"
else:
    risk_level = "low"
```

## Sentiment Analysis Calculations (Slack)

### VADER Sentiment Scoring
```
compound_score = analyzer.polarity_scores(message)['compound']
# Range: -1 (most negative) to +1 (most positive)

avg_sentiment = mean(all_compound_scores)
sentiment_volatility = stdev(all_compound_scores)
negative_ratio = count(scores < -0.05) / total_messages
positive_ratio = count(scores > 0.05) / total_messages
```

### Stress Indicator Detection
```
stress_keywords = ['overwhelmed', 'exhausted', 'burned out', 'drowning', 
                  'swamped', 'urgent', 'emergency', 'crisis']

stress_indicator_ratio = messages_containing_stress_keywords / total_messages
```

## Time-Based Calculations

### Business Hours Definition
```
business_start = 9  # 9 AM
business_end = 17   # 5 PM
business_days = [0, 1, 2, 3, 4]  # Monday-Friday

is_after_hours = hour < business_start or hour >= business_end or 
                 day_of_week not in business_days
                 
after_hours_percentage = after_hours_items / total_items
weekend_percentage = weekend_items / total_items
```

### Clustering Detection
```
cluster_window = 4  # hours

clustered_items = items where another item exists within cluster_window
clustering_ratio = clustered_items / total_items
```