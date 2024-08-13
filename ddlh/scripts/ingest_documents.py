from celery import chord

from ddlh import airtable, tasks
from ddlh.celery import celery_app  # noqa: F401
from ddlh.repositories import DocumentsRepository


def ingest_documents() -> None:
    db = airtable.get_db_instance()
    repo = DocumentsRepository(db)
    documents = repo.get_all_documents()
    chord(tasks.fetch.s(document) for document in documents)(tasks.index.s())


if __name__ == "__main__":
    ingest_documents()
