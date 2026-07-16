"""
Registry of legal document sources for the AML compliance corpus.
Update this file when regulations change or new sources become available.
"""
from dataclasses import dataclass, field


@dataclass
class LegalSource:
    name: str        # Becomes law_name in chunk payload
    url: str         # Direct PDF URL or local path relative to project root
    priority: int    # 1 = critical, 2 = important, 3 = supplementary
    file_type: str   # "pdf" | "html"
    notes: str = ""


LEGAL_SOURCES: list[LegalSource] = [
    # Lokalny plik — dostępny bez internetu
    LegalSource(
        name="Ustawa RODO PL 2018",
        url="knowledge_base/D20181000Lj.pdf",
        priority=2,
        file_type="pdf",
        notes="Ustawa z 10 maja 2018 r. o ochronie danych osobowych (Dz.U. 2018 poz. 1000)",
    ),
    # Do odblokowania gdy pobrana lokalnie:
    # LegalSource(
    #     name="Ustawa AML 2018",
    #     url="knowledge_base/D20180723Lj.pdf",
    #     priority=1,
    #     file_type="pdf",
    #     notes="Ustawa z 1 marca 2018 r. o przeciwdziałaniu praniu pieniędzy (Dz.U. 2018 poz. 723)",
    # ),
    # LegalSource(
    #     name="Ustawa AML 2018",
    #     url="https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20180000723/U/D20180723Lj.pdf",
    #     priority=1,
    #     file_type="pdf",
    # ),
]
