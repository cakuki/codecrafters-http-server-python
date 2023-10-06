import socket


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    client, addr = server_socket.accept() # wait for client

    request = client.recv(1024)
    
    if request.startswith(b"GET / "):
        client.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
    elif request.startswith(b"GET /echo/"):
        url = request.decode("utf-8").split("\r\n")[0].split(" ")[1]
        # split url after second slash, but only once
        arg = url.split("/", 2)[2]
        # send back the argument as body, and set the content length
        client.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: " + str(len(arg)).encode("utf-8") + b"\r\n\r\n" + arg.encode("utf-8"))
    else:
        client.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")


if __name__ == "__main__":
    main()
