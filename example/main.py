import sys

sys.path.append("..")

from microserve import MicroServeRouter


def main():
    router = MicroServeRouter()
    router.get("/test", get_handler)
    router.post("/test", post_handler)
    router.head("/test", head_handler)
    router.put("/test", put_handler)
    router.patch("/test", patch_handler)
    router.delete("/test", delete_handler)
    router.get("/download", download_handler)
    router.get("/html", html_handler)
    router.get("/xml", xml_handler)
    router.get("/middleware1", get_handler, middleware1)
    router.get("/middleware2", get_handler, middleware2)
    router.get("/middleware1and2", get_handler, middleware1, middleware2)
    try:
        router.run()
    except OSError:
        pass


def middleware1(ctx):
    ctx.abort(400)


def middleware2(ctx):
    print("middleware2")


def get_handler(ctx):
    ctx.json({"method": "get"})


def post_handler(ctx):
    ctx.json({"method": "post"})


def head_handler(ctx):
    ctx.return_code = 201


def put_handler(ctx):
    ctx.json({"method": "put"})


def patch_handler(ctx):
    ctx.json({"method": "patch"})


def delete_handler(ctx):
    ctx.json({"method": "delete"})


def download_handler(ctx):
    ctx.file("test.txt")


def html_handler(ctx):
    ctx.html("test.html")


def xml_handler(ctx):
    ctx.xml("<test>test</test>")


if __name__ == "__main__":
    main()
