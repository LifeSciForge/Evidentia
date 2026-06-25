# Graph Report - .  (2026-06-24)

## Corpus Check
- 68 files · ~58,226 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 629 nodes · 1049 edges · 52 communities (45 shown, 7 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 78 edges (avg confidence: 0.55)
- Token cost: 126,163 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Payer Intelligence & HTA|Payer Intelligence & HTA]]
- [[_COMMUNITY_Streamlit UI Layer|Streamlit UI Layer]]
- [[_COMMUNITY_Messaging & Talking Points|Messaging & Talking Points]]
- [[_COMMUNITY_Market Research Agent|Market Research Agent]]
- [[_COMMUNITY_LLM Manager|LLM Manager]]
- [[_COMMUNITY_GTM Output Schema|GTM Output Schema]]
- [[_COMMUNITY_KOL Profiling & RAG (v2)|KOL Profiling & RAG (v2)]]
- [[_COMMUNITY_Epidemiology & PubMed Tools|Epidemiology & PubMed Tools]]
- [[_COMMUNITY_Agent Messages Schema|Agent Messages Schema]]
- [[_COMMUNITY_PDF Brief Generator|PDF Brief Generator]]
- [[_COMMUNITY_Synthesis Agent|Synthesis Agent]]
- [[_COMMUNITY_ICP Definition Agent|ICP Definition Agent]]
- [[_COMMUNITY_API Cache Manager|API Cache Manager]]
- [[_COMMUNITY_Architecture Diagram Flow|Architecture Diagram Flow]]
- [[_COMMUNITY_FDA Tools (Unused)|FDA Tools (Unused)]]
- [[_COMMUNITY_Product Vision & Domain|Product Vision & Domain]]
- [[_COMMUNITY_Product Doc PDF Generator|Product Doc PDF Generator]]
- [[_COMMUNITY_GTM Workflow Orchestration|GTM Workflow Orchestration]]
- [[_COMMUNITY_Competitor Analysis Agent|Competitor Analysis Agent]]
- [[_COMMUNITY_Ollama LLM Provider|Ollama LLM Provider]]
- [[_COMMUNITY_Structured Logging|Structured Logging]]
- [[_COMMUNITY_Data Quality & Memory (v2)|Data Quality & Memory (v2)]]
- [[_COMMUNITY_Input Validator|Input Validator]]
- [[_COMMUNITY_GTMState Core|GTMState Core]]
- [[_COMMUNITY_Field Insight & Territory (v2)|Field Insight & Territory (v2)]]
- [[_COMMUNITY_GTM Output Document|GTM Output Document]]
- [[_COMMUNITY_UI Chart Components|UI Chart Components]]
- [[_COMMUNITY_KOL Engagement Tracking (v2)|KOL Engagement Tracking (v2)]]
- [[_COMMUNITY_Architecture Diagram Generator|Architecture Diagram Generator]]
- [[_COMMUNITY_Dev Workflow Skill|Dev Workflow Skill]]
- [[_COMMUNITY_TDD Skill|TDD Skill]]
- [[_COMMUNITY_Debugging Skill|Debugging Skill]]
- [[_COMMUNITY_Docker Entrypoint|Docker Entrypoint]]
- [[_COMMUNITY_Real-World Evidence|Real-World Evidence]]
- [[_COMMUNITY_UIUX Standards Skill|UI/UX Standards Skill]]

