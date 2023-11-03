from webob import Request, Response
from parse import parse
import inspect


class API:
    def __init__(self):
        self.routes = {}

    def __call__(self, environ, start_response):
        request = Request(environ)

        response = self.handle_request(request)

        return response(environ, start_response)

    # To be used as a decorator to define different application routes
    def route(self, path):
        assert path not in self.routes, "Route is already defined!"

        def wrapper(handler):
            self.routes[path] = handler
            return handler

        return wrapper

    # The request handler
    def handle_request(self, request):
        response = Response()

        handler, kwargs = self.find_handler(request_path=request.path)

        if handler is not None:
            # Class based request handler
            if inspect.isclass(handler):
                handler = getattr(
                    handler(), request.method.lower(), None)
                if handler is None:
                    raise AttributeError("Method not allowed", request.method)

            handler(request, response, **kwargs)
        else:
            self.default_response(response)

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
