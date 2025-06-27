# Burnout Calculation Methodology

This document provides a detailed explanation of how the Rootly Burnout Detector calculates burnout scores using the Maslach Burnout Inventory framework, enhanced with modern engineering data sources.

## Overview

The system uses a **three-dimensional scoring approach** based on Christina Maslach's research, analyzing incident response patterns, coding activity, and communication behaviors to provide comprehensive burnout assessment.

## Maslach Burnout Inventory Framework

The Maslach Burnout Inventory identifies three key dimensions of occupational burnout:

```mermaid
graph TD
    A[Burnout Assessment] --> B[Emotional Exhaustion<br/>40% Weight]
    A --> C[Depersonalization<br/>30% Weight]
    A --> D[Personal Accomplishment<br/>30% Weight - Inverted]
    
    B --> B1[Physical & Emotional<br/>Depletion]
    C --> C1[Cynicism & Detachment<br/>from Work]
    D --> D1[Sense of Achievement<br/>& Competence]
    
    style B fill:#ffcccc
    style C fill:#ffffcc
    style D fill:#ccffcc
```

## Data Sources & Integration

### Standard Analysis (Incident Data Only)
```mermaid
graph LR
    A[Rootly Incidents] --> B[Burnout Calculation]
    B --> C[Risk Score 0-10]
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#e8f5e8
```

### Enhanced Analysis (Multi-Source)
```mermaid
graph TD
    A[Rootly Incidents<br/>70% Weight] --> D[Dimension Score]
    B[GitHub Activity<br/>15% Weight] --> D
    C[Slack Communication<br/>15% Weight] --> D
    
    D --> E[Final Burnout Score]
    
    style A fill:#e1f5fe
    style B fill:#fff3e0
    style C fill:#e8f5e8
    style D fill:#f3e5f5
    style E fill:#ffebee
```

## Detailed Dimension Calculations

### 1. Emotional Exhaustion (40% Weight)

Measures physical and emotional depletion from work demands.

#### Incident Data Components:
- **Incident Frequency Score**: Based on incidents per week vs. team baseline
- **After-Hours Work Score**: Percentage of incidents handled outside business hours
- **Resolution Time Score**: Average time to resolve incidents
- **Incident Clustering Score**: Multiple incidents within 4-hour windows

#### GitHub Data Components:
- **After-Hours Commits**: Commits outside 9-5 business hours
- **Weekend Coding**: Development work on weekends
- **Commit Clustering**: Rapid consecutive commits indicating stress

#### Slack Data Components:
- **Message Volume**: Daily message frequency
- **After-Hours Communication**: Messages sent outside business hours
- **Stress Indicators**: VADER sentiment analysis + stress keyword detection
- **Emotional Volatility**: Standard deviation of sentiment scores

```mermaid
graph TD
    A[Emotional Exhaustion] --> B[Incident Analysis<br/>70%]
    A --> C[GitHub Analysis<br/>15%]
    A --> D[Slack Analysis<br/>15%]
    
    B --> B1[Frequency: incidents/week]
    B --> B2[After-hours: % outside 9-5]
    B --> B3[Resolution: avg time]
    B --> B4[Clustering: incidents within 4h]
    
    C --> C1[After-hours commits %]
    C --> C2[Weekend coding %]
    C --> C3[Commit clustering ratio]
    
    D --> D1[Message volume/day]
    D --> D2[After-hours messages %]
    D --> D3[Stress keywords detected]
    D --> D4[Sentiment volatility]
    
    style A fill:#ffcccc
    style B fill:#e1f5fe
    style C fill:#fff3e0
    style D fill:#e8f5e8
```

#### Calculation Formula:
```
Incident Score = (frequency_score + after_hours_score + resolution_score + clustering_score) / 4
GitHub Score = (after_hours_commits + weekend_commits + clustering_ratio) / 3  
Slack Score = (volume_score + after_hours_msgs + stress_score + volatility_score) / 4

Emotional Exhaustion = (Incident Score × 0.7) + (GitHub Score × 0.15) + (Slack Score × 0.15)
```

### 2. Depersonalization (30% Weight)

Measures cynicism and detachment from work relationships.

