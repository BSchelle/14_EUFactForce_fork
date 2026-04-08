"""Factories for test data."""

import random

import factory
from factory.django import DjangoModelFactory

from eu_fact_force.ingestion.models import (
    EMBEDDING_DIMENSIONS,
    DocumentChunk,
    SourceFile,
)


class SourceFileFactory(DjangoModelFactory):
    class Meta:
        model = SourceFile

    doi = ""
    s3_key = ""
    status = SourceFile.Status.STORED


def _random_embedding_vector() -> list[float]:
    return [random.random() for _ in range(EMBEDDING_DIMENSIONS)]


class DocumentChunkFactory(DjangoModelFactory):
    class Meta:
        model = DocumentChunk

    source_file = factory.SubFactory(SourceFileFactory)
    order = factory.Sequence(lambda n: n)
    content = factory.Sequence(lambda n: f"Paragraphe {n + 1}")
    embedding = factory.LazyFunction(_random_embedding_vector)
