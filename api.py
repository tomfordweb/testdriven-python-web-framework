from webob import Request, Response
from parse import parse
from requests import Session as RequestsSession
from wsgiadapter import WSGIAdapter as RequestsWSGIAdapter
from jinja2 import Environment, FileSystemLoader
from whitenoise import WhiteNoise

import inspect
import os


class API:
    def __init__(self, templates_dir="templates", static_dir="static"):
        self.routes = {}
        self.template_env = Environment(
            loader=FileSystemLoader(os.path.abspath(templates_dir))
        )
        self.whitenoise = WhiteNoise(self.wsgi_app, root=static_dir)

        self.exception_handler = None

    def __call__(self, environ, start_response):
        return self.whitenoise(environ, start_response)

    def wsgi_app(self, environ, start_response):
        request = Request(environ)

        response = self.handle_request(request)

        return response(environ, start_response)

    # Add capability to process jinja2 templates
    def template(self, template_name, context=None):
        if context is None:
            context = {}
        return self.template_env.get_template(template_name).render(**context)

    def add_exception_handler(self, exception_handler):
        self.exception_handler = exception_handler

    # To be used as a decorator to define different application routes
    def route(self, path):
        def wrapper(handler):
            self.add_route(path, handler)
            return handler

        return wrapper

    # Add a route to the applications routes
    def add_route(self, path, handler):
        assert path not in self.routes, "Route is already defined!"

        self.routes[path] = handler

    # The request handler
    def handle_request(self, request):
        response = Response()

        handler, kwargs = self.find_handler(request_path=request.path)

        try:
            if handler is not None:
                # Class based request handler
                if inspect.isclass(handler):
                    handler = getattr(handler(), request.method.lower(), None)
                    if handler is None:
                        raise AttributeError(
                            "Method not allowed", request.method)

                handler(request, response, **kwargs)
            else:
                self.default_response(response)
        except Exception as e:
            if self.exception_handler is None:
                raise e
            else:
                self.exception_handler(request, response, e)

        return response

    # Find the handler defined by @app.route decorator
    def find_handler(self, request_path):
        for path, handler in self.routes.items():
            parse_result = parse(path, request_path)
            if parse_result is not None:
                return handler, parse_result.named

        return None, None

    def default_response(self, response):
        response.status_code = 404
        response.text = "Not Found"

    def test_session(self, base_url="http://testserver"):
        session = RequestsSession()
        session.mount(prefix=base_url, adapter=RequestsWSGIAdapter(self))
        return session
