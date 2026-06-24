"""
Hospital database for the Evidentia MSL Intelligence Platform.

HOSPITALS is a dict keyed by hospital name, each value containing
'location' (str) and 'doctors' (list[str]).

This is a static seed list of real US cancer centers. In v2, this
will be replaced by a SQLite table (see SKILL_06).
"""

HOSPITALS = {
    "MD Anderson Cancer Center": {
        "location": "Houston, TX",
        "doctors": [
            "Dr. Roy S. Herbst (Thoracic Medical Oncology)",
            "Dr. Carolyn Melt (Lung Cancer, Immunotherapy)",
            "Dr. Vassiliki A. Papadimitrakopoulou (Thoracic Oncology)",
            "Dr. John V. Heymach (Thoracic Medical Oncology)"
        ]
    },
    "Memorial Sloan Kettering Cancer Center": {
        "location": "New York, NY",
        "doctors": [
            "Dr. Matthew D. Hellmann (Thoracic Oncology)",
            "Dr. Mark G. Kris (Lung Cancer Specialist)",
            "Dr. Natasha Rekhtman (Pulmonary Pathology)",
            "Dr. Geoffrey Oxnard (Precision Medicine Oncology)"
        ]
    },
    "Mayo Clinic - Cancer Center": {
        "location": "Rochester, MN",
        "doctors": [
            "Dr. Aaron S. Mansfield (Thoracic Oncology)",
            "Dr. Malini Hocking (Pulmonary & Critical Care)",
            "Dr. Syedain Gulrez (Oncology, Immunotherapy)",
            "Dr. Rajeev Dhupar (Thoracic Surgery & Oncology)"
        ]
    },
    "Cleveland Clinic": {
        "location": "Cleveland, OH",
        "doctors": [
            "Dr. Nathan Pennell (Hematology & Oncology)",
            "Dr. James Stevenson (Thoracic Surgery, Oncology)",
            "Dr. Paul Bunn (Lung Cancer, Clinical Research)",
            "Dr. Afshin Dowlati (Medical Oncology)"
        ]
    },
    "Dana-Farber Cancer Institute": {
        "location": "Boston, MA",
        "doctors": [
            "Dr. Bruce E. Johnson (Lung Cancer Program)",
            "Dr. Pasi A. Jänne (Thoracic Oncology)",
            "Dr. Leena Gandhi (Immunotherapy & Lung Cancer)",
            "Dr. Zofia Piotrowska (Medical Oncology)"
        ]
    },
    "UCSF Medical Center": {
        "location": "San Francisco, CA",
        "doctors": [
            "Dr. Thierry Jahan (Thoracic Oncology)",
            "Dr. Lawrence Shulman (Lung Cancer Specialist)",
            "Dr. Chiyoko Okubo (Oncology, Precision Medicine)",
            "Dr. Adekunle O. Odejimi (Immunotherapy Oncology)"
        ]
    },
    "Johns Hopkins Medical Center": {
        "location": "Baltimore, MD",
        "doctors": [
            "Dr. David Ettinger (Thoracic Oncology)",
            "Dr. Janis M. Taube (Immunotherapy, Pathology)",
            "Dr. Akhil Vaidya (Thoracic Surgery & Oncology)",
            "Dr. Leukaa Sidaway (Lung Cancer Research)"
        ]
    },
    "Stanford Health": {
        "location": "Stanford, CA",
        "doctors": [
            "Dr. Joel W. Neal (Thoracic Oncology)",
            "Dr. Heather Wakelee (Lung Cancer, Immunotherapy)",
            "Dr. Ayokunle Isiaka (Precision Oncology)",
            "Dr. Aparna Raj (Medical Oncology, Clinical Trials)"
        ]
    }
}
