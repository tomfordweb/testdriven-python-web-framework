import pytest


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

    assert client.get('http://testserver/foo').text == response_text

def test_class_based_handler_post(api, client):
    response_text = "hello bar"

    @api.route("/bar")
    class BarResource:
        def post(self, req, res):
            res.text = response_text

    assert client.post('http://testserver/bar').text == response_text

def test_class_based_handler_method_not_allowed(api, client):
    @api.route("/baz")
    class BazHandler:
        def post(self, req, res):
            res.text = "yo"
    with pytest.raises(AttributeError):
        client.get('http://testserver/baz')



