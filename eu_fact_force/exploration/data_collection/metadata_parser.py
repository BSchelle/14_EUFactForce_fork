from abc import ABC, abstractmethod
import xml.etree.ElementTree as ET
from typing import Optional
from utils import doi_to_id
import os


import requests


class MetadataParser(ABC):
    def __init__(self):
        self.fields_mapping = {
            "article name":  "",
            "authors":       "",
            "journal":       "",
            "publish date":  "",
            "link":          "",
            "keywords":      "",
            "cited articles": "",
            "doi":           "",
            "article type":  "",
            "open access":   "",
            "status":        ""
        }

        self.fields_mapping = {}

    @abstractmethod
    def get_metadata(self, doi: str) -> dict:
        pass

    @abstractmethod
    def get_pdf_url(self, doi: str) -> Optional[str]:
        pass

    def download_pdf(self, doi: str, output_dir: str = 'pdf') -> bool:
        id = doi_to_id(doi)
        output_path = os.path.join(output_dir, f"{id}.pdf")
        
        pdf_url = self.get_pdf_url(doi)
        if not pdf_url:
            print("PDF URL not found.")
            return False
        try:
            response = requests.get(pdf_url, timeout=30)
            response.raise_for_status()
            if not response.content.startswith(b"%PDF"):
                print(f"Content at {pdf_url} is not a valid PDF (possibly a paywall page).")
                return False
            with open(output_path, "wb") as f:
                f.write(response.content)
            return True
        except Exception as e:
            print(f"Download failed: {e}")
            return False


class HALMetadataParser(MetadataParser):
    def __init__(self):
        super().__init__()
        self.url = "https://api.archives-ouvertes.fr/search/?q=doiId_s:{doi}&fl=*"

    def _get_keywords(self, doc):
        return next((doc[key] for key in ["mesh_s", "keyword_s"] if doc.get(key)), None)

    def get_metadata(self, doi: str) -> dict:
        response = requests.get(self.url.format(doi=doi))
        response.raise_for_status()
        docs = response.json().get("response", {}).get("docs", [])

        if not docs:
            return {"found": False}

        doc = docs[0]

        return {
            "found":          True,
            "article name":   doc.get("title_s"),
            "authors":        doc.get("authFullName_s"),
            "journal":        doc.get("journalTitle_s"),
            "publish date":   doc.get("publicationDate_s"),
            "link":           doc.get("uri_s"),
            "keywords":       self._get_keywords(doc),
            "cited articles": None,
            "doi":            doc.get("doiId_s"),
            "article type":   doc.get("docType_s"),
            "open access":    doc.get("openAccess_bool"),
            "status":         None,
        }

    def get_pdf_url(self, doi: str) -> Optional[str]:
        try:
            response = requests.get(
                f"https://api.archives-ouvertes.fr/search/?q=doiId_s:{doi}&wt=xml&fl=uri_s",
                timeout=10,
            )
            response.raise_for_status()
            root = ET.fromstring(response.content)
            if int(root.find(".//result").get("numFound", "0")) == 0:
                return None
            uri_el = root.find(".//str[@name='uri_s']")
            if uri_el is None or not uri_el.text:
                return None
            return f"{uri_el.text}/document"
        except Exception as e:
            print(f"HAL error: {e}")
            return False


if __name__ == "__main__":
    parser = HALMetadataParser()
    doi = "10.26855/ijcemr.2021.01.001"
    metadata = parser.get_metadata(doi)
    success = parser.download_pdf(doi)
    print(metadata)
    print(f"success: {success}")