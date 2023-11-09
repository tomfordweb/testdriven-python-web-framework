from webob import Request
from parse import parse
from requests import Session as RequestsSession
from wsgiadapter import WSGIAdapter as RequestsWSGIAdapter
from jinja2 import Environment, FileSystemLoader
from whitenoise import WhiteNoise

from .middleware import Middleware
from .response import Response

import inspect
import os


class API:
    def __init__(self, templates_dir="templates", static_dir="static"):
        self.routes = {}
        self.template_env = Environment(
            loader=FileSystemLoader(os.path.abspath(templates_dir))
        )
        # The static file handler, by default all requests pass through this.
        # Notice that the main wsgi_app handler is passed to this.
        self.whitenoise = WhiteNoise(self.wsgi_app, root=static_dir)
        self.exception_handler = None
        self.middleware = Middleware(self)

    # Per pep3333 all WSGI servers must be callable
    # We pass it to whitenoise so that static files can be processed
    def __call__(self, environ, start_response):
        path_info = environ["PATH_INFO"]
        if path_info.startswith("/static"):
            environ["PATH_INFO"] = path_info[len("/static") :]
            return self.whitenoise(environ, start_response)

        return self.middleware(environ, start_response)

    # The main request handler.
    def wsgi_app(self, environ, start_response):
        request = Request(environ)

        response = self.handle_request(request)

        return response(environ, start_response)

    # Add capability to process jinja2 templates
    def template(self, template_name, context=None):
        if context is None:
            context = {}
        return self.template_env.get_template(template_name).render(**context)

    def add_middleware(self, middleware_class):
        self.middleware.add(middleware_class)

    # Allows capability to add a custom exception handler passed by reference
    def add_exception_handler(self, exception_handler):
        self.exception_handler = exception_handler

    # To be used as a decorator to define different application routes
    # It behaves the same as add_route, but is a bit more fluent.
    def route(self, path, allowed_methods=None):
        def wrapper(handler):
            self.add_route(path, handler, allowed_methods)
            return handler

        return wrapper

    # Add a route to the applications routes
    # this is the same as the "route" decorator method, and is more of a django approach
    def add_route(self, path, handler, allowed_methods=None):
        assert path not in self.routes, "Route is already defined!"

        if allowed_methods is None:
            allowed_methods = ["get", "post", "put", "patch", "delete", "options"]

        self.routes[path] = {"handler": handler, "allowed_methods": allowed_methods}

    # Handle the request
    def handle_request(self, request):
        response = Response()

        handler_data, kwargs = self.find_handler(request_path=request.path)

        try:
            if handler_data is not None:
                handler = handler_data["handler"]
                allowed_methods = handler_data["allowed_methods"]
                # Class based request handler
                if inspect.isclass(handler):
                    handler = getattr(handler(), request.method.lower(), None)
                    if handler is None:
                        raise AttributeError("Method not allowed", request.method)
                else:
                    if request.method.lower() not in allowed_methods:
                        raise AttributeError("Method not allowed", request.method)

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
        for path, handler_data in self.routes.items():
            parse_result = parse(path, request_path)
            if parse_result is not None:
                return handler_data, parse_result.named

        return None, None

    # By default, if the page cannot be found - return 404
    def default_response(self, response):
        response.status_code = 404
        response.text = "Not Found"

    # Allows one to create a spoofed/mocked test server
    def test_session(self, base_url="http://testserver"):
        session = RequestsSession()
        session.mount(prefix=base_url, adapter=RequestsWSGIAdapter(self))
        return session
