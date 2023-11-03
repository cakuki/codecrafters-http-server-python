import re
from typing import NamedTuple, Callable

from .request import Request
from .response import Response


class Route(NamedTuple):
    method: str
    path: str
    pattern: re.Pattern
    handler: Callable[[Request], Response]


class Router:
    routes: list[Route]

    def __init__(self):
        self.routes = []

    def add_route(self, method: str, path: str, handler: Callable[[Request], Response]):
        # convert path to regex, support named arguments
        pattern = re.compile(re.sub(r"(?<=/):(\w+)", "(?P<\\1>.*)", path))
        self.routes.append(Route(method, path, pattern, handler))

    def handle_request(self, sock):
        request = Request(sock.recv(1024))
        response = Response("404 Not Found")

        matcher = (
            (match, route)
            for route in self.routes
            if route.method == request.method
            and (match := route.pattern.fullmatch(request.path))
        )

        try:
            match, route = next(matcher)
            request.args = match.groupdict()
            response = route.handler(request)
        except StopIteration:
            pass

        sock.sendall(response.to_bytes())
        sock.close()

    def get(self, path):
        def decorator(handler):
            self.add_route("GET", path, handler)
            return handler

        return decorator

    def post(self, path):
        def decorator(handler):
            self.add_route("POST", path, handler)
            return handler

        return decorator
