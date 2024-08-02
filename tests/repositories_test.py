from unittest.mock import MagicMock, call

import more_itertools as mit

from ddlh.repositories import DocumentsRepository


class TestDocumentsRepository:

    def setup_method(self, method):
        self.featured_documents = [
            {"id": "fd_1", "fields": {"document": ["doc3_id"]}},
            {"id": "fd_2", "fields": {"document": ["doc1_id"]}},
        ]
        self.themes = [
            {
                "id": "theme1_id",
                "fields": {"name": "theme1", "summary": "Theme 1 summary"},
            },
            {
                "id": "theme2_id",
                "fields": {"name": "theme2", "summary": "Theme 2 summary"},
            },
        ]
        self.formats = [
            {"id": "format_id", "fields": {"name": "Format", "type": "type"}}
        ]

        self.documents = [
            {
                "id": "doc1_id",
                "fields": {
                    "link": "doc1",
                    "themes": ["theme1_id"],
                    "tags": ["tag1", "tag2"],
                    "format": ["format_id"],
                    "author": "doc1_author",
                    "title": "doc1_title",
                    "topic": "doc1_topic",
                    "description": "doc1_description",
                    "image_url": "doc1_imag_eurl",
                },
            },
            {
                "id": "doc2_id",
                "fields": {
                    "link": "doc2",
                    "themes": ["theme2_id"],
                    "tags": ["tag2", "tag3"],
                    "format": ["format_id"],
                    "author": "doc2_author",
                    "title": "doc2_title",
                    "topic": "doc2_topic",
                    "description": "doc2_description",
                    "image_url": None,
                },
            },
            {
                "id": "doc3_id",
                "fields": {
                    "link": "doc3",
                    "themes": ["theme2_id"],
                    "tags": ["tag2", "tag3"],
                    "format": ["format_id"],
                    "author": "doc3_author",
                    "title": "doc3_title",
                    "topic": "doc3_topic",
                    "description": "doc3_description",
                },
            },
        ]

        self.airtable_data = {
            "themes": self.themes,
            "documents": self.documents,
            "formats": self.formats,
            "featured_documents": self.featured_documents,
        }

        self.airtable = MagicMock()

        def _airtable_all(table_name):
            return self.airtable_data.get(table_name, [])

        def _airtable_get(table_name, id):
            return mit.nth(
                [row for row in _airtable_all(table_name) if row["id"] == id],
                0,
            )

        self.airtable.get.side_effect = _airtable_get
        self.airtable.all.side_effect = _airtable_all

    def create_db(self):
        return DocumentsRepository(self.airtable)

    def test_airtable_api_gets_all_rows(self):
        """
        It retrieves all rows of the documents table
        """
        self.create_db()
        calls = self.airtable.all.call_args_list
        assert call("documents") in calls

    def test_airtable_api_gets_themes(self):
        """
        It retrieves all rows of the themes table
        """
        self.create_db()
        calls = self.airtable.all.call_args_list
        assert call("themes") in calls

    def test_it_gets_the_format_for_each_document(self):
        """
        It gets the corresponding format for each format id encountered
        """
        self.create_db()
        calls = self.airtable.get.call_args_list
        assert call("formats", "format_id") in calls

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

    def test_get_featured_documents_returns_featured_documents(self):
        """
        getting featured documents returns only featured documents, in order.
        """
        db = self.create_db()

        featured = db.get_featured_documents()

        assert len(featured) == 2
        assert featured[0]["link"] == "doc3"
        assert featured[1]["link"] == "doc1"
