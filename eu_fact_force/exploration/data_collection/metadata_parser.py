from abc import ABC, abstractmethod
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

    def download_pdf(self, pdf_url, save_path):
        response = requests.get(pdf_url)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"PDF downloaded successfully to {save_path}")
        else:
            print(f"Failed to download PDF. Status code: {response.status_code}")


class HALMetadataParser(MetadataParser):
    def __init__(self):
        super().__init__()
        self.url = "https://api.archives-ouvertes.fr/search/?q=doiId_s:{doi}&fl=*"
        self.metadata_mapping = {
            "article name":  "title_s",
            "authors":       "authFullName_s",
            "journal":       "journalTitle_s",
            "publish date":  "publicationDate_s",
            "link":          "uri_s",
            "keywords":      ["mesh_s", "keyword_s"],
            "cited articles": "",
            "doi":           "doiId_s",
            "article type":  "docType_s",
            "open access":   "openAccess_bool",
            "status":        ""
        }
        

    def get_metadata(self, doi: str) -> dict:
        response = requests.get(self.url.format(doi=doi))
        response.raise_for_status()                                                                
        docs = response.json().get("response", {}).get("docs", [])

        if not docs:
            return {"found": False}

        doc = docs[0]
        results = {}

        for metadata_type, metadata_value in self.metadata_mapping.items():
            if metadata_value is None:
                pass

            # if the field is a list of possible fields, take the first one that exists in the doc
            elif isinstance(metadata_value, list):
                results[metadata_type] = next(                                                          
                    (doc[key] for key in metadata_value if doc.get(key)), None
                )

            # champ simple
            else:
                results[metadata_type] = doc.get(metadata_value)

        return {"found": True} | results

if __name__ == "__main__":
    parser = HALMetadataParser()
    doi = "10.26855/ijcemr.2021.01.001"
    metadata = parser.get_metadata(doi)
    print(metadata)