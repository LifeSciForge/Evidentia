"""
Tavily Web Search Tools
"""

from typing import Dict, Any
from tavily import TavilyClient
from src.core.settings import settings
from src.core.logger import get_logger

logger = get_logger(__name__)


class TavilySearchClient:
    """Client for Tavily web search"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.TAVILY_API_KEY
        self.client = TavilyClient(api_key=self.api_key)
    
    def search(
        self,
        query: str,
        search_depth: str = "advanced",
        max_results: int = 5
    ) -> Dict[str, Any]:
        """General web search"""
        try:
            result = self.client.search(query, max_results=max_results)
            return {
                "success": True,
                "answer": result.get("answer", ""),
                "results": result.get("results", [])
            }
        except Exception as e:
            logger.error(f"Tavily search error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "answer": "",
                "results": []
            }
    
    def search_competitor_news(self, competitor_name: str) -> Dict[str, Any]:
        """Search competitor news"""
        query = f"{competitor_name} news announcement partnership 2025 2026"
        return self.search(query, max_results=5)
    
    def search_drug_news(self, drug_name: str) -> Dict[str, Any]:
        """Search drug news"""
        query = f"{drug_name} FDA approval clinical trial news 2025"
        return self.search(query, max_results=5)
    
    def search_regulatory_updates(self, drug_name: str, indication: str) -> Dict[str, Any]:
        """Search regulatory updates"""
        query = f"{drug_name} {indication} FDA EMA regulatory decision 2025"
        return self.search(query, max_results=5)
    
    def search_pricing_information(self, drug_name: str, max_results: int = 5) -> Dict[str, Any]:
        """Search pricing information"""
        query = f"{drug_name} price cost USD therapy 2025"
        return self.search(query, max_results=max_results)
    
    def search_payer_coverage(self, drug_name: str, region: str = "US", max_results: int = 5) -> Dict[str, Any]:
        """Search payer coverage information"""
        query = f"{drug_name} {region} payer coverage reimbursement insurance 2025"
        return self.search(query, max_results=max_results)
    
    def search_market_analysis(self, indication: str, max_results: int = 5) -> Dict[str, Any]:
        """Search for market analysis"""
        query = f"{indication} market size forecast CAGR growth 2025-2030"
        return self.search(query, max_results=max_results)
    
    def search_clinical_evidence(self, drug_name: str, indication: str, max_results: int = 5) -> Dict[str, Any]:
        """Search for clinical evidence"""
        query = f"{drug_name} clinical efficacy safety {indication} Phase 3 results"
        return self.search(query, max_results=max_results)


# Convenience functions
def tavily_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """General Tavily search"""
    client = TavilySearchClient()
    return client.search(query, max_results=max_results)


def search_competitor_news(competitor_name: str) -> Dict[str, Any]:
    """Search competitor news"""
    client = TavilySearchClient()
    return client.search_competitor_news(competitor_name)


def search_drug_news(drug_name: str) -> Dict[str, Any]:
    """Search drug news"""
    client = TavilySearchClient()
    return client.search_drug_news(drug_name)


def search_regulatory(drug_name: str, indication: str) -> Dict[str, Any]:
    """Search regulatory updates"""
    client = TavilySearchClient()
    return client.search_regulatory_updates(drug_name, indication)


def search_pricing_information(drug_name: str, max_results: int = 5) -> Dict[str, Any]:
    """Search pricing information"""
    client = TavilySearchClient()
    return client.search_pricing_information(drug_name, max_results)


def search_market_analysis(indication: str, max_results: int = 5) -> Dict[str, Any]:
    """Search for market analysis"""
    client = TavilySearchClient()
    return client.search_market_analysis(indication, max_results)


def search_clinical_evidence(drug_name: str, indication: str, max_results: int = 5) -> Dict[str, Any]:
    """Search for clinical evidence"""
    client = TavilySearchClient()
    return client.search_clinical_evidence(drug_name, indication, max_results)


def search_payer_coverage(drug_name: str, region: str = "US", max_results: int = 5) -> Dict[str, Any]:
    """Search for payer coverage information"""
    client = TavilySearchClient()
    return client.search_payer_coverage(drug_name, region, max_results)