#### Incident Data Components:
- **Escalation Rate**: Frequency of escalating incidents to others
- **Solo Work Rate**: Handling incidents without collaboration
- **Response Time Trends**: Increasing response times over time
- **Communication Quality**: Length and detail of resolution messages

#### GitHub Data Components:
- **Repository Switching**: Working across too many repositories
- **PR Collaboration**: Participation in pull request reviews
- **Code Review Quality**: Engagement in collaborative development

#### Slack Data Components:
- **Thread Participation**: Engagement in collaborative discussions
- **Private Message Ratio**: Avoiding public channels
- **Channel Diversity**: Context switching across too many channels
- **Communication Quality**: Message length and engagement depth

```mermaid
graph TD
    A[Depersonalization] --> B[Incident Analysis<br/>70%]
    A --> C[GitHub Analysis<br/>15%]
    A --> D[Slack Analysis<br/>15%]
    
    B --> B1[Escalation rate]
    B --> B2[Solo incident %]
    B --> B3[Response time trend]
    B --> B4[Message quality]
    
    C --> C1[Repository switching]
    C --> C2[PR collaboration rate]
    C --> C3[Code review participation]
    
    D --> D1[Thread participation]
    D --> D2[DM vs public ratio]
    D --> D3[Channel diversity]
    D --> D4[Message length trends]
    
    style A fill:#ffffcc
    style B fill:#e1f5fe
    style C fill:#fff3e0
    style D fill:#e8f5e8
```

### 3. Personal Accomplishment (30% Weight - Inverted)

Measures sense of achievement and professional competence. **Note: Higher accomplishment scores are inverted to contribute to lower burnout.**

#### Incident Data Components:
- **Resolution Success Rate**: Percentage of incidents successfully resolved
- **Resolution Time Improvement**: Getting faster at resolving incidents over time
- **Complexity Handling**: Success with high-severity incidents
- **Knowledge Sharing**: Documentation and post-incident analysis quality

#### GitHub Data Components:
- **Productive Commit Frequency**: Optimal range of 3-8 commits per week
- **PR Creation Rate**: Contributing new features and improvements
- **Repository Contributions**: Consistent development across projects

#### Slack Data Components:
- **Communication Patterns**: Healthy, helpful communication style
- **Collaborative Engagement**: Active participation in team discussions
- **Consistent Presence**: Regular, professional communication

```mermaid
graph TD
    A[Personal Accomplishment<br/>Inverted] --> B[Incident Analysis<br/>70%]
    A --> C[GitHub Analysis<br/>15%]
    A --> D[Slack Analysis<br/>15%]
    
    B --> B1[Resolution success %]
    B --> B2[Time improvement trend]
    B --> B3[Complexity handling]
    B --> B4[Knowledge sharing score]
    
    C --> C1[Commit frequency 3-8/week]
    C --> C2[PR creation rate]
    C --> C3[Repository diversity]
    
    D --> D1[Helpful communication]
    D --> D2[Team engagement]
    D --> D3[Consistent presence]
    
    style A fill:#ccffcc
    style B fill:#e1f5fe
    style C fill:#fff3e0
    style D fill:#e8f5e8
```

## Final Score Calculation

### Overall Burnout Score Formula

```
Final Burnout Score = 
    (Emotional Exhaustion × 0.4) + 
    (Depersonalization × 0.3) + 
    ((10 - Personal Accomplishment) × 0.3)
```

### Risk Level Classification

```mermaid
graph LR
    A[Burnout Score] --> B{Score Range}
    B -->|0.0 - 3.9| C[Low Risk<br/>Healthy Engagement]
    B -->|4.0 - 6.9| D[Medium Risk<br/>Early Warning Signs]
    B -->|7.0 - 10.0| E[High Risk<br/>Immediate Action Needed]
    
    style C fill:#c8e6c9
    style D fill:#fff9c4
    style E fill:#ffcdd2
```

## Scoring Examples

### Example 1: Healthy Engineer
```
Emotional Exhaustion: 2.1 (low incident load, good boundaries)
Depersonalization: 1.8 (good collaboration, responsive)
Personal Accomplishment: 7.5 (successful resolutions, knowledge sharing)

Burnout Score = (2.1 × 0.4) + (1.8 × 0.3) + ((10 - 7.5) × 0.3)
             = 0.84 + 0.54 + 0.75
             = 2.13 (Low Risk)
```

