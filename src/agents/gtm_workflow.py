"""
GTM Workflow - Fixed for async execution with proper state handling
"""

from langgraph.graph import StateGraph, END
from typing import Callable, Dict, Any, List, Optional
from dataclasses import fields as dataclass_fields
from src.schema.gtm_state import GTMState
from src.agents.gtm_agents.market_research_agent import market_research_agent
from src.agents.gtm_agents.payer_intelligence_agent import payer_intelligence_agent
from src.agents.gtm_agents.competitor_analysis_agent import competitor_analysis_agent
from src.agents.gtm_agents.icp_definition_agent import icp_definition_agent
from src.agents.gtm_agents.messaging_agent import messaging_agent
from src.agents.gtm_agents.synthesis_agent import synthesis_agent
from src.core.logger import get_logger
import asyncio

logger = get_logger(__name__)


class GTMWorkflow:
    """GTM Workflow Orchestrator"""
    
    def __init__(self):
        self.graph = None
        self.app = None
        self._build_graph()
    
    def _build_graph(self):
        logger.info("🏗️ Building GTM Workflow Graph...")
        self.graph = StateGraph(GTMState)
        
        logger.info("📌 Adding agent nodes...")
        self.graph.add_node("market_research", market_research_agent)
        self.graph.add_node("payer_intelligence", payer_intelligence_agent)
        self.graph.add_node("competitor_analysis", competitor_analysis_agent)
        self.graph.add_node("icp_definition", icp_definition_agent)
        self.graph.add_node("messaging", messaging_agent)
        self.graph.add_node("synthesis", synthesis_agent)
        
        logger.info("🔗 Adding workflow edges...")
        self.graph.add_edge("market_research", "payer_intelligence")
        self.graph.add_edge("payer_intelligence", "competitor_analysis")
        self.graph.add_edge("competitor_analysis", "icp_definition")
        self.graph.add_edge("icp_definition", "messaging")
        self.graph.add_edge("messaging", "synthesis")
        self.graph.add_edge("synthesis", END)
        
        self.graph.set_entry_point("market_research")
        
        logger.info("💾 Compiling workflow...")
        self.app = self.graph.compile()
        
        logger.info("✅ GTM Workflow Graph built successfully")
    
    async def run(
        self,
        drug_name: str,
        indication: str,
        current_doctor: str = None,
        current_hospital: str = None,
        progress_callback: Optional[Callable[[str, List[str], int], None]] = None,
    ) -> GTMState:
        """
        Run the full GTM workflow.

        Args:
            drug_name: Drug being analysed.
            indication: Disease indication.
            current_doctor: Optional KOL name for MSL talking points.
            current_hospital: Optional institution name.
            progress_callback: Optional callable invoked after each agent
                completes.  Signature:
                    callback(agent_name: str,
                             agents_completed: List[str],
                             progress_percentage: int) -> None
                Runs on the event-loop thread — keep it non-blocking.
        """
        logger.info(f"Starting GTM Workflow for {drug_name} in {indication}")

        initial_state = GTMState(
            drug_name=drug_name,
            indication=indication,
            current_doctor=current_doctor,
            current_hospital=current_hospital,
        )

        try:
            logger.info("⏳ Executing workflow (async, streaming)...")
            final_state = initial_state
            seen_agents: List[str] = []

            # stream_mode="values" yields the full state after every node.
            async for snapshot in self.app.astream(
                initial_state, stream_mode="values"
            ):
                # LangGraph may return a raw dict or a GTMState instance.
                # Filter to known dataclass fields to avoid TypeError from
                # any internal LangGraph metadata keys in the snapshot dict.
                if isinstance(snapshot, dict):
                    known = {f.name for f in dataclass_fields(GTMState)}
                    current_state = GTMState(**{k: v for k, v in snapshot.items() if k in known})
                else:
                    current_state = snapshot

                final_state = current_state

                # Detect which agent just completed by comparing lists.
                newly_done = [
                    a for a in current_state.agents_completed
                    if a not in seen_agents
                ]
                if newly_done and progress_callback:
                    agent_name = newly_done[-1]
                    try:
                        progress_callback(
                            agent_name,
                            list(current_state.agents_completed),
                            current_state.progress_percentage,
                        )
                    except Exception as cb_exc:
                        # Never let a UI callback crash the workflow.
                        logger.warning(
                            f"progress_callback raised an error: {cb_exc}"
                        )

                seen_agents = list(current_state.agents_completed)

            logger.info("✅ Workflow completed successfully")
            logger.info(f"📊 Agents completed: {final_state.agents_completed}")
            logger.info(f"🎯 Progress: {final_state.progress_percentage}%")

            return final_state

        except Exception as e:
            logger.error(f"❌ Workflow execution failed: {str(e)}")
            initial_state.add_error("Workflow", str(e))
            initial_state.agent_status = "error"
            return initial_state


def create_gtm_workflow() -> GTMWorkflow:
    return GTMWorkflow()


def run_gtm_analysis_sync(drug_name: str, indication: str) -> GTMState:
    """Synchronous wrapper - runs async code in sync context"""
    workflow = create_gtm_workflow()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(workflow.run(drug_name, indication))
        return result
    finally:
        loop.close()
