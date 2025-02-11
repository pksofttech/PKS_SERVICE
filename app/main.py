"""Main.py for Start of app"""

from fastapi import FastAPI, Request, staticfiles
from starlette.middleware.cors import CORSMiddleware

from app.stdio import print_success, print_warning, time_now


from app.service import mqtt_service

# ? Setting router path
from app.routes import api, websocket


async def lifespan(app_fastapi: FastAPI):
    """lifespan for start proseecss pre load"""
    print(app_fastapi)
    print_success(f"Server Start Time : {time_now()}")
    await mqtt_service.startup()
    yield
    # Clean up the ML models and release the resources
    print_warning(f"Server shutdown Time : {time_now()}")
    print_success(f"Server Start Time : {time_now()}")
    await mqtt_service.shutdown()


app = FastAPI(
    title="PKS-SERVICES-API",
    version="0.0.30",
    description="Service For PKSOFTTECH.ORG SYSTEMS",
    lifespan=lifespan,
)

app.mount("/static", staticfiles.StaticFiles(directory="./static"), name="static")
# app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def middle_process_time(request: Request, call_next):
    """middle ware"""
    start_time = time_now()
    response = await call_next(request)
    process_time = time_now() - start_time
    # response.headers["Process-Time"] = str(process_time)
    print_success(f"Process time :{process_time.microseconds/1000} ms")
    return response


app.include_router(websocket.router)
app.include_router(api.router)


# @app.exception_handler(HTTPException)
# async def app_exception_handler(request: Request, exception: HTTPException):
#     url_str = str(request.url).split("/")[-1]
#     # print_error(url_str)
#     if request.method == "GET":
#         print_error(exception.detail)
#         if exception.detail == "Not Found":
#             if "." in url_str:
#                 return HTMLResponse(str(exception.detail), status_code=exception.status_code)
#             return RedirectResponse(url=f"/page_404?url={request.url}")
#         return PlainTextResponse(str(exception.detail), status_code=exception.status_code)

#     else:
#         return JSONResponse(str(exception.detail), status_code=exception.status_code)
