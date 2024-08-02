import pytest  # type: ignore

from ddlh.tasks import dispatch


class TestDispatch:
    @pytest.fixture(autouse=True, params=["text/html", "application/pdf"])
    def setup_content_type(self, request):
        self.set_content_type(request.param)

    def set_content_type(self, content_type):
        self.content_type = content_type

    @pytest.fixture(autouse=True)
    def setup_mocks(self, mocker):
        self.ingest_html_task = mocker.patch("ddlh.tasks.ingest_html")
        self.ingest_pdf_task = mocker.patch("ddlh.tasks.ingest_pdf")
        self.content_type = mocker.patch("ddlh.tasks.content_type")
        self.content_type.return_value = self.content_type

    def setup_method(self, method):
        self.url = "http://example.com"

    def test_dispatch_on_content_type(self, mocker):
        """
        It queues the appropriate ingestor task, passing the url
        """
        dispatch.apply(args=(self.url,)).get()
        if self.content_type == "text/html":
            self.ingest_html_task.delay.assert_called_with(self.url)
        elif self.content_type == "application/pdf":
            self.ingest_pdf_task.delay.assert_called_with(self.url)
