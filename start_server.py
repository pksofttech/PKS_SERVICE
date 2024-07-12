import uvicorn
import logging

DEBUG = True
LOGGING_LEVEL = logging.INFO

LOGGING_CONFIG = uvicorn.config.LOGGING_CONFIG
if DEBUG:
    LOGGING_CONFIG["loggers"]["uvicorn"]["level"] = "DEBUG"
    LOGGING_CONFIG["loggers"]["uvicorn.error"]["level"] = "DEBUG"
    LOGGING_CONFIG["loggers"]["uvicorn.access"]["level"] = "DEBUG"
LOGGING_CONFIG["loggers"]["foo"] = {
    "handlers": ["default"],
    "level": LOGGING_LEVEL,
    "propagate": False,
}

print("*" * 150)
print("\n\nStarting Server...")
if __name__ == "__main__":
    _host = "0.0.0.0"
    _port = 8000
    print(f"Start App Service at IP>>{_host}:{_port}")
    uvicorn.run(
        "app.main:app",
        # workers=2,
        host=_host,
        port=_port,
        # reload_includes=["*.html"],
        # reload_dirs=[
        #     "./app",
        #     "./templates",
        # ],
        reload=True,
        log_level=LOGGING_LEVEL,
        # log_level="debug" if DEBUG else "info",
        log_config=LOGGING_CONFIG,
    )
