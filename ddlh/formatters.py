from flask import render_template

from ddlh import airtable
from ddlh.models import Summary
from ddlh.repositories import DocumentsRepository


def format_summary(summary: Summary) -> str:
    document_summaries = []
    repository = DocumentsRepository(airtable.get_db_instance())
    for document_summary in summary.document_summaries:
        document = repository.get_document(document_summary.document)
        if document:
            document_summaries.append(
                {"document": document, "summary": document_summary.summary}
            )
    return render_template(
        "partials/search_summary.j2",
        top_sentence=summary.top_sentence,
        document_summaries=document_summaries,
    )
