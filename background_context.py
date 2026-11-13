"""
General background context for the LLM Context experiment.

This module provides background information about major events during the study period
(May 30 - June 30, 2024) that are relevant to understanding social media discourse
about political ideology and stance toward Biden and Trump.
"""

from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime, date


class EventType(str, Enum):
    """Types of background events."""
    LEGAL = "legal"
    POLITICAL = "political"
    ELECTORAL = "electoral"
    MEDIA = "media"


class BackgroundEvent:
    """Represents a significant background event during the study period."""
    
    def __init__(
        self,
        event_id: str,
        title: str,
        date: date,
        event_type: EventType,
        description: str,
        key_figures: List[str],
        impact: str,
        related_keywords: List[str],
    ):
        self.event_id = event_id
        self.title = title
        self.date = date
        self.event_type = event_type
        self.description = description
        self.key_figures = key_figures
        self.impact = impact
        self.related_keywords = related_keywords
    
    def to_dict(self) -> Dict:
        """Convert event to dictionary."""
        return {
            'event_id': self.event_id,
            'title': self.title,
            'date': self.date.isoformat(),
            'event_type': self.event_type.value,
            'description': self.description,
            'key_figures': self.key_figures,
            'impact': self.impact,
            'related_keywords': self.related_keywords,
        }
    
    def to_text(self) -> str:
        """Convert event to formatted text for context."""
        return f"""
EVENT: {self.title}
Date: {self.date.strftime('%B %d, %Y')}
Type: {self.event_type.value}

Description:
{self.description}

Key Figures: {', '.join(self.key_figures)}

Impact:
{self.impact}

Related Keywords: {', '.join(self.related_keywords)}
"""


# ============================================================================
# MAJOR EVENTS DURING STUDY PERIOD (May 30 - June 30, 2024)
# ============================================================================

TRUMP_HUSH_MONEY_TRIAL = BackgroundEvent(
    event_id="event_trump_trial_2024",
    title="Donald Trump Hush-Money Trial Verdict",
    date=date(2024, 5, 30),
    event_type=EventType.LEGAL,
    description="""
A New York jury delivered a historic verdict in Donald Trump's criminal hush-money case, 
finding him guilty on all 34 felony counts related to falsifying business records. These 
charges stemmed from alleged payments to adult film actress Stormy Daniels during the 
2016 presidential campaign to prevent disclosure of an alleged affair.

This was the first criminal conviction of a former U.S. president, representing a 
significant moment in American legal and political history. The conviction took place 
amid Trump's 2024 presidential campaign as the Republican nominee.
""",
    key_figures=["Donald Trump", "Judge Juan Merchan", "Stormy Daniels", "Michael Cohen"],
    impact="""
- Made Trump the first former U.S. president to be convicted of crimes
- Became a central and polarizing issue in the 2024 presidential campaign
- Intensified partisan divisions regarding the politicization of the justice system
- Raised questions about Trump's eligibility and viability as a candidate
- Generated intense media coverage and social media discourse
- Supporters viewed it as politically motivated; critics as appropriate accountability
""",
    related_keywords=[
        "Trump conviction", "felony", "hush money", "Stormy Daniels", 
        "falsifying records", "Manhattan DA", "jury verdict", "criminal trial"
    ]
)


HUNTER_BIDEN_GUN_TRIAL = BackgroundEvent(
    event_id="event_hunter_biden_trial_2024",
    title="Hunter Biden Federal Gun Trial Verdict",
    date=date(2024, 6, 11),
    event_type=EventType.LEGAL,
    description="""
Hunter Biden, the son of President Joe Biden, was found guilty on three felony counts 
related to the unlawful purchase and possession of a firearm in 2018. The charges 
included illegally purchasing a handgun while being addicted to drugs and lying on 
federal forms about his drug use.

The verdict came during the 2024 presidential campaign, creating a parallel to the 
Trump conviction but from the opposing political party. Hunter Biden's history of 
personal struggles with addiction had been a subject of political controversy.
""",
    key_figures=["Hunter Biden", "President Joe Biden", "Delaware prosecutors", "Gun dealers"],
    impact="""
- Created parallel narrative to Trump's conviction during the campaign
- Drew significant media attention and became a point of partisan conflict
- Republicans emphasized it as evidence of Biden family misconduct
- Democrats noted Hunter Biden's willingness to cooperate with justice system
- Raised questions about family privilege and accountability
- Intensified discussions about gun control and drug policy
- Became ammunition in social media debates about Biden presidency
""",
    related_keywords=[
        "Hunter Biden", "gun trial", "felony", "firearms", "drug use",
        "Delaware court", "federal charges", "guilty verdict", "Biden family"
    ]
)


BIDEN_TRUMP_DEBATE = BackgroundEvent(
    event_id="event_biden_trump_debate_2024",
    title="First Biden-Trump Presidential Debate",
    date=date(2024, 6, 27),
    event_type=EventType.ELECTORAL,
    description="""
The first presidential debate between incumbent President Joe Biden and former President 
Donald Trump was held in Atlanta, hosted by CNN. This debate was a major event in the 
2024 general election campaign, featuring the two leading candidates for the presidency.

The debate covered key policy areas including the economy, healthcare, foreign policy, 
immigration, and other pressing national issues. Both candidates sought to present their 
vision for the country and challenge the other's record and positions.

The debate received significant media coverage and sparked widespread discussion on 
social media platforms about the candidates' performance, competence, stamina, and 
policy positions.
""",
    key_figures=["Joe Biden", "Donald Trump", "CNN moderators", "American voters"],
    impact="""
- Significantly shaped media narratives and public discussions about both candidates
- Provided a major platform for direct comparison of positions and rhetoric
- Influenced voter perceptions of candidate competence and fitness for office
- Generated extensive social media discourse and commentary
- Served as a moment for voters to assess candidate performance
- Created talking points for both campaigns moving forward
- Affected polling numbers and campaign momentum
- Highlighted key differences on major policy issues
""",
    related_keywords=[
        "presidential debate", "Biden", "Trump", "2024 election", "CNN",
        "debate performance", "policy positions", "campaign", "voters",
        "competence", "stamina", "rhetoric"
    ]
)


