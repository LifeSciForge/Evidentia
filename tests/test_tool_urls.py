from src.service.tools.clinical_trials_tools import nct_url
from src.service.tools.pubmed_tools import pmid_url


def test_nct_url():
    assert nct_url("NCT04685135") == "https://clinicaltrials.gov/study/NCT04685135"


def test_pmid_url():
    assert pmid_url("36546659") == "https://pubmed.ncbi.nlm.nih.gov/36546659/"
