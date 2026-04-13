import json
from pathlib import Path
import tempfile

from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status

from .services import save_to_s3_and_postgres, save_chunks, add_embeddings
from .parsing import parse_file


@api_view(['POST'])
@parser_classes([MultiPartParser])
def upload_pdf(request):
    """
    Receives a PDF + JSON metadata from Dash,
    runs the ingestion pipeline and returns the status.
    """
    # data validation
    pdf_file = request.FILES.get('file')
    metadata_raw = request.data.get('metadata')

    if not pdf_file:
        return Response(
            {"error": "Fichier PDF manquant"},
            status=status.HTTP_400_BAD_REQUEST
        )
    if not metadata_raw:
        return Response(
            {"error": "Métadonnées manquantes"},
            status=status.HTTP_400_BAD_REQUEST
        )

    #valid metadata test
    try:
        metadata = json.loads(metadata_raw)
    except json.JSONDecodeError:
        return Response(
            {"error": "Métadonnées JSON invalides"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # temp data save
    with tempfile.NamedTemporaryFile(
        suffix='.pdf',
        delete=False
    ) as tmp:
        for chunk in pdf_file.chunks():
            tmp.write(chunk)
        tmp_path = Path(tmp.name)

    # data pipeline save -> parse -> embedding
    try:
        # variable initialization to avoid NameError if not found in try block
        source_file = None
        chunks = []

        doi = metadata.get('doi')
        tags = metadata.get('authors', [])

        source_file = save_to_s3_and_postgres(
            local_file_path=tmp_path,
            tags_pubmed=tags,
            doi=doi,
        )
        document_parts = parse_file(source_file)
        chunks = save_chunks(source_file, document_parts)
        add_embeddings(chunks)

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        tmp_path.unlink(missing_ok=True)  # clean temp file

    return Response({
        "status": "success",
        "source_file_id": source_file.id,
        "filename": pdf_file.name,
        "chunks_count": len(chunks),
    }, status=status.HTTP_201_CREATED)
