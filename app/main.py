import socket


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)

    # listen for connections from client loop forever
    while True:
        client, address = server_socket.accept()
        request = client.recv(1024)
        handle_request(request, client)
        client.close()

def handle_request(request, client):
    # get user-agent header from request, which could be in any order
    user_agent = ""
    for line in request.decode("utf-8").split("\r\n"):
        if line.startswith("User-Agent:"):
            user_agent = line.split(" ", 1)[1]
    
    if request.startswith(b"GET / "):
        client.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
    elif request.startswith(b"GET /user-agent"):
        client.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: " + str(len(user_agent)).encode("utf-8") + b"\r\n\r\n" + user_agent.encode("utf-8"))
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
