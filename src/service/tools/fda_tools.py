"""
FDA Tools
Integration with FDA OpenFDA API for drug approval data
"""

import requests
from typing import List, Dict, Any, Optional
from src.core.logger import get_logger

logger = get_logger(__name__)

FDA_API_BASE = "https://api.fda.gov/drug"


class FDAClient:
    """Client for FDA OpenFDA API"""
    
    def __init__(self):
        self.base_url = FDA_API_BASE
        self.session = requests.Session()
    
    def search_drug_approvals(
        self,
        drug_name: str,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Search for drug approvals
        
        Args:
            drug_name: Name of the drug
            max_results: Maximum results
            
        Returns:
            Approval information
        """
        try:
            logger.info(f"Searching FDA approvals for: {drug_name}")
            
            # Search NDAs
            url = f"{self.base_url}/nda.json"
            params = {
                "search": f"applicant:{drug_name} OR generic_name:{drug_name}",
                "limit": max_results
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            # Parse approvals
            approvals = []
            for result in results:
                parsed = self._parse_approval(result)
                if parsed:
                    approvals.append(parsed)
            
            return {
                "success": True,
                "drug_name": drug_name,
                "total_approvals": len(approvals),
                "approvals": approvals
            }
        except Exception as e:
            logger.error(f"Error searching FDA approvals: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "approvals": []
            }
    
    def _parse_approval(self, approval_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse FDA approval data"""
        try:
            return {
                "nda_number": approval_data.get("application_number", ""),
                "drug_name": approval_data.get("generic_name", ""),
                "applicant": approval_data.get("applicant", ""),
                "approval_type": approval_data.get("application_type", ""),
                "submission_date": approval_data.get("submission_date", ""),
                "approval_date": approval_data.get("approval_date", ""),
                "active_ingredients": approval_data.get("active_ingredients", []),
                "dosage_form": approval_data.get("dosage_form", "")
            }
        except Exception as e:
            logger.error(f"Error parsing approval: {str(e)}")
            return None
    
    def search_recalls(
        self,
        drug_name: str,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """Search for drug recalls"""
        try:
            logger.info(f"Searching FDA recalls for: {drug_name}")
            
            url = f"{self.base_url}/enforcement.json"
            params = {
                "search": f"drug_name:{drug_name}",
                "limit": max_results
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            recalls = []
            for recall in results:
                recalls.append({
                    "recall_class": recall.get("recall_class", ""),
                    "reason": recall.get("reason_for_recall", ""),
                    "status": recall.get("status", ""),
                    "date": recall.get("recall_initiation_date", ""),
                    "product": recall.get("product_description", "")
                })
            
            return {
                "success": True,
                "drug_name": drug_name,
                "total_recalls": len(recalls),
                "recalls": recalls
            }
        except Exception as e:
            logger.error(f"Error searching recalls: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "recalls": []
            }
    
    def search_adverse_events(
        self,
        drug_name: str,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """Search for adverse events"""
        try:
            logger.info(f"Searching adverse events for: {drug_name}")
            
            url = f"{self.base_url}/event.json"
            params = {
                "search": f"patient.drug.generic_name:{drug_name}",
                "limit": max_results
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            events = []
            for event in results[:max_results]:
                if "reactions" in event:
                    for reaction in event.get("reactions", []):
                        events.append({
                            "adverse_event": reaction.get("reactionmeddrapt", ""),
                            "outcome": reaction.get("reactionoutcome", ""),
                            "severity": reaction.get("reactionmeddraversionpt", "")
                        })
            
            return {
                "success": True,
                "drug_name": drug_name,
                "total_adverse_events": len(events),
                "adverse_events": events[:max_results]
            }
        except Exception as e:
            logger.error(f"Error searching adverse events: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "adverse_events": []
            }


# Convenience functions
def get_drug_approvals(drug_name: str, max_results: int = 10) -> Dict[str, Any]:
    """Get drug approvals"""
    client = FDAClient()
    return client.search_drug_approvals(drug_name, max_results)


def get_recalls(drug_name: str, max_results: int = 10) -> Dict[str, Any]:
    """Get drug recalls"""
    client = FDAClient()
    return client.search_recalls(drug_name, max_results)


def get_adverse_events(drug_name: str, max_results: int = 10) -> Dict[str, Any]:
    """Get adverse events"""
    client = FDAClient()
    return client.search_adverse_events(drug_name, max_results)