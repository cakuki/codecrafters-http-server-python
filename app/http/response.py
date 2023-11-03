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
