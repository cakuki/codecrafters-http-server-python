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
