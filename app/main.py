import os
import re
import socket
import sys
import threading
from typing import Callable, NamedTuple


class Request:
    method: str
    path: str
    headers: dict[str, str]
    body: bytes
    args: dict[str, str]

    def __init__(self, raw_request: bytes):
        request_line = raw_request.split(b"\r\n")[0].decode("utf-8")
        self.method, self.path, _ = request_line.split(" ")

        self.headers = {}
        for header_line in raw_request.split(b"\r\n")[1:]:
            if not header_line:
                break
            key, value = header_line.decode("utf-8").split(": ")
            self.headers[key] = value

        self.body = raw_request.split(b"\r\n\r\n")[1]


class Response:
    status: str
    headers: dict[str, str]
    body: bytes

    def __init__(
        self, status: str = "200 OK", headers: dict[str, str] = {}, body: bytes = b""
    ):
        self.status = status
        self.headers = headers
        self.body = body

    def to_bytes(self) -> bytes:
        content_length = str(len(self.body))
        self.headers["Content-Length"] = content_length

        return (
            b"HTTP/1.1 "
            + self.status.encode()
            + b"\r\n"
            + b"\r\n".join(
                key.encode() + b": " + value.encode()
                for key, value in self.headers.items()
            )
            + b"\r\n\r\n"
            + self.body
        )


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


def main():
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)

    serve_dir = sys.argv[-1]

    router = Router()

    @router.get("/")
    def index(request: Request):
        return Response()

    @router.get("/user-agent")
    def user_agent(request: Request):
        return Response(
            headers={"Content-Type": "text/plain"},
            body=request.headers["User-Agent"].encode(),
        )

    @router.get("/echo/:message")
    def echo(request: Request):
        return Response(
            headers={"Content-Type": "text/plain"},
            body=request.args["message"].encode(),
        )

    @router.get("/files/:path")
    def get_files(request: Request):
        filename = request.args["path"]
        filepath = os.path.join(serve_dir, filename)

        if not os.path.isfile(filepath):
            return Response("404 Not Found")

        with open(filepath, "rb") as f:
            return Response(
                headers={"Content-Type": "application/octet-stream"},
                body=f.read(),
            )

    @router.post("/files/:path")
    def post_files(request: Request):
        filename = request.args["path"]
        filepath = os.path.join(serve_dir, filename)

        with open(filepath, "wb") as f:
            f.write(request.body)

        return Response("201 OK")

    while True:
        sock, _ = server_socket.accept()
        thread = threading.Thread(target=router.handle_request, args=(sock,))
        thread.start()


if __name__ == "__main__":
    main()