## God Nodes (most connected - your core abstractions)
1. `GTMState` - 35 edges
2. `TavilySearchClient` - 24 edges
3. `market_research_agent()` - 21 edges
4. `payer_intelligence_agent()` - 18 edges
5. `synthesis_agent()` - 18 edges
6. `get_claude()` - 18 edges
7. `get_logger()` - 18 edges
8. `messaging_agent()` - 17 edges
9. `PubMedClient` - 15 edges
10. `extract_json_from_text()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `kol_profiling_agent (v2)` --semantically_similar_to--> `icp_definition_agent()`  [INFERRED] [semantically similar]
  skills/SKILL_01_MSL_INTELLIGENCE_CORE.md → src/agents/gtm_agents/icp_definition_agent.py
- `competitor_analysis_agent()` --references--> `BUG: Competitor data hallucination`  [EXTRACTED]
  src/agents/gtm_agents/competitor_analysis_agent.py → CLAUDE.md
- `MSLTalkingPoints` --references--> `Do Not Say Compliance Guardrails`  [EXTRACTED]
  src/schema/gtm_state.py → README.md
- `BUG: Max 20 publications cap` --references--> `market_research_agent()`  [EXTRACTED]
  CLAUDE.md → src/agents/gtm_agents/market_research_agent.py
- `PLAN.md — MSL Talking Points Plan` --references--> `generate_msl_talking_points()`  [EXTRACTED]
  PLAN.md → src/agents/gtm_agents/messaging_agent.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **v1 Six-Agent Brief Generation Pipeline** — gtm_agents_market_research_agent_market_research_agent, gtm_agents_payer_intelligence_agent_payer_intelligence_agent, gtm_agents_competitor_analysis_agent_competitor_analysis_agent, gtm_agents_icp_definition_agent_icp_definition_agent, gtm_agents_messaging_agent_messaging_agent, gtm_agents_synthesis_agent_synthesis_agent, schema_gtm_state_gtmstate [EXTRACTED 1.00]
- **v2 Planned New Agents** — gtm_agents_memory_retrieval_agent_memory_retrieval_agent, gtm_agents_kol_profiling_agent_kol_profiling_agent, gtm_agents_insight_extraction_agent_insight_extraction_agent, gtm_agents_engagement_scoring_agent_engagement_scoring_agent, gtm_agents_field_synthesis_agent_field_synthesis_agent [EXTRACTED 1.00]
- **Known Critical Bugs** — bug_competitor_hallucination, bug_fda_tools_never_called, bug_fragile_json_parsing, bug_no_session_persistence, bug_hardcoded_hospital_list, bug_max_20_publications [EXTRACTED 1.00]

## Communities (52 total, 7 thin omitted)

### Community 0 - "Payer Intelligence & HTA"
Cohesion: 0.07
Nodes (42): HEOR (Health Economics and Outcomes Research), HTA (Health Technology Assessment), QALY (Quality-Adjusted Life Year), format_hta_summary(), get_default_payer_data(), payer_intelligence_agent(), Payer Intelligence Agent Searches for HTA decisions, reimbursement criteria, and, Payer Intelligence Agent Node          Gathers HTA decisions, reimbursement crit (+34 more)

### Community 1 - "Streamlit UI Layer"
Cohesion: 0.07
Nodes (45): BUG: Hardcoded hospital list, Evidentia - MSL Intelligence Platform Entry point for Streamlit Cloud deployment, display_clinical_evidence_section(), display_competitive_section(), display_discovery_questions_section(), display_download_section(), display_final_brief_section(), display_msl_results() (+37 more)

### Community 2 - "Messaging & Talking Points"
Cohesion: 0.11
Nodes (39): extract_competitor_summary(), extract_icp_summary(), extract_market_summary(), extract_payer_summary(), generate_msl_talking_points(), get_default_persona_data(), get_default_positioning_data(), messaging_agent() (+31 more)

### Community 3 - "Market Research Agent"
Cohesion: 0.09
Nodes (30): BaseModel, BUG: Max 20 publications cap, format_publications_for_storage(), format_publications_summary(), format_trials_summary(), get_default_market_data(), market_research_agent(), Market Research Agent Searches for market sizing, clinical trials, and epidemiol (+22 more)

### Community 4 - "LLM Manager"
Cohesion: 0.08
Nodes (25): BaseChatModel, BaseSettings, ChatAnthropic, ChatOpenAI, get_model(), get_openai(), LLMManager, LLM initialization and configuration Handles model selection, initialization, an (+17 more)

### Community 5 - "GTM Output Schema"
Cohesion: 0.07
Nodes (29): ChannelStrategy, CommercialTimeline, CompetitiveIntelligence, ExecutiveSummary, GTMChannelMix, LaunchPhase, MarketOpportunity, PositioningFramework (+21 more)

### Community 6 - "KOL Profiling & RAG (v2)"
Cohesion: 0.11
Nodes (22): BUG: Competitor data hallucination, ChromaDB Vector Store, RAG (Retrieval-Augmented Generation), kol_profiling_agent (v2), ClinicalEvidenceRAG (hybrid BM25+vector+rerank), Response, KOLProfile dataclass, SKILL_01 MSL Intelligence Core (+14 more)

### Community 7 - "Epidemiology & PubMed Tools"
Cohesion: 0.12
Nodes (20): Any, Any, _extract_enrollment_total(), fetch_epidemiology_data(), _format_pub_citations(), Epidemiology Tools Collects disease epidemiology data for a given indication usi, Sum enrollment figures from trial records as a patient-population proxy., Build citation strings from PubMed records. (+12 more)

### Community 8 - "Agent Messages Schema"
Cohesion: 0.08
Nodes (25): AgentMessage, AIGeneratedContent, AnalysisRequest, AnalysisResult, create_agent_message(), Agent Messages Schema Message types that agents use to communicate within the La, Error that occurred during workflow execution, Content generated by an LLM within an agent (+17 more)

### Community 9 - "PDF Brief Generator"
Cohesion: 0.16
Nodes (24): _build_clinical_evidence(), _build_competitive_position(), _build_discovery_questions(), _build_footer(), _build_header(), _build_objections(), _build_styles(), _build_talking_points() (+16 more)

### Community 10 - "Synthesis Agent"
Cohesion: 0.14
Nodes (22): format_competitor_context(), format_icp_context(), format_market_context(), format_messaging_context(), format_payer_context(), format_string(), format_timeline(), get_default_strategy_data() (+14 more)

### Community 11 - "ICP Definition Agent"
Cohesion: 0.16
Nodes (19): format_icp_description(), get_default_buying_committee(), get_default_icp_data(), icp_definition_agent(), ICP Definition Agent Defines Ideal Customer Profile based on market and competit, ICP Definition Agent Node          Defines Ideal Customer Profile (buying person, Format ICP dictionary into readable description, Return default buying committee structure (+11 more)

### Community 12 - "API Cache Manager"
Cohesion: 0.12
Nodes (11): CacheManager, Cache Manager — SKILL_05 In-process TTL cache for API responses. Prevents redund, Thread-safe in-process TTL dictionary cache., Returns a stable cache key from api_type + args.         Example: make_key("pubm, Return cached value if key exists and has not expired.         Deletes expired e, Store value with expiry = now + ttl seconds., Delete all cache entries whose key was built with drug_name.         Returns cou, Store value with raw_key metadata (enables clear_drug()). (+3 more)

### Community 13 - "Architecture Diagram Flow"
Cohesion: 0.15
Nodes (20): Agent 1 - Market Research, Agent 2 - Payer Intelligence, Agent 3 - Competitor Analysis, Agent 4 - ICP Definition, Agent 5 - Messaging & Positioning, Agent 6 - GTM Synthesis, Claude Sonnet 4 (LLM Core), Competitor Data (Market Share, Positioning) (+12 more)

### Community 14 - "FDA Tools (Unused)"
Cohesion: 0.20
Nodes (12): BUG: fda_tools.py never called, Any, FDAClient, get_adverse_events(), get_drug_approvals(), get_recalls(), FDA Tools Integration with FDA OpenFDA API for drug approval data, Search for adverse events (+4 more)

### Community 15 - "Product Vision & Domain"
Cohesion: 0.12
Nodes (16): Closed-Loop MSL Intelligence, Evidentia MSL Intelligence Platform, HCP (Healthcare Professional), KOL Influence Tier (Tier 1/2/3), KOL (Key Opinion Leader), LangGraph StateGraph Shared-State Pattern, MSL (Medical Science Liaison), Parallel Agent Orchestration (+8 more)

### Community 16 - "Product Doc PDF Generator"
Cohesion: 0.24
Nodes (15): build_pdf(), build_styles(), callout_box(), comparison_table(), cover_page(), divider(), highlight_box(), Generate Evidentia product document as PDF. Run: python3 generate_pdf.py (+7 more)

### Community 17 - "GTM Workflow Orchestration"
Cohesion: 0.17
Nodes (11): create_gtm_workflow(), GTMWorkflow, GTM Workflow - Fixed for async execution with proper state handling, Synchronous wrapper - runs async code in sync context, GTM Workflow Orchestrator, Run the full GTM workflow.          Args:             drug_name: Drug being anal, run_gtm_analysis_sync(), get_logger() (+3 more)

### Community 18 - "Competitor Analysis Agent"
Cohesion: 0.22
Nodes (15): get_claude(), competitor_analysis_agent(), get_default_competitor_data(), Competitor Analysis Agent Analyzes competitor landscape, positioning, and market, Return default competitor data when synthesis fails, Competitor Analysis Agent Node          Analyzes competitor drugs, positioning,, CompetitorAnalysisData, CompetitorData (+7 more)

### Community 19 - "Ollama LLM Provider"
Cohesion: 0.23
Nodes (9): get_llm(), LLMClient, LLMProvider, LLM Provider - Uses Ollama (local, free, zero API cost), Available LLM providers, LLM client using Ollama (local inference, zero cost), Invoke LLM using Ollama (runs locally, zero cost), Get LLM client (uses Ollama by default) (+1 more)

### Community 20 - "Structured Logging"
Cohesion: 0.20
Nodes (9): JSONFormatter, log_agent_execution(), Logging configuration for GTM Simulator Sets up structured logging for the appli, Log agent execution details          Args:         agent_name: Name of agent, Custom formatter that outputs JSON, Format log record as JSON, Set up logging configuration          Args:         name: Logger name         lo, setup_logging() (+1 more)

### Community 21 - "Data Quality & Memory (v2)"
Cohesion: 0.22
Nodes (10): BUG: Fragile JSON parsing (re.search), BUG: No session persistence (state lost on refresh), CacheManager (TTL API cache), Data Confidence Badge, Do Not Say Compliance Guardrails, Pydantic JSON Validation, SQLite Structured Persistence (evidentia.db), memory_retrieval_agent (v2) (+2 more)

### Community 22 - "Input Validator"
Cohesion: 0.20
Nodes (6): InputValidator, Input Validator — SKILL_05 Validates user-supplied inputs at Streamlit UI bounda, Validates drug name, indication, and field notes inputs., Returns cleaned drug name or raises ValueError.         Rules: non-empty, ≥2 cha, Returns cleaned indication or raises ValueError.         Rules: non-empty, ≥3 ch, Returns cleaned field notes or raises ValueError.         Rules: non-empty, 10–1

### Community 23 - "GTMState Core"
Cohesion: 0.22
Nodes (6): CLAUDE.md — Project Instructions, GTMState, Central State Machine for LangGraph workflow          All 6 agents read from and, Mark agent as completed, Convert state to dictionary for serialization, Any

### Community 24 - "Field Insight & Territory (v2)"
Cohesion: 0.28
Nodes (9): Field Insight, Insight Categories (10 types), Territory Intelligence, field_synthesis_agent (v2), insight_extraction_agent (v2), FieldInsight dataclass, TerritoryIntelligence dataclass, SKILL_02 Insight Capture Engine (+1 more)

### Community 25 - "GTM Output Document"
Cohesion: 0.29
Nodes (5): GTMOutputDocument, Complete GTM Strategy Output Document, Convert to dictionary for JSON export, Generate human-readable summary, Any

### Community 26 - "UI Chart Components"
Cohesion: 0.29
Nodes (5): competitor_positioning_scatter(), market_sizing_waterfall(), Reusable Streamlit UI components, Create TAM/SAM/SOM waterfall chart, Create competitor positioning scatter plot

### Community 27 - "KOL Engagement Tracking (v2)"
Cohesion: 0.60
Nodes (5): KOL Coverage Gap, Engagement Quality Score (0-10), engagement_scoring_agent (v2), KOLInteraction dataclass, SKILL_03 KOL Engagement Tracker

## Knowledge Gaps
- **32 isolated node(s):** `docker-entrypoint.sh script`, `Config`, `ValidationResult`, `Any`, `Any` (+27 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_logger()` connect `GTM Workflow Orchestration` to `Payer Intelligence & HTA`, `Streamlit UI Layer`, `Messaging & Talking Points`, `Market Research Agent`, `LLM Manager`, `KOL Profiling & RAG (v2)`, `Epidemiology & PubMed Tools`, `Synthesis Agent`, `ICP Definition Agent`, `FDA Tools (Unused)`, `Competitor Analysis Agent`, `Structured Logging`?**
  _High betweenness centrality (0.195) - this node is a cross-community bridge._
