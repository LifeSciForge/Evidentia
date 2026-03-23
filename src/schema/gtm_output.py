"""
GTM Output Schema
Final GTM strategy document that gets exported as PDF/JSON
"""

from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ExecutiveSummary:
    """One-page executive summary of GTM strategy"""
    strategy_title: str = ""
    drug_name: str = ""
    indication: str = ""
    key_insight: str = ""
    recommended_strategy: str = ""
    expected_launch_window: str = ""
    market_opportunity: str = ""
    key_success_factors: List[str] = field(default_factory=list)


@dataclass
class MarketOpportunity:
    """Market sizing and opportunity assessment"""
    total_addressable_market: Optional[float] = None
    serviceable_addressable_market: Optional[float] = None
    serviceable_obtainable_market: Optional[float] = None
    currency: str = "USD"
    patient_population_total: Optional[int] = None
    addressable_patient_population: Optional[int] = None
    market_growth_rate: Optional[float] = None
    years_to_peak_sales: Optional[int] = None
    peak_annual_sales_estimate: Optional[float] = None
    market_assumptions: List[str] = field(default_factory=list)


@dataclass
class TargetSegment:
    """Definition of primary target segment"""
    segment_name: str = ""
    segment_description: str = ""
    patient_characteristics: List[str] = field(default_factory=list)
    geography: List[str] = field(default_factory=list)
    company_size_profile: str = ""
    estimated_segment_size: Optional[int] = None
    penetration_assumptions: Optional[float] = None


@dataclass
class PositioningFramework:
    """Brand positioning strategy"""
    category_definition: str = ""
    category_credentials: List[str] = field(default_factory=list)
    key_differentiators: List[str] = field(default_factory=list)
    competitive_advantages: List[str] = field(default_factory=list)
    value_propositions: Dict[str, str] = field(default_factory=dict)
    messaging_pillars: List[str] = field(default_factory=list)
    brand_personality: str = ""
    elevator_pitch: str = ""


@dataclass
class ChannelStrategy:
    """Go-to-market channel mix"""
    channel_name: str = ""
    channel_description: str = ""
    target_audience: str = ""
    key_activities: List[str] = field(default_factory=list)
    expected_reach: Optional[int] = None
    estimated_roi: Optional[float] = None
    success_metrics: List[str] = field(default_factory=list)


@dataclass
class GTMChannelMix:
    """Full channel strategy across multiple channels"""
    primary_channel: ChannelStrategy = field(default_factory=ChannelStrategy)
    secondary_channels: List[ChannelStrategy] = field(default_factory=list)
    channel_allocation_percentages: Dict[str, float] = field(default_factory=dict)
    integrated_messaging: str = ""


@dataclass
class PricingStrategy:
    """Pricing approach and rationale"""
    pricing_approach: str = ""
    rationale: str = ""
    price_point_low: Optional[float] = None
    price_point_mid: Optional[float] = None
    price_point_high: Optional[float] = None
    currency: str = "USD"
    price_per_unit_dose: Optional[float] = None
    annual_patient_cost: Optional[float] = None
    cost_per_qaly: Optional[float] = None
    competitive_pricing_analysis: Dict[str, float] = field(default_factory=dict)
    payback_period_assumptions: str = ""


@dataclass
class ReimbursementStrategy:
    """Payer and reimbursement approach"""
    payer_target_list: List[str] = field(default_factory=list)
    reimbursement_barriers: List[str] = field(default_factory=list)
    reimbursement_solutions: List[str] = field(default_factory=list)
    health_economics_studies_required: List[str] = field(default_factory=list)
    managed_access_programs: List[str] = field(default_factory=list)
    copay_assistance_strategy: str = ""
    expected_coverage_timeline: str = ""


@dataclass
class LaunchPhase:
    """Single phase of commercial timeline"""
    phase_name: str = ""
    duration_months: Optional[int] = None
    start_month: Optional[int] = None
    key_milestones: List[str] = field(default_factory=list)
    resource_requirements: Dict[str, str] = field(default_factory=dict)
    expected_outcomes: List[str] = field(default_factory=list)


@dataclass
class CommercialTimeline:
    """Full commercial launch timeline"""
    phases: List[LaunchPhase] = field(default_factory=list)
    total_duration_months: Optional[int] = None
    key_dependencies: List[str] = field(default_factory=list)
    critical_path_items: List[str] = field(default_factory=list)


@dataclass
class ResourcePlan:
    """Resources required for GTM execution"""
    commercial_team_headcount: Optional[int] = None
    field_force_size: Optional[int] = None
    regional_managers: Optional[int] = None
    marketing_budget_annual: Optional[float] = None
    sales_training_investment: Optional[float] = None
    market_access_investment: Optional[float] = None
    technology_investments: List[str] = field(default_factory=list)
    key_partnerships_required: List[str] = field(default_factory=list)


