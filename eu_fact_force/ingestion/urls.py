from django.urls import path
from . import upload, views

app_name = "ingestion"
urlpatterns = [
    path("ingest/", views.ingest, name="ingest"),
    path("api/upload/", upload.upload_pdf, name="api-upload"),
]
