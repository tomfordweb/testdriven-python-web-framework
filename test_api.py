import pytest

from api import API
from middleware import Middleware

FILE_DIR = "css"
FILE_NAME = "main.css"
FILE_CONTENTS = "body {background-color: #bada55}"


def _create_static(static_dir):
    asset = static_dir.mkdir(FILE_DIR).join(FILE_NAME)
    asset.write(FILE_CONTENTS)

    return asset


def test_basic_route_adding(api):
    @api.route("/home")
    def home(req, res):
        res.text = "YOLO"


def test_route_overlap_throws_exception(api):
    @api.route("/home")
    def home(req, res):
        res.text = "YOLO"

    with pytest.raises(AssertionError):

        @api.route("/home")
        def home2(req, res):
            res.text = "yolo2"


def test_it_can_send_requests(api, client):
    RESPONSE_TEXT = "This is cool"

    @api.route("/hey")
    def cool(req, res):
        res.text = RESPONSE_TEXT

    assert client.get("http://testserver/hey").text == RESPONSE_TEXT


def test_parameterized_route(api, client):
    @api.route("/{name}")
    def greeting(req, res, name):
        res.text = f"hey {name}"

    assert client.get("http://testserver/tom").text == "hey tom"
    assert client.get("http://testserver/ashley").text == "hey ashley"


def test_it_returns_404_nonexistent_route(api, client):
    response = client.get("http://testserver/foobar")

    assert response.status_code == 404
    assert response.text == "Not Found"


def test_class_based_handler_get(api, client):
    response_text = "hello foo"

    @api.route("/foo")
    class FooResource:
        def get(self, req, res):
            res.text = response_text

    assert client.get("http://testserver/foo").text == response_text


def test_class_based_handler_post(api, client):
    response_text = "hello bar"

    @api.route("/bar")
    class BarResource:
        def post(self, req, res):
            res.text = response_text

    assert client.post("http://testserver/bar").text == response_text


def test_class_based_handler_method_not_allowed(api, client):
    @api.route("/baz")
    class BazHandler:
        def post(self, req, res):
            res.text = "yo"

    with pytest.raises(AttributeError):
        client.get("http://testserver/baz")


def test_alternative_django_approach_of_adding_route(api, client):
    response_text = "alternative way to add a route"

    def alternative(req, resp):
        resp.text = response_text

    api.add_route("/alternative", alternative)

    assert client.get("http://testserver/alternative").text == response_text


def test_template(api, client):
    @api.route("/html")
    def html_handler(req, res):
        res.body = api.template(
            "index.html", context={"title": "Some Title", "name": "Some Name"}
        ).encode()

    response = client.get("http://testserver/html")

    assert "text/html" in response.headers["Content-Type"]
    assert "Some Title" in response.text
    assert "Some Name" in response.text


def test_custom_exception_handler(api, client):
    def on_exception(req, res, exc):
        res.text = "AttributeErrorHappened"

    api.add_exception_handler(on_exception)

    @api.route("/")
    def index(req, resp):
        raise AttributeError()

    response = client.get("http://testserver/")

    assert response.text == "AttributeErrorHappened"


def test_404_returned_for_nonexistent_static_file(client):
    assert client.get("http://testserver/static/main.css").status_code == 404


def test_assets_are_served(tmpdir_factory):
    static_dir = tmpdir_factory.mktemp("static")
    _create_static(static_dir)
    api = API(static_dir=str(static_dir))
    client = api.test_session()

    response = client.get(f"http://testserver/static/{FILE_DIR}/{FILE_NAME}")

    assert response.status_code == 200
    assert response.text == FILE_CONTENTS


def test_middleware_methods_are_called(api, client):
    process_request_called = False
    process_response_called = False

    class CallMiddlewareMethods(Middleware):
        def __init__(self, app):
            super().__init__(app)

        def process_request(self, req):
            nonlocal process_request_called
            process_request_called = True

        def process_response(self, req, resp):
            nonlocal process_response_called
            process_response_called = True

    api.add_middleware(CallMiddlewareMethods)

    @api.route("/")
    def index(req, res):
        res.text = "hey"

    client.get("http://testserver/")

    assert process_request_called is True
    assert process_response_called is True


def test_allowed_methods_for_function_based_handlers(api, client):
    @api.route("/home", allowed_methods=["post"])
    def home(request, response):
        response.text = "Hello"

    with pytest.raises(AttributeError):
        client.get("http://testServer/home")

    assert client.post("http://testserver/home").text == "Hello"


def test_json_response_helper(api, client):
    @api.route("/json")
    def json_handler(request, response):
        response.json = {"name": "tom"}

    response = client.get("http://testserver/json")
    json_body = response.json()

    assert "application/json" in response.headers['Content-Type']
    assert json_body["name"] == "tom"


def test_html_response_helper(api, client):
    @api.route("/html")
    def html_handler(request, response):
        response.html = api.template(
            "index.html", context={"title": "Best Title", "name": "Best Name"}
        )
    response = client.get("http://testserver/html")

    assert "text/html" in response.headers['Content-Type']
    assert "Best Title" in response.text
    assert "Best Name" in response.text

def test_text_response_helper(api, client):
    response_text = "Just Plain Text"

    @api.route('/text')
    def text_handler(req, resp):
        resp.text = response_text
    
    response = client.get('http://testserver/text')

    assert "text/plain" in response.headers['Content-Type']
    assert response.text == response_text

def manually_setting_body(api,client):
    @api.route('/body')
    def text_handler(request, response):
        response.body = b"Byte Body"
        response.content_type = "text/plain"

    response = client.get('http://testserver/body')

    assert "text/plain" in response.headers["Content-Type"]
    assert response.text == "Byte Body"

    k



