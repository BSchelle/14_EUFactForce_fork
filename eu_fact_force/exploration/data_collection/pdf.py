import xml.etree.ElementTree as ET
from typing import Optional

import requests

# ---------------------------------------------------------------------------
# PDF URL resolution — one function per source
# ---------------------------------------------------------------------------


def get_pdf_url_from_hal(doi: str) -> Optional[str]:
    """Return the PDF URL for a DOI from HAL, or None if not found."""
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
        return None


def get_pdf_url_from_openalex(doi: str) -> Optional[str]:
    """Return the PDF URL for a DOI from OpenAlex (best open-access location), or None if not found."""
    try:
        response = requests.get(f"https://api.openalex.org/works/doi:{doi}", timeout=10)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return (response.json().get("best_oa_location") or {}).get("pdf_url")
    except Exception as e:
        print(f"OpenAlex error: {e}")
        return None


def get_pdf_url_from_crossref(doi: str) -> Optional[str]:
    """Return the PDF URL for a DOI from CrossRef (first link with content-type pdf), or None if not found."""
    try:
        response = requests.get(f"https://api.crossref.org/works/doi/{doi}", timeout=10)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        for link in response.json().get("message", {}).get("link", []):
            if "pdf" in link.get("content-type", "") and link.get("URL"):
                return link["URL"]
        return None
    except Exception as e:
        print(f"CrossRef error: {e}")
        return None

# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def download_pdf(doi: str, output_path: str) -> bool:
    """Try to download the PDF for a DOI to output_path, falling back through HAL → OpenAlex → CrossRef.

    Returns True if a valid PDF was saved, False otherwise.
    """
    sources = [
        ("HAL",       get_pdf_url_from_hal),
        ("OpenAlex",  get_pdf_url_from_openalex),
        ("CrossRef",  get_pdf_url_from_crossref),
    ]
    for name, get_url in sources:
        pdf_url = get_url(doi)
        if not pdf_url:
            print(f"PDF not found in {name}.")
            continue
        print(f"Trying PDF URL from {name}: {pdf_url}")
        if _download_url(pdf_url, output_path):
            return True
    print("No PDF found in any source.")
    return False


def _download_url(url: str, output_path: str) -> bool:
    """Download a URL to output_path. Returns False if the content is not a valid PDF."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        if not response.content.startswith(b"%PDF"):
            print(f"Content at {url} is not a valid PDF (possibly a paywall page).")
            return False
        with open(output_path, "wb") as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Download the PDF of an article from its DOI.")
    parser.add_argument("--doi", required=True)
    parser.add_argument("--output-dir", default="pdf")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    doi_slug = args.doi.replace("/", "_").replace(".", "_")
    download_pdf(args.doi, os.path.join(args.output_dir, f"{doi_slug}.pdf"))
