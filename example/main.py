import sys

sys.path.append("..")

from microserve import MicroServeRouter


def main():
    router = MicroServeRouter()
    router.get("/", get_handler)
    router.get("/get", get_handler)
    router.post("/post", post_handler)
    router.post("/post/", post_trail_handler)
    router.get("/user/:name", var_handler)
    router.get("/user/:name/add", var_get_handler)
    router.run()


def get_handler(ctx):
    ctx.return_code = 201
    ctx.json({"hello": "world"})


def post_handler(ctx):
    ctx.return_code = 202
    ctx.json('{"hello": "world"}')


def post_trail_handler(ctx):
    ctx.json({"post": "trail"})


def var_handler(ctx):
    ctx.json({"name": ctx.get_path_variable("name")})


def var_get_handler(ctx):
    ctx.json({"name": ctx.get_path_variable("name"), "method": "add"})


if __name__ == "__main__":
    main()
