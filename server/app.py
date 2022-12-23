from sanic import Request, Sanic
from sanic.response import file, text

from server.log import init_logging
from server.tasks.dump_db import dump

app = Sanic("sanic", configure_logging=False)


@app.get("/")
async def index(_):
    return await file("client/index.html")


@app.post("/dump/")
async def dump_db(request: Request):
    dump.delay(request.json)
    return text("success")


if __name__ == "__main__":
    init_logging()
    app.run(host="0.0.0.0", port=5000, fast=True)
