from unittest.mock import MagicMock, call

import pytest  # type: ignore

from app.airtable_db import AirtableDocumentDatabase


class TestAirtableDocumentDatabase:

    @pytest.fixture(autouse=True)
    def mock_airtable(self, mocker):
        self.airtable_constructor = mocker.patch(
            "app.airtable_db.Api", autospec=True
        )
        self.airtable_client = self.airtable_constructor.return_value
        self.documents_table = MagicMock()
        self.themes_table = MagicMock()
        self.themes_table.get.side_effect = lambda arg: self.themes.get(arg)
        self.airtable_client.table.side_effect = [
            self.documents_table,
            self.themes_table,
        ]
        self.documents_table.all.return_value = [
            {"fields": document} for document in self.documents
        ]
        self.themes_table = self.themes_table

    def setup_method(self, method):
        self.token = "TOKEN"
        self.base_id = "BASE_ID"
        self.documents_table_id = "DOCUMENTS_TABLE_ID"
        self.themes_table_id = "THEMES_TABLE_ID"
        self.themes = {
            "theme1_id": {
                "fields": {"name": "theme1"},
            },
            "theme2_id": {"fields": {"name": "theme2"}},
        }
        self.documents = [
            {
                "link": "doc1",
                "themes": ["theme1_id"],
                "tags": ["tag1", "tag2"],
            },
            {
                "link": "doc2",
                "themes": ["theme2_id"],
                "tags": ["tag2", "tag3"],
            },
        ]

    def test_airtable_api_constructed_with_passed_token(self):
        """
        It passes the given token to the airtable constructor.
        """
        AirtableDocumentDatabase(
            self.token,
            self.base_id,
            self.documents_table_id,
            self.themes_table_id,
        )
        self.airtable_constructor.assert_called_with(self.token)

    def test_airtable_api_gets_documents_table(self):
        """
        It gets the documents table with the given base_id and table_id
        """
        AirtableDocumentDatabase(
            self.token,
            self.base_id,
            self.documents_table_id,
            self.themes_table_id,
        )
        calls = self.airtable_client.table.call_args_list
        assert call(self.base_id, self.documents_table_id) in calls

    def test_airtable_api_gets_themes_table(self):
        """
        It gets the themes table with the given base_id and table_id
        """
        AirtableDocumentDatabase(
            self.token,
            self.base_id,
            self.documents_table_id,
            self.themes_table_id,
        )
        calls = self.airtable_client.table.call_args_list
        assert call(self.base_id, self.themes_table_id) in calls

    def test_airtable_api_gets_all_rows(self):
        """
        It retrieves all rows of the documents table
        """
        AirtableDocumentDatabase(
            self.token,
            self.base_id,
            self.documents_table_id,
            self.themes_table_id,
        )
        self.documents_table.all.assert_called()

    def test_airtable_api_gets_themes(self):
        """
        It looks up theme data for the given theme ids
        """
        AirtableDocumentDatabase(
            self.token,
            self.base_id,
            self.documents_table_id,
            self.themes_table_id,
        )
        assert self.themes_table.get.call_args_list == [
            call("theme1_id"),
            call("theme2_id"),
        ]

    def test_get_all_documents_returns_documents(self):
        """
        get_all_documents returns all the documents in the table
        """
        db = AirtableDocumentDatabase(
            self.token,
            self.base_id,
            self.documents_table_id,
            self.themes_table_id,
        )
        links = [doc["link"] for doc in db.get_all_documents()]
        assert "doc1" in links
        assert "doc2" in links

    def test_get_all_tags_returns_tags(self):
        """
        get_all_tags returns all the tags used in
        every document in the table
        """
        db = AirtableDocumentDatabase(
            self.token,
            self.base_id,
            self.documents_table_id,
            self.themes_table_id,
        )
        tags = db.get_all_tags()
        assert "tag1" in tags
        assert "tag2" in tags
        assert "tag3" in tags

    def test_get_all_themes_returns_themes(self):
        """
        get_all_themes returns all the themes used in
        every document in the table
        """
        db = AirtableDocumentDatabase(
            self.token,
            self.base_id,
            self.documents_table_id,
            self.themes_table_id,
        )
        themes = db.get_all_themes()
        print(themes)
        assert "theme1" in themes
        assert "theme2" in themes

    def test_get_documents_for_tag_returns_tagged_documents_only(self):
        """
        get_documents_for_tag returns all, and only,
        documents for the given tag
        """
        db = AirtableDocumentDatabase(
            self.token,
            self.base_id,
            self.documents_table_id,
            self.themes_table_id,
        )
        links1 = [doc["link"] for doc in db.get_documents_for_tag("tag1")]
        links2 = [doc["link"] for doc in db.get_documents_for_tag("tag2")]
        links3 = [doc["link"] for doc in db.get_documents_for_tag("tag3")]
        assert "doc1" in links1
        assert "doc2" not in links1
        assert "doc1" in links2
        assert "doc2" in links2
        assert "doc1" not in links3
        assert "doc2" in links3

    def test_get_documents_for_theme_returns_themed_documents_only(self):
        """
        get_documents_for_theme returns all, and only,
        documents for the given theme
        """
        db = AirtableDocumentDatabase(
            self.token,
            self.base_id,
            self.documents_table_id,
            self.themes_table_id,
        )
        links1 = [doc["link"] for doc in db.get_documents_for_theme("theme1")]
        links2 = [doc["link"] for doc in db.get_documents_for_theme("theme2")]
        assert "doc1" in links1
        assert "doc2" not in links1
        assert "doc1" not in links2
        assert "doc2" in links2
