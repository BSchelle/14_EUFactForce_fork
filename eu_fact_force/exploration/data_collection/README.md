# data_collection

Fetches bibliographic metadata and PDF for a scientific article from its DOI.

## Files

| File | Role |
|---|---|
| `main.py` | CLI entry point — fetches metadata and downloads the PDF |
| `metadata.py` | Metadata fetching logic and API configuration |
| `pdf.py` | PDF download logic |

## Usage

```bash
python3 main.py --doi "10.1038/s41562-021-01122-8"
python3 main.py --doi "10.1038/s41562-021-01122-8" --output-dir my_pdfs/
```

Outputs a JSON object to stdout with the article metadata, and saves the PDF as `{output-dir}/{id}.pdf`.

The article `id` is derived from the DOI by replacing `/`, `-` and `.` with `_`
(e.g. `10.1038/s41562-021-01122-8` → `10_1038_s41562-021-01122-8`).

### Fetch metadata only

```bash
python3 metadata.py --doi "10.1038/s41562-021-01122-8"
python3 metadata.py --doi "10.1038/s41562-021-01122-8" --api CrossRef
```

### Download PDF only

```bash
python3 pdf.py --doi "10.1038/s41562-021-01122-8"
python3 pdf.py --doi "10.1038/s41562-021-01122-8" --output-dir my_pdfs/
```

## Metadata output

```json
{
  "id": "10_1038_s41562-021-01122-8",
  "found": true,
  "sources": ["CrossRef", "OpenAlex"],
  "article name": "...",
  "author": ["Author One", "Author Two"],
  "journal": "...",
  "publish date": "2021-06-07",
  "link": "https://...",
  "keywords": ["keyword1", "keyword2"],
  "cited articles": ["10.1000/xyz123", "..."],
  "doi code": "10.1038/s41562-021-01122-8",
  "article type": "journal-article",
  "open access": false,
  "status": "published"
}
```

Fields may be `null` if not available in any API. `sources` lists which APIs returned a result.

For each field, the most complete value across all APIs is kept (longest list or string).

## Supported APIs

| API | URL | Notable fields |
|---|---|---|
| **CrossRef** | `api.crossref.org` | cited articles, retraction/correction status |
| **HAL** | `api.archives-ouvertes.fr` | French institutional publications |
| **OpenAlex** | `api.openalex.org` | open-access PDF link, MeSH keywords |

APIs are queried in the order: CrossRef → HAL → OpenAlex.

## Adding a new API

Add an entry to `API_CONFIG` in `metadata.py` and append the name to `API_ORDER`:

```python
"MyAPI": {
    "url": "https://api.example.com/works/",  # DOI is appended
    "url_suffix": "",                          # optional suffix after the DOI
    "response_root": "/data/item",            # path to the document root in the response
    "fields": {
        "article name": "/data/title",        # leading "/" = path from response root
        "author": "authors/name",             # no leading "/" = path from document root
        "keywords": {"fallback": ["mesh", "tags"]},
        ...
    },
},
```

See the `_extract_field` docstring in `metadata.py` for the full list of supported path spec formats.