@dataclass
class SuccessMetrics:
    """KPIs to track GTM success"""
    metric_name: str = ""
    target_value: str = ""
    baseline_value: Optional[str] = None
    measurement_frequency: str = ""
    responsible_party: str = ""


@dataclass
class RiskAssessment:
    """Risk identification and mitigation"""
    risk_description: str = ""
    probability: str = ""
    impact: str = ""
    mitigation_strategy: str = ""
    contingency_plan: str = ""


@dataclass
class CompetitiveIntelligence:
    """Competitive landscape summary"""
    main_competitors: List[str] = field(default_factory=list)
    competitor_strengths: Dict[str, List[str]] = field(default_factory=dict)
    competitor_weaknesses: Dict[str, List[str]] = field(default_factory=dict)
    competitive_gaps: List[str] = field(default_factory=list)
    competitive_moat: str = ""
    market_share_projections: Dict[str, Optional[float]] = field(default_factory=dict)


@dataclass
class GTMOutputDocument:
    """Complete GTM Strategy Output Document"""
    
    document_title: str = "Pharma GTM Strategy"
    document_version: str = "1.0"
    generated_date: str = field(default_factory=lambda: datetime.now().isoformat())
    drug_name: str = ""
    indication: str = ""
    report_author: str = "GTM Simulator AI"
    
    executive_summary: ExecutiveSummary = field(default_factory=ExecutiveSummary)
    market_opportunity: MarketOpportunity = field(default_factory=MarketOpportunity)
    target_segment: TargetSegment = field(default_factory=TargetSegment)
    positioning: PositioningFramework = field(default_factory=PositioningFramework)
    channel_mix: GTMChannelMix = field(default_factory=GTMChannelMix)
    pricing: PricingStrategy = field(default_factory=PricingStrategy)
    reimbursement: ReimbursementStrategy = field(default_factory=ReimbursementStrategy)
    timeline: CommercialTimeline = field(default_factory=CommercialTimeline)
    resources: ResourcePlan = field(default_factory=ResourcePlan)
    success_metrics: List[SuccessMetrics] = field(default_factory=list)
    competitive_landscape: CompetitiveIntelligence = field(default_factory=CompetitiveIntelligence)
    risks: List[RiskAssessment] = field(default_factory=list)
    
    key_assumptions: List[str] = field(default_factory=list)
    data_sources: List[str] = field(default_factory=list)
    methodology_notes: str = ""
    next_steps: List[str] = field(default_factory=list)
    appendices: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON export"""
        return {
            "metadata": {
                "document_title": self.document_title,
                "document_version": self.document_version,
                "generated_date": self.generated_date,
                "drug_name": self.drug_name,
                "indication": self.indication,
            },
            "executive_summary": self.executive_summary.__dict__,
            "market_opportunity": self.market_opportunity.__dict__,
            "target_segment": self.target_segment.__dict__,
            "positioning": self.positioning.__dict__,
            "channel_mix": {
                "primary_channel": self.channel_mix.primary_channel.__dict__,
                "secondary_channels": [c.__dict__ for c in self.channel_mix.secondary_channels],
                "channel_allocation": self.channel_mix.channel_allocation_percentages,
            },
            "pricing": self.pricing.__dict__,
            "reimbursement": self.reimbursement.__dict__,
            "timeline": {
                "phases": [p.__dict__ for p in self.timeline.phases],
                "total_duration_months": self.timeline.total_duration_months,
            },
            "resources": self.resources.__dict__,
            "success_metrics": [m.__dict__ for m in self.success_metrics],
            "competitive_landscape": self.competitive_landscape.__dict__,
            "risks": [r.__dict__ for r in self.risks],
            "key_assumptions": self.key_assumptions,
            "data_sources": self.data_sources,
            "next_steps": self.next_steps,
        }
    
    def summary_text(self) -> str:
        """Generate human-readable summary"""
        return f"""
GTM STRATEGY FOR {self.drug_name.upper()}

Indication: {self.indication}
Generated: {self.generated_date}

EXECUTIVE SUMMARY
{self.executive_summary.key_insight}

MARKET OPPORTUNITY
TAM: ${self.market_opportunity.total_addressable_market:,.0f} {self.market_opportunity.currency}
Patient Population: {self.market_opportunity.patient_population_total:,}

TARGET SEGMENT
{self.target_segment.segment_description}

KEY SUCCESS FACTORS
{chr(10).join(f"• {factor}" for factor in self.executive_summary.key_success_factors)}

COMPETITIVE POSITIONING
{self.positioning.elevator_pitch}

NEXT STEPS
{chr(10).join(f"• {step}" for step in self.next_steps)}
        """.strip()