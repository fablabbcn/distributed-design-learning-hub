from flask import current_app as app
from flask import render_template

from ddlh.models import SearchResult
from ddlh.utils import downcase_first


def format_search_result(result: SearchResult) -> str:
    document_summaries = []
    repository = app.config["documents_repository"]
    for document_summary in result.summary.document_summaries:
        document = repository.get_document(document_summary.document)
        if document:
            document_summaries.append(
                {
                    "document": document,
                    "summary": downcase_first(document_summary.summary),
                }
            )
    return render_template(
        "partials/search_summary.j2",
        query=result.query,
        top_sentence=result.summary.top_sentence,
        document_summaries=document_summaries,
    )
