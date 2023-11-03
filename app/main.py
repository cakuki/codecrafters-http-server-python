import os
import socket
import sys
import threading

from .http import Request, Response, Router


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
