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
        self.formats_table = MagicMock()
        self.featured_documents_table = MagicMock()
        self.ui_strings_table = MagicMock()
        self.formats_table.get.side_effect = lambda arg: self.formats.get(arg)
        self.airtable_client.table.side_effect = [
            self.documents_table,
            self.themes_table,
            self.formats_table,
            self.featured_documents_table,
            self.ui_strings_table,
        ]
        self.themes_table.all.return_value = [
            {"id": id, "fields": fields}
            for (id, fields) in self.themes.items()
        ]
        self.documents_table.all.return_value = [
            {"fields": document} for document in self.documents
        ]

    def setup_method(self, method):
        self.token = "TOKEN"
        self.base_id = "BASE_ID"
        self.documents_table_id = "DOCUMENTS_TABLE_ID"
        self.themes_table_id = "THEMES_TABLE_ID"
        self.formats_table_id = "FORMATS_TABLE_ID"
        self.featured_documents_table_id = "FEATURED_DOCUMENTS_TABLE_ID"
        self.ui_strings_table_id = "UI_STRINGS_TABLE_ID"
        self.themes = {
            "theme1_id": {"name": "theme1", "summary": "Theme 1 summary"},
            "theme2_id": {"name": "theme2", "summary": "Theme 2 summary"},
        }
        self.formats = {
            "format_id": {"fields": {"name": "Format", "type": "type"}}
        }
        self.documents = [
            {
                "link": "doc1",
                "themes": ["theme1_id"],
                "tags": ["tag1", "tag2"],
                "format": ["format_id"],
            },
            {
                "link": "doc2",
                "themes": ["theme2_id"],
                "tags": ["tag2", "tag3"],
                "format": ["format_id"],
            },
        ]

    def create_db(self):
        return AirtableDocumentDatabase(
            self.token,
            self.base_id,
            self.documents_table_id,
            self.themes_table_id,
            self.formats_table_id,
            self.featured_documents_table_id,
            self.ui_strings_table_id,
        )

    def test_airtable_api_constructed_with_passed_token(self):
        """
        It passes the given token to the airtable constructor.
        """
        self.create_db()
        self.airtable_constructor.assert_called_with(self.token)

    def test_airtable_api_gets_documents_table(self):
        """
        It gets the documents table with the given base_id and table_id
        """
        self.create_db()
        calls = self.airtable_client.table.call_args_list
        assert call(self.base_id, self.documents_table_id) in calls

    def test_airtable_api_gets_themes_table(self):
        """
        It gets the themes table with the given base_id and table_id
        """
        self.create_db()
        calls = self.airtable_client.table.call_args_list
        assert call(self.base_id, self.themes_table_id) in calls

    def test_airtable_api_gets_all_rows(self):
        """
        It retrieves all rows of the documents table
        """
        self.create_db()
        self.documents_table.all.assert_called()

    def test_airtable_api_gets_themes(self):
        """
        It retrieves all rows of the themes table
        """
        self.create_db()
        self.themes_table.all.assert_called()

    def test_get_all_documents_returns_documents(self):
        """
        get_all_documents returns all the documents in the table
        """
        db = self.create_db()
        links = [doc["link"] for doc in db.get_all_documents()]
        assert "doc1" in links
        assert "doc2" in links

    def test_get_all_tags_returns_tags(self):
        """
        get_all_tags returns all the tags used in
        every document in the table
        """
        db = self.create_db()
        tags = db.get_all_tags()
        assert "tag1" in tags
        assert "tag2" in tags
        assert "tag3" in tags

    def test_get_all_themes_returns_themes(self):
        """
        get_all_themes returns all the themes used in
        every document in the table
        """
        db = self.create_db()
        themes = db.get_all_themes()
        assert "theme1" in themes
        assert "theme2" in themes

    def test_get_documents_for_tag_returns_tagged_documents_only(self):
        """
        get_documents_for_tag returns all, and only,
        documents for the given tag
        """
        db = self.create_db()
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
        db = self.create_db()
        links1 = [doc["link"] for doc in db.get_documents_for_theme("theme1")]
        links2 = [doc["link"] for doc in db.get_documents_for_theme("theme2")]
        assert "doc1" in links1
        assert "doc2" not in links1
        assert "doc1" not in links2
        assert "doc2" in links2

    def test_get_tags_for_theme_returns_tags_for_theme_only(self):
        """
        get_tags_for_theme returns all, and only, tags for
        documents with the given theme
        """
        db = self.create_db()
        tags1 = db.get_tags_for_theme("theme1")
        tags2 = db.get_tags_for_theme("theme2")

        assert "tag1" in tags1
        assert "tag2" in tags1
        assert "tag2" in tags2
        assert "tag3" in tags2

    def test_get_theme_returns_theme_metadata(self):
        """
        get_theme returns metadata for the passed theme
        """
        db = self.create_db()

        theme1 = db.get_theme("theme1")
        theme2 = db.get_theme("theme2")

        assert theme1 is not None
        assert theme2 is not None

        assert theme1["summary"] == "Theme 1 summary"
        assert theme2["summary"] == "Theme 2 summary"
