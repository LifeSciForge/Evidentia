import requests
from typing import Dict
from datetime import datetime

class ClinicalTrialsAPI:
    """Fetch verified clinical trial data from ClinicalTrials.gov"""
    
    BASE_URL = "https://clinicaltrials.gov/api/query/full_studies"
    
    def search(self, drug_name: str, indication: str, max_results: int = 20) -> Dict:
        """Search for trials"""
        
        try:
            params = {
                "expr": f"{drug_name} AND {indication}",
                "fmt": "json",
                "pageSize": min(max_results, 100)
            }
            
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            trials = []
            for study in data.get("FullStudiesResponse", {}).get("NStudiesReturned", []):
                protocol = study.get("ProtocolSection", {})
                nct_id = protocol.get("IdentificationModule", {}).get("nctId", "")
                
                trial = {
                    "nct_id": nct_id,
                    "title": protocol.get("IdentificationModule", {}).get("briefTitle", ""),
                    "status": protocol.get("StatusModule", {}).get("overallStatus", ""),
                    "phase": protocol.get("DesignModule", {}).get("phases", [""])[0],
                    "url": f"https://clinicaltrials.gov/ct2/show/{nct_id}",
                    "source": "ClinicalTrials.gov",
                    "verified": True
                }
                trials.append(trial)
            
            return {
                "status": "success",
                "trials_found": len(trials),
                "trials": trials,
                "source": "ClinicalTrials.gov",
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "trials": []
            }


if __name__ == "__main__":
    api = ClinicalTrialsAPI()
    result = api.search("ivonescimab", "NSCLC", max_results=5)
    print(f"Found {result['trials_found']} trials")
    for trial in result['trials'][:2]:
        print(f"- {trial['title']}")
