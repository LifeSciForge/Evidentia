"""
ClinicalTrials.gov API Tools
"""

import requests
from typing import Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.core.logger import get_logger

logger = get_logger(__name__)

BASE_URL = "https://clinicaltrials.gov/api/v2/studies"


class ClinicalTrialsClient:
    """Client for ClinicalTrials.gov API v2"""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "GTM-Simulator/1.0"
        })

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        reraise=True,
    )
    def _get_with_retry(self, url: str, params: dict) -> requests.Response:
        response = self.session.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response

    def search_trials(
        self,
        drug_name: str,
        condition: str,
        status: str = "RECRUITING,ACTIVE_NOT_RECRUITING,ENROLLING_BY_INVITATION",
        phase: str = "PHASE2,PHASE3,PHASE4",
        max_results: int = 50,
    ) -> Dict[str, Any]:
        """
        Search for clinical trials by drug and condition
        Using ClinicalTrials.gov API v2 (no bracket syntax)
        """
        try:
            query = f"{drug_name} {condition}"

            params = {
                "query.term": query,
                "filter.overallStatus": status,
                "pageSize": min(max_results, 100),
                "sort": "LastUpdatePostDate"
            }

            logger.info(f"Searching ClinicalTrials.gov for: {query}")
            response = self._get_with_retry(self.base_url, params)
            
            data = response.json()
            trials = data.get("studies", [])
            
            logger.info(f"Found {len(trials)} trials")
            
            # Parse trials
            parsed_trials = []
            for trial in trials[:max_results]:
                parsed = self._parse_trial(trial)
                if parsed:  # Only add if parsing was successful
                    parsed_trials.append(parsed)
            
            return {
                "success": True,
                "total_results": len(trials),
                "returned_results": len(parsed_trials),
                "trials": parsed_trials,
                "query": {
                    "drug_name": drug_name,
                    "condition": condition
                }
            }
            
        except Exception as e:
            logger.error(f"ClinicalTrials.gov search error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "total_results": 0,
                "returned_results": 0,
                "trials": []
            }
    
    def get_trial_details(self, nct_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific trial"""
        try:
            url = f"{self.base_url}/{nct_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return {
                "success": True,
                "trial": self._parse_trial(data)
            }
        except Exception as e:
            logger.error(f"Error fetching trial {nct_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_trials_by_sponsor(self, sponsor_name: str, max_results: int = 20) -> Dict[str, Any]:
        """Get trials by sponsor"""
        try:
            params = {
                "query.term": sponsor_name,
                "pageSize": min(max_results, 100)
            }
            
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            trials = data.get("studies", [])
            
            parsed_trials = []
            for trial in trials[:max_results]:
                parsed = self._parse_trial(trial)
                if parsed:
                    parsed_trials.append(parsed)
            
            return {
                "success": True,
                "total_results": len(trials),
                "trials": parsed_trials
            }
        except Exception as e:
            logger.error(f"Error fetching sponsor trials: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "trials": []
            }
    
    def _parse_trial(self, trial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse trial data from API response"""
        try:
            protocol = trial_data.get("protocolSection", {})
            id_module = protocol.get("identificationModule", {})
            status_module = protocol.get("statusModule", {})
            recruitment = protocol.get("recruitmentModule", {})
            design = protocol.get("designModule", {})
            
            # Extract primary endpoints
            outcomes_module = protocol.get("outcomesModule", {})
            primary_outcomes = outcomes_module.get("primaryOutcomes", [])
            primary_endpoint = "N/A"
            if primary_outcomes:
                primary_endpoint = primary_outcomes[0].get("measure", "N/A")
            
            # Generate key insight for MSL
            phase = design.get("phases", [""])[0] if design.get("phases") else ""
            status = status_module.get("overallStatus", "")
            key_insight = f"{phase} study, {status}. {primary_endpoint}"
            
            return {
                "nct_id": id_module.get("nctId", "N/A"),
                "title": id_module.get("briefTitle", "N/A"),
                "status": status_module.get("overallStatus", "N/A"),
                "phase": phase if phase else "N/A",
                "enrollment": recruitment.get("enrollmentCount", 0),
                "sponsor": id_module.get("organization", {}).get("fullName", "N/A"),
                "start_date": status_module.get("startDateStruct", {}).get("date", "N/A"),
                "completion_date": status_module.get("completionDateStruct", {}).get("date", "N/A"),
                "primary_endpoint": primary_endpoint,
                "key_insight": key_insight
            }
        except Exception as e:
            logger.error(f"Error parsing trial: {str(e)}")
            return {}


# Convenience functions
def search_clinical_trials(
    drug_name: str,
    condition: str,
    max_results: int = 50
) -> Dict[str, Any]:
    """Convenience function to search trials"""
    client = ClinicalTrialsClient()
    return client.search_trials(drug_name, condition, max_results=max_results)


def get_trial(nct_id: str) -> Dict[str, Any]:
    """Convenience function to get single trial"""
    client = ClinicalTrialsClient()
    return client.get_trial_details(nct_id)


def get_sponsor_trials(sponsor_name: str, max_results: int = 20) -> Dict[str, Any]:
    """Convenience function to get trials by sponsor"""
    client = ClinicalTrialsClient()
    return client.get_trials_by_sponsor(sponsor_name, max_results)