# ============================================================================
# STUDY PERIOD SUMMARY
# ============================================================================

STUDY_PERIOD_GENERAL_BACKGROUND = """
GENERAL BACKGROUND (May 30 – June 30, 2024)

During the period from May 30 to June 30, 2024, the United States was in the midst of 
the presidential election campaign between President Joe Biden (Democratic Party) and 
former President Donald Trump (Republican Party). 

Public attention during this month focused heavily on several high-profile legal and 
political events involving the candidates or their families, as well as the first 
general-election debate.

Key Context:
- Both candidates were actively campaigning across the country
- Social media platforms were primary venues for political discourse
- Partisan divisions were significantly elevated during this period
- Major news events dominated social media conversations
- Voter engagement with political content was heightened during election season

The events listed below became focal points for social media discussion, with users 
expressing their political ideology and stance toward both candidates through reactions 
to these developments.
"""


# ============================================================================
# BACKGROUND CONTEXT MANAGEMENT
# ============================================================================

class BackgroundContextManager:
    """Manage and provide background context for analysis."""
    
    def __init__(self):
        self.events: Dict[str, BackgroundEvent] = {
            'trump_trial': TRUMP_HUSH_MONEY_TRIAL,
            'hunter_biden_trial': HUNTER_BIDEN_GUN_TRIAL,
            'biden_trump_debate': BIDEN_TRUMP_DEBATE,
        }
    
    def get_event(self, event_key: str) -> Optional[BackgroundEvent]:
        """Get a specific background event."""
        return self.events.get(event_key)
    
    def get_all_events(self) -> Dict[str, BackgroundEvent]:
        """Get all background events."""
        return self.events
    
    def get_event_text(self, event_key: str) -> Optional[str]:
        """Get formatted text for a specific event."""
        event = self.events.get(event_key)
        return event.to_text() if event else None
    
    def get_all_events_text(self) -> str:
        """Get formatted text for all events."""
        parts = [STUDY_PERIOD_GENERAL_BACKGROUND]
        for event_key in sorted(self.events.keys()):
            parts.append(self.events[event_key].to_text())
        return "\n".join(parts)
    
    def get_general_context(self) -> str:
        """Get general study period context."""
        return STUDY_PERIOD_GENERAL_BACKGROUND
    
    def get_context_for_date(self, post_date: Optional[date]) -> str:
        """
        Get relevant background context for a specific post date.
        
        Returns all events that occurred before or on the post date.
        """
        if not post_date:
            return self.get_general_context()
        
        parts = [STUDY_PERIOD_GENERAL_BACKGROUND]
        
        # Add events that occurred before this date
        for event_key in sorted(self.events.keys()):
            event = self.events[event_key]
            if event.date <= post_date:
                parts.append(event.to_text())
        
        return "\n".join(parts)
    
    def get_event_summary(self, event_key: str) -> Optional[Dict]:
        """Get event as dictionary."""
        event = self.events.get(event_key)
        return event.to_dict() if event else None
    
    def get_keywords_for_event(self, event_key: str) -> Optional[List[str]]:
        """Get keywords associated with an event."""
        event = self.events.get(event_key)
        return event.related_keywords if event else None
    
    def search_events_by_keyword(self, keyword: str) -> List[BackgroundEvent]:
        """Find events related to a specific keyword."""
        keyword_lower = keyword.lower()
        matching_events = []
        
        for event in self.events.values():
            if (keyword_lower in event.title.lower() or
                keyword_lower in event.description.lower() or
                any(keyword_lower in k.lower() for k in event.related_keywords) or
                any(keyword_lower in f.lower() for f in event.key_figures)):
                matching_events.append(event)
        
        return matching_events


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_background_context_manager() -> BackgroundContextManager:
    """Get a background context manager instance."""
    return BackgroundContextManager()


def format_background_for_llm(
    event_key: Optional[str] = None,
    post_date: Optional[date] = None
) -> str:
    """
    Get formatted background context for LLM prompts.
    
    Args:
        event_key: Specific event to include (optional)
        post_date: Date to filter events by (optional)
    
    Returns:
        Formatted background context text
    """
    manager = get_background_context_manager()
    
    if event_key:
        return manager.get_event_text(event_key) or manager.get_general_context()
    elif post_date:
        return manager.get_context_for_date(post_date)
    else:
        return manager.get_all_events_text()


if __name__ == "__main__":
    # Example usage
    manager = BackgroundContextManager()
    
    print("=" * 80)
    print("ALL BACKGROUND EVENTS")
    print("=" * 80)
    print(manager.get_all_events_text())
    
    print("\n" + "=" * 80)
    print("TRUMP TRIAL EVENT DETAILS")
    print("=" * 80)
    print(manager.get_event_summary('trump_trial'))
    
    print("\n" + "=" * 80)
    print("KEYWORD SEARCH: 'Biden'")
    print("=" * 80)
    events = manager.search_events_by_keyword('Biden')
    for event in events:
        print(f"- {event.title}")
