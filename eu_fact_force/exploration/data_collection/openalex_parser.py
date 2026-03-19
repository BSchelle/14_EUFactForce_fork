from metadata_parser import MetadataParser
import requests
from typing import Optional


class OpenAlexMetadataParser(MetadataParser):
    def __init__(self):
        super().__init__()
        self.url = "https://api.openalex.org/works/doi:{doi}"
        self.cited_articles_url = "https://api.openalex.org/works?filter=ids.openalex:{ids}&select=id,doi&per-page=200"

    def _get_authors(self, doc):
        return [
            a.get("raw_author_name")
            for a in doc.get("authorships", [])
            if a.get("raw_author_name")
        ]

    def _get_journal(self, doc):
        return (
            (doc.get("primary_location") or {})
            .get("source", {})
            .get("host_organization_name")
        )

    def _get_link(self, doc):
        return (doc.get("best_oa_location") or {}).get("pdf_url")

    def _get_keywords(self, doc):
        seen = set()
        result = []
        for item in doc.get("mesh", []):
            name = item.get("descriptor_name")
            if name and name not in seen:
                seen.add(name)
                result.append(name)
        return result or None

    def _get_cited_articles(self, doc):
        referenced_works = doc.get("referenced_works", [])
        if not referenced_works:
            return []
        ids = [url.split("/")[-1] for url in referenced_works]
        response = requests.get(self.cited_articles_url.format(ids="|".join(ids)))
        response.raise_for_status()
        return [
            r["doi"].removeprefix("https://doi.org/")
            for r in response.json().get("results", [])
            if r.get("doi")
        ]

    def _get_doi(self, doc):
        doi = doc.get("doi") or ""
        return doi.removeprefix("https://doi.org/") or None

    def _get_status(self, doc):
        return "retracted" if doc.get("is_retracted") else "published"

    def get_metadata(self, doi: str) -> dict:
        response = requests.get(self.url.format(doi=doi))
        if response.status_code == 404:
            return {"found": False}
        response.raise_for_status()
        doc = response.json()

        if not doc:
            return {"found": False}

        return {
            "found":           True,
            "article name":    doc.get("title"),
            "authors":         self._get_authors(doc),
            "journal":         self._get_journal(doc),
            "publish date":    doc.get("publication_date"),
            "link":            self._get_link(doc),
            "keywords":        self._get_keywords(doc),
            "cited articles":  self._get_cited_articles(doc),
            "doi":             self._get_doi(doc),
            "article type":    doc.get("type"),
            "open access":     (doc.get("open_access") or {}).get("is_oa"),
            "status":          self._get_status(doc),
        }

    def get_pdf_url(self, doi) -> Optional[str]:
        """Return the PDF URL for a DOI from OpenAlex (best open-access location), or None if not found."""
        try:
            response = requests.get(f"https://api.openalex.org/works/doi:{doi}", timeout=10)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            doc = response.json()
            location = doc.get("best_oa_location") or {}
            return location.get("pdf_url") or (doc.get("open_access") or {}).get("oa_url")
        except Exception as e:
            print(f"OpenAlex error: {e}")
            return None


if __name__ == "__main__":
    parser = OpenAlexMetadataParser()
    doi = "10.1056/nejmoa2035389"
    metadata = parser.get_metadata(doi)
    print(metadata)
    parser.download_pdf(doi)
