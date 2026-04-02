"""
PubMed Tools
Integration with PubMed API via Biopython to fetch literature
"""

from Bio import Entrez
from typing import List, Dict, Any, Optional
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.core.logger import get_logger

logger = get_logger(__name__)

# Configure Entrez
Entrez.email = "gtm-simulator@pharma.ai"


class PubMedClient:
    """Client for PubMed literature search"""

    def __init__(self, email: str = "gtm-simulator@pharma.ai"):
        Entrez.email = email

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def _esearch_with_retry(self, query: str, max_results: int) -> list:
        handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results, sort="date")
        results = Entrez.read(handle)
        handle.close()
        return results.get("IdList", [])

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def _efetch_with_retry(self, id_list: list):
        handle = Entrez.efetch(db="pubmed", id=",".join(id_list), rettype="xml")
        articles = Entrez.read(handle)
        handle.close()
        return articles

    def search_publications(
        self,
        drug_name: str,
        condition: str = None,
        max_results: int = 20,
    ) -> Dict[str, Any]:
        """
        Search PubMed for publications with automatic retry (3 attempts, exponential backoff).
        """
        try:
            if condition:
                query = f'("{drug_name}"[Title/Abstract] OR "{drug_name}"[Drug Name]) AND ("{condition}"[Title/Abstract] OR "{condition}"[MeSH Terms])'
            else:
                query = f'"{drug_name}"[Title/Abstract] OR "{drug_name}"[Drug Name]'

            logger.info(f"Searching PubMed for: {query}")

            id_list = self._esearch_with_retry(query, max_results)
            logger.info(f"Found {len(id_list)} publications")

            if not id_list:
                return {
                    "success": True,
                    "total_results": 0,
                    "publications": [],
                    "query": query
                }

            articles = self._efetch_with_retry(id_list)
            
            # Parse articles
            publications = []
            for article in articles.get("PubmedArticle", []):
                parsed = self._parse_article(article)
                if parsed:
                    publications.append(parsed)
            
            return {
                "success": True,
                "total_results": len(id_list),
                "returned_results": len(publications),
                "publications": publications,
                "query": query
            }
            
        except Exception as e:
            logger.error(f"Error searching PubMed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "publications": []
            }
    
    def _parse_article(self, article: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse PubMed article XML"""
        try:
            medline = article.get("MedlineCitation", {})
            article_info = medline.get("Article", {})
            
            pmid = medline.get("PMID", "")
            title = article_info.get("ArticleTitle", "")
            
            # Authors
            authors_list = article_info.get("AuthorList", [])
            authors = []
            for author in authors_list:
                name = author.get("LastName", "")
                if name:
                    authors.append(name)
            
            # Abstract
            abstract_section = article_info.get("Abstract", {})
            abstract = abstract_section.get("AbstractText", "")
            if isinstance(abstract, list):
                abstract = " ".join(abstract)
            
            # Journal info
            journal = article_info.get("Journal", {})
            journal_title = journal.get("Title", "")
            
            pubdate = article_info.get("ArticleDate", article_info.get("PubDate", {}))
            pub_date = pubdate.get("Year", "") if isinstance(pubdate, dict) else ""
            
            # MeSH terms
            mesh_terms = []
            for mesh_heading in medline.get("MeshHeadingList", []):
                descriptor = mesh_heading.get("DescriptorName", "")
                if descriptor:
                    mesh_terms.append(descriptor)
            
            return {
                "pmid": str(pmid),
                "title": title,
                "authors": authors[:5],  # First 5 authors
                "journal": journal_title,
                "publication_year": pub_date,
                "abstract": abstract[:500] if abstract else "",  # First 500 chars
                "mesh_terms": mesh_terms[:10],  # First 10 MeSH terms
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            }
        except Exception as e:
            logger.error(f"Error parsing article: {str(e)}")
            return None
    
    def search_clinical_trials_publications(
        self,
        drug_name: str,
        indication: str,
        max_results: int = 20
    ) -> Dict[str, Any]:
        """Search for Phase 3 and clinical trial publications"""
        try:
            query = f'("{drug_name}"[Title/Abstract]) AND ("Phase 3"[Title/Abstract] OR "Phase III"[Title/Abstract] OR "clinical trial"[Publication Type])'
            
            handle = Entrez.esearch(
                db="pubmed",
                term=query,
                retmax=max_results,
                sort="date"
            )
            search_results = Entrez.read(handle)
            handle.close()
            
            id_list = search_results.get("IdList", [])
            
            if not id_list:
                return {
                    "success": True,
                    "clinical_trial_publications": 0,
                    "publications": []
                }
            
            handle = Entrez.efetch(
                db="pubmed",
                id=",".join(id_list),
                rettype="xml"
            )
            articles = Entrez.read(handle)
            handle.close()
            
            publications = []
            for article in articles.get("PubmedArticle", []):
                parsed = self._parse_article(article)
                if parsed:
                    publications.append(parsed)
            
            return {
                "success": True,
                "clinical_trial_publications": len(publications),
                "publications": publications
            }
        except Exception as e:
            logger.error(f"Error searching clinical trials: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "publications": []
            }
    
    def search_hta_publications(
        self,
        drug_name: str,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """Search for Health Technology Assessment publications"""
        try:
            query = f'("{drug_name}"[Title/Abstract]) AND ("HTA"[Title/Abstract] OR "health technology assessment"[Title/Abstract] OR "NICE"[Title/Abstract] OR "ICER"[Title/Abstract])'
            
            handle = Entrez.esearch(
                db="pubmed",
                term=query,
                retmax=max_results,
                sort="date"
            )
            search_results = Entrez.read(handle)
            handle.close()
            
            id_list = search_results.get("IdList", [])
            
            if not id_list:
                return {
                    "success": True,
                    "hta_publications": 0,
                    "publications": []
                }
            
            handle = Entrez.efetch(
                db="pubmed",
                id=",".join(id_list),
                rettype="xml"
            )
            articles = Entrez.read(handle)
            handle.close()
            
            publications = []
            for article in articles.get("PubmedArticle", []):
                parsed = self._parse_article(article)
                if parsed:
                    publications.append(parsed)
            
            return {
                "success": True,
                "hta_publications": len(publications),
                "publications": publications
            }
        except Exception as e:
            logger.error(f"Error searching HTA publications: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "publications": []
            }


# Convenience functions
def search_pubmed(
    drug_name: str,
    condition: str = None,
    max_results: int = 20
) -> Dict[str, Any]:
    """Search PubMed for publications"""
    client = PubMedClient()
    return client.search_publications(drug_name, condition, max_results)


def search_clinical_trials_pubs(
    drug_name: str,
    indication: str,
    max_results: int = 20
) -> Dict[str, Any]:
    """Search for clinical trial publications"""
    client = PubMedClient()
    return client.search_clinical_trials_publications(drug_name, indication, max_results)


def search_hta_pubs(
    drug_name: str,
    max_results: int = 10
) -> Dict[str, Any]:
    """Search for HTA publications"""
    client = PubMedClient()
    return client.search_hta_publications(drug_name, max_results)