from parsers.crossref import CrossrefMetadataParser
from parsers.openalex import OpenAlexMetadataParser
from parsers.pubmed import PubMedMetadataParser
from parsers.hal import HALMetadataParser
from parsers.arxiv import ArxivMetadataParser

PARSERS = [
    CrossrefMetadataParser(),
    OpenAlexMetadataParser(),
    PubMedMetadataParser(),
    HALMetadataParser(),
    ArxivMetadataParser(),
]
