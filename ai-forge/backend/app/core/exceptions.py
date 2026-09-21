from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger


class AppError(Exception):
    def __init__(self, message: str, code: int = 400, status_code: int = 400):
        super().__init__(message)
        self.message, self.code, self.status_code = message, code, status_code


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message, "data": None},
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(_: Request, exc: Exception):
        logger.exception(exc)
        return JSONResponse(
            status_code=500, content={"code": 500, "message": "服务器内部错误", "data": None}
        )
