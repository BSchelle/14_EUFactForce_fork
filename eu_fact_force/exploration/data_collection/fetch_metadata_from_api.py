OPENALEX_API_KEY = "AtCqIiBpdcCzao86YBx2L2"

api_to_metadata = {
    "HAL": {
        "url": "https://api.archives-ouvertes.fr/search/?q=doiId_s:",
        "metadata_fields": {
            "author": "authFullName_s",
            "keywords": "mesh_s",
            "publish date": "publicationDate_s",
            "cited articles": "",
            "article name": "title_s",
            "doi code": "doiId_s",
            "article type": "docType_s"
        }
    },
    "CrossRef": {
        "url": "https://api.crossref.org/works/doi/",
        "metadata_fields": {
            "author": {
                "first_name": "/message/author/0/given",
                "last_name": "/message/author/0/family"
            },
            "keywords": "",
            "publish date": {
                "year":"/message/published/date-parts/0/0",
                "month":"/message/published/date-parts/0/1",
                "day":"/message/published/date-parts/0/2",
            },
            "cited articles": "/message/reference",  # id/DOI ou unstructured
            "article name": "/message/title/0",
            "doi code": "/message/DOI",
            "article type": "/message/type"
        }
    },
    "OpenAlex": {
        "url": f"https://api.openalex.org/works/doi:",  # ?api_key={OPENALEX_API_KEY}
        "metadata_fields": {
            "author": "raw_author_name",
            "keywords": "mesh",  # id/descriptor_name
            "publish date": "publication_date",
            "cited articles": "referenced_works",  # id (donne un lien openalex auquel on ajoute api. avant openalex pour avoir les métadonnées)
            "article name": "title",
            "doi code": "doi",
            "article type": "type"
        }
    }
}