### Example 2: At-Risk Engineer
```
Emotional Exhaustion: 6.2 (high incident load, after-hours work)
Depersonalization: 5.1 (increasing escalations, shorter messages)
Personal Accomplishment: 4.2 (declining resolution success)

Burnout Score = (6.2 × 0.4) + (5.1 × 0.3) + ((10 - 4.2) × 0.3)
             = 2.48 + 1.53 + 1.74
             = 5.75 (Medium Risk)
```

### Example 3: High-Risk Engineer
```
Emotional Exhaustion: 8.3 (excessive incident load, poor boundaries)
Depersonalization: 7.6 (high escalation rate, communication decline)
Personal Accomplishment: 2.8 (low resolution success, minimal sharing)

Burnout Score = (8.3 × 0.4) + (7.6 × 0.3) + ((10 - 2.8) × 0.3)
             = 3.32 + 2.28 + 2.16
             = 7.76 (High Risk)
```

## Sentiment Analysis Detail

### VADER Sentiment Scoring

The system uses VADER (Valence Aware Dictionary and sEntiment Reasoner) for Slack message analysis:

```mermaid
graph TD
    A[Slack Message] --> B[VADER Analysis]
    B --> C[Compound Score<br/>-1 to +1]
    B --> D[Positive Ratio]
    B --> E[Negative Ratio]
    B --> F[Neutral Ratio]
    
    G[Stress Keywords] --> H[Stress Score]
    A --> G
    
    C --> I[Sentiment Metrics]
    H --> I
    
    I --> J[Emotional Exhaustion<br/>Component]
    
    style A fill:#e8f5e8
    style B fill:#f3e5f5
    style I fill:#fff3e0
    style J fill:#ffcccc
```

### Stress Keywords Detected:
- **High Stress**: "overwhelmed", "exhausted", "burned out", "drowning", "urgent"
- **Moderate Stress**: "busy", "behind", "pressure", "stretched", "tight timeline"
- **Negative Sentiment**: "sorry", "failed", "broken", "can't", "frustrated"

### Sentiment Volatility Calculation:
```
Volatility = Standard Deviation of Daily Sentiment Scores
- Low (0.0-0.2): Stable emotional state
- Moderate (0.2-0.4): Some emotional fluctuation  
- High (0.4+): High emotional instability
```

## Data Collection Periods

All analyses use consistent 30-day lookback periods:

```mermaid
gantt
    title Data Collection Timeline
    dateFormat  YYYY-MM-DD
    
    section Rootly Data
    Incidents & Alerts    :2024-05-27, 2024-06-26
    
    section GitHub Data  
    Commits & PRs         :2024-05-27, 2024-06-26
    
    section Slack Data
    Messages & Patterns   :2024-05-27, 2024-06-26
    
    section Analysis
    Burnout Calculation   :2024-06-26, 1d
```

## Validation & Calibration

The scoring system is calibrated based on:

1. **Clinical Research**: Maslach Burnout Inventory validated thresholds
2. **Engineering Context**: Adapted for on-call and development work patterns
3. **Team Baselines**: Scores relative to team and organizational norms
4. **Temporal Trends**: Changes over time more significant than absolute scores

## Recommendations Engine

Based on calculated scores, the system generates targeted recommendations:

```mermaid
graph TD
    A[Burnout Score] --> B{Risk Level}
    
    B -->|High 7.0+| C[Immediate Interventions]
    B -->|Medium 4.0-6.9| D[Preventive Actions]
    B -->|Low 0-3.9| E[Maintenance Activities]
    
    C --> C1[Reduce incident load]
    C --> C2[Enforce boundaries]
    C --> C3[Additional support]
    
    D --> D1[Monitor trends]
    D --> D2[Workload adjustment]
    D --> D3[Skills development]
    
    E --> E1[Continue practices]
    E --> E2[Knowledge sharing]
    E --> E3[Team mentoring]
    
    style C fill:#ffcdd2
    style D fill:#fff9c4
    style E fill:#c8e6c9
```

This methodology provides a comprehensive, data-driven approach to identifying burnout risk before it becomes severe, enabling proactive intervention and support for engineering teams.