def doi_to_id(doi: str) -> str:
    """Convert a DOI to a filesystem-safe ID."""
    return (
        doi.replace(
            "/",
            "_",
        )
        .replace(".", "_")
        .replace("-", "_")
    )