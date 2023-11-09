from api import API
from middleware import Middleware


def custom_exception_handler(request, response, exception_cls):
    response.text = str(exception_cls)
    response.status_code = 500

app = API()

class RequestLogMiddleware(Middleware):
    def process_request(self, req):
        print("Processing request", req.url)

    def process_response(self, req, res):
        print("Processing response", req.url)

app.add_middleware(RequestLogMiddleware)

app.add_exception_handler(custom_exception_handler)


@app.route("/home")
def home(request, response):
    response.text = "Hello from the HOME page"


@app.route("/about")
def about(request, response):
    response.text = "Hello from the ABOUT page"


@app.route("/hello/{name}")
def greeting(request, response, name):
    response.text = f"Hello, {name}"


@app.route("/book")
class BooksResource:
    def get(self, req, resp):
        resp.text = "Books Page"

    def post(self, req, resp):
        resp.text = "Endpoint to create a book"


@app.route("/")
def template_handler(req, resp):
    resp.body = app.template(
        "index.html",
        context={
            "name": "Test Driven Python Web Framework",
            "title": "Test Driven Python Web Framework",
        },
    ).encode()

@app.route('/exception')
def exception_thrower(req, res):
    raise AssertionError("This handler should not be used")


