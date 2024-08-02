from ddlh import airtable, elasticsearch, tasks
from ddlh.repositories import DocumentsRepository
from ddlh.utils import url_to_id


def ingest_documents() -> None:
    db = airtable.get_db_instance()
    repo = DocumentsRepository(db)
    documents = repo.get_all_documents()
    for document in documents:
        id = url_to_id(document.link)
        elasticsearch.index(id, **document.asdict())
        tasks.dispatch.delay(document.link)


if __name__ == "__main__":
    ingest_documents()
