import os
import socket
import sys


def main():
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)

    serve_dir = sys.argv[-1]
    os.environ["SERVE_DIR"] = serve_dir

    # listen for connections from client loop forever
    while True:
        client, address = server_socket.accept()
        request = client.recv(1024)
        handle_request(request, client, serve_dir)
        client.close()

def handle_request(request, client, serve_dir):
    if request.startswith(b"GET / "):
        client.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
    elif request.startswith(b"GET /user-agent"):
        # get user-agent header from request, which could be in any order
        user_agent = ""
        for line in request.decode("utf-8").split("\r\n"):
            if line.startswith("User-Agent:"):
                user_agent = line.split(" ", 1)[1]
        client.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: " + str(len(user_agent)).encode("utf-8") + b"\r\n\r\n" + user_agent.encode("utf-8"))
    elif request.startswith(b"GET /echo/"):
        url = request.decode("utf-8").split("\r\n")[0].split(" ")[1]
        # split url after second slash, but only once
        arg = url.split("/", 2)[2]
        # send back the argument as body, and set the content length
        client.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: " + str(len(arg)).encode("utf-8") + b"\r\n\r\n" + arg.encode("utf-8"))
    elif request.startswith(b"GET /files/"):
        filename = request.decode("utf-8").split("\r\n")[0].split(" ")[1].split("/", 2)[2]
        filepath = os.path.join(serve_dir, filename)
        print("filename: " + filename)
        print("filepath: " + filepath)
        if os.path.isfile(filepath):
            # get file size
            file_size = os.path.getsize(filepath)
            # send back the file as body, and set the content length
            client.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: " + str(file_size).encode("utf-8") + b"\r\n\r\n")
            with open(filepath, "rb") as f:
                client.sendfile(f)
        else:
            client.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")
    else:
        client.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")


if __name__ == "__main__":
    main()
