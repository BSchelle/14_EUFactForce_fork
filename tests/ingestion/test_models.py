"""Tests for SourceFile model (e.g. storage cleanup on delete)."""

from pathlib import Path
from unittest.mock import patch

import pytest

from eu_fact_force.ingestion.models import SourceFile

PROJECT_ROOT = Path(__file__).resolve().parent.parent
README_PATH = PROJECT_ROOT / "README.md"


@pytest.mark.django_db
def test_deleting_source_file_removes_file_from_storage(tmp_path, tmp_storage):
    """
    When a SourceFile is deleted, the corresponding file is removed from storage.
    save_file_to_s3 uses get_s3_client(); on mock we write to tmp_storage so that
    default_storage (overridden to tmp_storage) and the client target the same place.
    """
    fn = tmp_path / "test_file.txt"
    with fn.open("w") as f:
        f.write("test content")

    def fake_upload_fileobj(Fileobj, Bucket, Key):
        dest = tmp_storage / Key
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(Fileobj.read())

    with patch("eu_fact_force.ingestion.s3.get_s3_client") as mock_client:
        mock_client.return_value.upload_fileobj = fake_upload_fileobj
        inp = SourceFile.create_from_file(fn, doi="test_doi")

    s3_fn = tmp_storage / inp.s3_key
    assert s3_fn.exists()
    inp.delete()
    assert not s3_fn.exists()
