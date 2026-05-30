from threading import Thread

from omnidoer.demo.server import DemoHandler, ThreadingHTTPServer


class DemoServerFixture:
    def __enter__(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), DemoHandler)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.origin = f"http://127.0.0.1:{self.server.server_address[1]}"
        return self

    def __exit__(self, exc_type, exc, tb):
        self.server.shutdown()
        self.server.server_close()
