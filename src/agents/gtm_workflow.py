"""
GTM Workflow - Fixed for async execution with proper state handling
"""

from langgraph.graph import StateGraph, END
from typing import Dict, Any
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
    ) -> GTMState:
        logger.info(f"Starting GTM Workflow for {drug_name} in {indication}")

        initial_state = GTMState(
            drug_name=drug_name,
            indication=indication,
            current_doctor=current_doctor,
            current_hospital=current_hospital,
        )
        
        try:
            logger.info("⏳ Executing workflow (async)...")
            result = await self.app.ainvoke(initial_state)
            
            # Convert dict result back to GTMState if needed
            if isinstance(result, dict):
                logger.info("Converting dict result back to GTMState...")
                final_state = GTMState(**result)
            else:
                final_state = result
            
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