- **Why does `get_claude()` connect `Competitor Analysis Agent` to `Payer Intelligence & HTA`, `Streamlit UI Layer`, `Messaging & Talking Points`, `Market Research Agent`, `LLM Manager`, `Synthesis Agent`, `ICP Definition Agent`?**
  _High betweenness centrality (0.151) - this node is a cross-community bridge._
- **Why does `GTMState` connect `GTMState Core` to `Payer Intelligence & HTA`, `Messaging & Talking Points`, `Market Research Agent`, `Agent Messages Schema`, `Synthesis Agent`, `ICP Definition Agent`, `GTM Workflow Orchestration`, `Competitor Analysis Agent`?**
  _High betweenness centrality (0.122) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `GTMState` (e.g. with `GTMWorkflow` and `MSLTalkingPoints`) actually correct?**
  _`GTMState` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Generate architecture diagram as PNG using graphviz`, `Debug script to catch startup errors`, `docker-entrypoint.sh script` to the rest of the system?**
  _249 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Payer Intelligence & HTA` be split into smaller, more focused modules?**
  _Cohesion score 0.06918238993710692 - nodes in this community are weakly interconnected._
- **Should `Streamlit UI Layer` be split into smaller, more focused modules?**
  _Cohesion score 0.06560283687943262 - nodes in this community are weakly interconnected._