import argparse
import json
import os

from metadata import fetch_metadata_all_apis
from pdf import download_pdf


def doi_to_id(doi: str) -> str:
    """Convert a DOI to a filesystem-safe ID."""
    return doi.replace("/", "_", ).replace(".", "_").replace("-", "_")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch metadata and download PDF for a DOI.")
    parser.add_argument("--doi", required=True, help="DOI of the article")
    parser.add_argument("--output-dir", default="pdf", help="Directory to save the PDF (default: pdf/)")
    args = parser.parse_args()

    doi = args.doi
    article_id = doi_to_id(doi)

    # --- Metadata ---
    metadata = {"id": article_id} | fetch_metadata_all_apis(doi)
    print(json.dumps(metadata, indent=2, ensure_ascii=False))

    # --- PDF ---
    os.makedirs(args.output_dir, exist_ok=True)
    output_path = os.path.join(args.output_dir, f"{article_id}.pdf")
    success = download_pdf(doi, output_path)

    if success:
        size = os.path.getsize(output_path)
        if size == 0:
            print(f"Warning: PDF file is empty ({output_path})")
        else:
            print(f"PDF saved: {output_path} ({size} bytes)")
    else:
        print("PDF download failed.")
