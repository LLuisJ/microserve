from enum import Enum
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import signal


class MicroServeError(Enum):
    NONE = 200
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    MIDDLEWARE_ERROR = -1


class MicroServeNode:
    segment = None
    children = {}
    handlers = {}
    variable_name = ""
    middlewares = {}

    def __init__(self, segment, children, handlers, variable_name):
        self.segment = segment
        self.children = children
        self.handlers = handlers
        self.variable_name = variable_name
        self.middlewares = {}


class MicroServeRouter:
    root = None
    server = None
    handler = None

    def __init__(self):
        self.root = MicroServeNode(None, {}, {}, "")

    def get(self, path, handler, *middlewares):
        self._add_route("GET", path, handler, middlewares)

    def post(self, path, handler, *middlewares):
        self._add_route("POST", path, handler, middlewares)

    def head(self, path, handler, *middlewares):
        self._add_route("HEAD", path, handler, middlewares)

    def put(self, path, handler, *middlewares):
        self._add_route("PUT", path, handler, middlewares)

    def patch(self, path, handler, *middlewares):
        self._add_route("PATCH", path, handler, middlewares)

    def delete(self, path, handler, *middlewares):
        self._add_route("DELETE", path, handler, middlewares)

    def options(self, path, handler, *middlewares):
        self._add_route("OPTIONS", path, handler, middlewares)

    def _add_route(self, method, path, handler, *middlewares):
        _middleware = []
        if middlewares[0]:
            for middleware in middlewares[0]:
                if not callable(middleware):
                    raise TypeError("Middleware {} is not callable".format(middleware))
                _middleware.append(middleware)
        current_node = self.root
        segments = path.split("/")
        for segment in segments:
            if segment not in current_node.children:
                if segment.startswith(":"):
                    if ":variable" not in current_node.children:
                        current_node.children[":variable"] = MicroServeNode(
                            ":variable", {}, {}, segment.removeprefix(":")
                        )
                    current_node = current_node.children[":variable"]
                    continue
                else:
                    current_node.children[segment] = MicroServeNode(segment, {}, {}, "")
            current_node = current_node.children[segment]
        current_node.handlers[method] = handler
        current_node.middlewares[method] = _middleware

    def match(self, method, path):
        current_node = self.root
        segments = path.split("/")
        ctx = MicroServeContext.create_context()
        for segment in segments:
            if segment not in current_node.children:
                if ":variable" in current_node.children:
                    current_node = current_node.children[":variable"]
                    ctx[0].set_path_variable(current_node.variable_name, segment)
                    continue
                else:
                    return MicroServeError.NOT_FOUND, None, ctx
            current_node = current_node.children[segment]
        if method not in current_node.handlers:
            return MicroServeError.METHOD_NOT_ALLOWED, None, ctx
        middlewares = current_node.middlewares[method]
        if middlewares:
            for middleware in middlewares:
                if ctx[0].request_aborted:
                    break
                middleware(ctx[0])
        if ctx[0].request_aborted:
            return MicroServeError.MIDDLEWARE_ERROR, None, ctx
        return MicroServeError.NONE, current_node.handlers[method], ctx

    def run(self, host="127.0.0.1", port=8080):
        signal.signal(signal.SIGINT, self.stop)
        self.server = HTTPServer((host, port), create_micro_serve_handler(self))
        self.server.serve_forever()

    def stop(self, _, __):
        self.server.server_close()


class MicroServeContext:
    path_variables = {}
    return_code = 200
    request_headers = {}
    response_headers = {}
    response_data = ""
    request_aborted = False

    def set_headers(self, headers):
        self.request_header = headers

    def set_path_variable(self, name, value):
        self.path_variables[name] = value

    def get_path_variable(self, name):
        return self.path_variables[name]

    def json(self, data):
        self.response_headers["Content-Type"] = "application/json"
        if isinstance(data, dict):
            self.response_data = json.dumps(data)
        else:
            self.response_data = data
        self.response_headers["Content-Length"] = len(self.response_data)

    def text(self, data):
        self.response_headers["Content-Type"] = "text/plain"
        self.response_headers["Content-Length"] = len(self.response_data)
        self.response_data = data

    def html(self, file):
        self.response_headers["Content-Type"] = "text/html"
        with open(file, "r") as f:
            self.response_data = f.read()
            self.response_headers["Content-Length"] = len(self.response_data)

    def xml(self, data):
        self.response_headers["Content-Type"] = "text/xml"
        self.response_headers["Content-Length"] = len(data)
        self.response_data = data

    def file(self, path):
        self.response_headers["Content-Type"] = "application/octet-stream"
        self.response_headers["Content-Disposition"] = f"attachment; filename={path}"
        with open(path, "rb") as f:
            self.response_data = f.read()
            self.response_headers["Content-Length"] = len(self.response_data)

    def abort(self, code):
        self.return_code = code
        self.request_aborted = True

    @staticmethod
    def create_context():
        ctx = MicroServeContext()
        return [ctx]


def create_micro_serve_handler(router):
    class MicroServeHandler(BaseHTTPRequestHandler):
        server_version = "MicroServe/1.0"
        sys_version = ""

        def do_GET(self):
            self._match("GET", self.path)

        def do_POST(self):
            self._match("POST", self.path)

        def do_HEAD(self):
            self._match("HEAD", self.path)

        def do_PUT(self):
            self._match("PUT", self.path)

        def do_PATCH(self):
            self._match("PATCH", self.path)

        def do_DELETE(self):
            self._match("DELETE", self.path)

        def do_OPTIONS(self):
            self._match("OPTIONS", self.path)

        def _match(self, method, path):
            error, handler, ctx = router.match(method, path)
            if error != MicroServeError.NONE:
                if error != MicroServeError.MIDDLEWARE_ERROR:
                    self.send_response(error.value)
                else:
                    self.send_response(ctx[0].return_code)
                self.end_headers()
            else:
                handler(ctx[0])
                self._respond(ctx[0])

        def _respond(self, ctx):
            self.send_response(ctx.return_code)
            for header, value in ctx.response_headers.items():
                self.send_header(header, value)
            self.end_headers()
            if not isinstance(ctx.response_data, bytes):
                self.wfile.write(ctx.response_data.encode("utf-8"))
            else:
                self.wfile.write(ctx.response_data)

        def log_message(self, format, *args):
            pass

    return MicroServeHandler
