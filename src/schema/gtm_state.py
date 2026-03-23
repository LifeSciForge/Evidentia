"""
GTM State Machine
Core data structures that flow through all 6 agents in the LangGraph workflow
"""

from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MarketResearchData:
    """Output from Market Research Agent"""
    drug_name: str
    indication: str
    tam_estimate: Optional[float] = None  # Total Addressable Market
    sam_estimate: Optional[float] = None  # Serviceable Available Market
    som_estimate: Optional[float] = None  # Serviceable Obtainable Market
    patient_population: Optional[int] = None
    clinical_trials: List[Dict[str, Any]] = field(default_factory=list)
    key_publications: List[Dict[str, str]] = field(default_factory=list)
    epidemiology: Dict[str, Any] = field(default_factory=dict)
    research_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    research_notes: str = ""


@dataclass
class PayerIntelligenceData:
    """Output from Payer Intelligence Agent"""
    hta_status: Optional[str] = None  # NICE/EMA/ICER status
    reimbursement_criteria: List[str] = field(default_factory=list)
    qaly_threshold: Optional[float] = None  # Cost per QALY
    pricing_ceiling: Optional[float] = None
    access_restrictions: List[str] = field(default_factory=list)
    comparator_drugs: List[str] = field(default_factory=list)
    payer_feedback: Dict[str, str] = field(default_factory=dict)  # By region
    pricing_signals: Dict[str, Any] = field(default_factory=dict)
    payer_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    payer_notes: str = ""


@dataclass
class CompetitorData:
    """Output from Competitor Analysis Agent"""
    competitor_name: str
    competitor_indication: str
    market_share: Optional[float] = None
    pricing: Optional[float] = None
    positioning: str = ""
    key_differentiators: List[str] = field(default_factory=list)
    clinical_advantages: List[str] = field(default_factory=list)
    clinical_disadvantages: List[str] = field(default_factory=list)
    launch_date: Optional[str] = None
    sales_data: Optional[float] = None


@dataclass
class CompetitorAnalysisData:
    """Output from Competitor Analysis Agent - aggregates 3 main competitors"""
    competitors: List[CompetitorData] = field(default_factory=list)
    competitive_gaps: Dict[str, str] = field(default_factory=dict)
    market_positioning_strategy: str = ""
    competitive_threats: List[str] = field(default_factory=list)
    competitive_opportunities: List[str] = field(default_factory=list)
    competitive_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    competitive_notes: str = ""


@dataclass
class ICPProfile:
    """Output from ICP Definition Agent"""
    primary_icp: str = ""  # e.g., "Large pharma (>$5B revenue)"
    secondary_icp: str = ""
    company_size_range: str = ""
    therapeutic_areas_focus: List[str] = field(default_factory=list)
    key_personas: List[str] = field(default_factory=list)  # e.g., ["CCO", "Market Access Lead"]
    buying_committee: Dict[str, str] = field(default_factory=dict)  # role -> decision_weight
    urgency_triggers: List[str] = field(default_factory=list)
    geography_priority: List[str] = field(default_factory=list)
    estimated_tam_by_segment: Dict[str, float] = field(default_factory=dict)
    icp_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    icp_notes: str = ""


@dataclass
class PersonaMessaging:
    """Messaging for a single buyer persona"""
    persona: str  # e.g., "Chief Commercial Officer"
    role_description: str
    key_pain_points: List[str] = field(default_factory=list)
    value_propositions: List[str] = field(default_factory=list)
    objection_responses: Dict[str, str] = field(default_factory=dict)  # objection -> response
    success_metrics: List[str] = field(default_factory=list)
    engagement_triggers: List[str] = field(default_factory=list)


@dataclass
class MessagingData:
    """Output from Messaging & Positioning Agent"""
    category_definition: str = ""
    positioning_statement: str = ""
    key_differentiators: List[str] = field(default_factory=list)
    value_prop_by_persona: Dict[str, PersonaMessaging] = field(default_factory=dict)
    competitive_vs_statements: List[str] = field(default_factory=list)  # "vs Competitor X..."
    messaging_pillars: List[str] = field(default_factory=list)
    common_objections: Dict[str, str] = field(default_factory=dict)
    messaging_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    messaging_notes: str = ""


@dataclass
class GTMStrategy:
    """Final GTM Strategy - output from Synthesis Agent"""
    executive_summary: str = ""
    market_overview: str = ""
    market_sizing: Dict[str, float] = field(default_factory=dict)  # TAM, SAM, SOM
    target_segment: str = ""
    positioning_framework: str = ""
    key_messages: List[str] = field(default_factory=list)
    channel_strategy: Dict[str, str] = field(default_factory=dict)  # channel -> approach
    pricing_strategy: str = ""
    pricing_range: Optional[Dict[str, float]] = None  # min/max
    reimbursement_strategy: str = ""
    commercial_timeline: List[Dict[str, str]] = field(default_factory=list)  # phase -> timeline
    resource_requirements: Dict[str, str] = field(default_factory=dict)
    success_metrics: List[str] = field(default_factory=list)
    key_risks: List[str] = field(default_factory=list)
    risk_mitigation: Dict[str, str] = field(default_factory=dict)  # risk -> mitigation
    competitive_moat: str = ""
    synthesis_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    synthesis_notes: str = ""


@dataclass
class GTMState:
    """
    Central State Machine for LangGraph workflow
    
    All 6 agents read from and write to this state.
    This is the single source of truth for the entire GTM synthesis process.
    """
    
    # User Input
    drug_name: str
    indication: str
    
    # Agent Outputs
    market_data: Optional[MarketResearchData] = None
    payer_data: Optional[PayerIntelligenceData] = None
    competitor_data: Optional[CompetitorAnalysisData] = None
    icp_profile: Optional[ICPProfile] = None
    messaging_data: Optional[MessagingData] = None
    final_gtm_strategy: Optional[GTMStrategy] = None
    
    # Workflow Metadata
    workflow_id: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    agents_completed: List[str] = field(default_factory=list)
    errors: List[Dict[str, str]] = field(default_factory=list)
    
    # Streaming & UI
    current_agent: Optional[str] = None
    agent_status: str = "initializing"
    progress_percentage: int = 0
    
    def add_error(self, agent_name: str, error_message: str):
        """Log agent error"""
        self.errors.append({
            "agent": agent_name,
            "error": error_message,
            "timestamp": datetime.now().isoformat()
        })
    
    def mark_agent_complete(self, agent_name: str):
        """Mark agent as completed"""
        if agent_name not in self.agents_completed:
            self.agents_completed.append(agent_name)
        self.progress_percentage = int((len(self.agents_completed) / 6) * 100)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization"""
        return {
            "drug_name": self.drug_name,
            "indication": self.indication,
            "workflow_id": self.workflow_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "agents_completed": self.agents_completed,
            "progress_percentage": self.progress_percentage,
            "market_data": self.market_data.__dict__ if self.market_data else None,
            "payer_data": self.payer_data.__dict__ if self.payer_data else None,
            "competitor_data": self.competitor_data.__dict__ if self.competitor_data else None,
            "icp_profile": self.icp_profile.__dict__ if self.icp_profile else None,
            "messaging_data": self.messaging_data.__dict__ if self.messaging_data else None,
            "final_gtm_strategy": self.final_gtm_strategy.__dict__ if self.final_gtm_strategy else None,
        }