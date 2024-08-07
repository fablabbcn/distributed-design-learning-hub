from celery import chord

from ddlh import airtable, tasks
from ddlh.repositories import DocumentsRepository


def ingest_documents() -> None:
    db = airtable.get_db_instance()
    repo = DocumentsRepository(db)
    documents = repo.get_all_documents()
    chord(tasks.fetch.s(document) for document in documents)(tasks.index.s()).get()


if __name__ == "__main__":
    ingest_documents()
