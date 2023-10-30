import os
import socket
import sys


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

    def __init__(self, status: str, headers: dict[str, str], body: bytes):
        self.status = status
        self.headers = headers
        self.body = body

    def to_bytes(self) -> bytes:
        content_length = str(len(self.body))
        self.headers["Content-Length"] = content_length

        return (
            b"HTTP/1.1 "
            + self.status.encode("utf-8")
            + b"\r\n"
            + b"\r\n".join(
                key.encode("utf-8") + b": " + value.encode("utf-8")
                for key, value in self.headers.items()
            )
            + b"\r\n\r\n"
            + self.body
        )


class Router:
    def __init__(self):
        self.routes_get = {}
        self.routes_post = {}

    def add_route(self, method, path, handler):
        if method == "GET":
            self.routes_get[path] = handler
        elif method == "POST":
            self.routes_post[path] = handler

    def handle_request(self, request, client):
        routes = self.routes_get if request.method == "GET" else self.routes_post

        # go through routes and find the first one that matches, support * wildcard
        for path, handler in routes.items():
            if path == request.path:
                handler(request, client)
                return
            elif path.endswith("*"):
                if request.path.startswith(path[:-1]):
                    # add wildcard argument to request
                    request.args = {"*": request.path[len(path[:-1]) :]}
                    handler(request, client)
                    return

        # return 404
        response = Response("404 Not Found", {}, b"")
        client.sendall(response.to_bytes())

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
    os.environ["SERVE_DIR"] = serve_dir

    router = Router()

    @router.get("/")
    def index(request, client):
        response = Response("200 OK", {}, b"")
        client.sendall(response.to_bytes())

    @router.get("/user-agent")
    def user_agent(request, client):
        response = Response(
            "200 OK",
            {"Content-Type": "text/plain"},
            request.headers["User-Agent"].encode("utf-8"),
        )
        client.sendall(response.to_bytes())

    @router.get("/echo/*")
    def echo(request, client):
        response = Response(
            "200 OK", {"Content-Type": "text/plain"}, request.args["*"].encode("utf-8")
        )
        client.sendall(response.to_bytes())

    @router.get("/files/*")
    def files(request, client):
        print('request.path.split("/")[-1]', request.path.split("/")[-1])
        print('request.args["*"]', request.args["*"])
        filename = request.path.split("/")[-1]
        filepath = os.path.join(serve_dir, filename)
        if os.path.isfile(filepath):
            with open(filepath, "rb") as f:
                response = Response("200 OK", {}, f.read())
        else:
            response = Response("404 Not Found", {}, b"")
        client.sendall(response.to_bytes())

    print("Listening...")
    # listen for connections from client loop forever
    while True:
        client, address = server_socket.accept()
        request = Request(client.recv(1024))
        router.handle_request(request, client)
        client.close()


if __name__ == "__main__":
    main()
