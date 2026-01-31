from fastapi import FastAPI
from psycopg2 import IntegrityError

#
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
# from authlib.jose import JoseError
from sqlalchemy.exc import IntegrityError
# from psycopg2.errors import CheckViolation, UniqueViolation, ForeignKeyViolation

from .handlers import ExceptionHandler
from .custom_exceptions import CustomAPIException
import logging

logger = logging.getLogger(__name__)

# def setup_exception_handlers(app: FastAPI, config):
#     """Register all exception handlers with the FastAPI application"""
#     handler = ExceptionHandler(config)
    
#     # Register custom exception handler
#     @app.exception_handler(CustomAPIException)
#     async def custom_api_exception_handler(request, exc: CustomAPIException):
#         logger.warning(
#             f"Custom API exception at {request.url.path}: {exc.message}"
#         )
        
#         from app.utils.responses import api_response
        
#         return api_response(
#             success=False,
#             message=exc.message,
#             errors={
#                 "error_code": exc.error_code,
#                 "details": exc.details
#             },
#             status_code=exc.status_code,
#             path=str(request.url.path)
#         )
    
#     # Register other exception handlers
#     app.add_exception_handler(CustomAPIException, custom_api_exception_handler)
#     app.add_exception_handler(Exception, handler.global_exception_handler)
#     app.add_exception_handler(StarletteHTTPException, handler.http_exception_handler)
#     app.add_exception_handler(RequestValidationError, handler.validation_exception_handler)
#     # app.add_exception_handler(JoseError, handler.authlib_jwt_exception_handler)
#     app.add_exception_handler(IntegrityError, handler.integrity_error_handler)
    
#     logger.info("✅ Exception handlers registered successfully")

# v2 - correct order
def setup_exception_handlers(app: FastAPI, config):
    handler = ExceptionHandler(config)

    # 1️⃣ Custom domain exceptions
    app.add_exception_handler(
        CustomAPIException,
        handler.custom_api_exception_handler
    )

    # 2️⃣ Request validation (Pydantic, JSON parsing, body errors)
    app.add_exception_handler(
        RequestValidationError,
        handler.validation_exception_handler
    )

    # 3️⃣ HTTP errors (404, 405, etc.)
    app.add_exception_handler(
        StarletteHTTPException,
        handler.http_exception_handler
    )

    # 4️⃣ Database integrity errors
    app.add_exception_handler(
        IntegrityError,
        handler.integrity_error_handler
    )

    # 5️⃣ LAST RESORT — unknown errors
    app.add_exception_handler(
        Exception,
        handler.global_exception_handler
    )

    logger.info("✅ Exception handlers registered successfully")

# Import for easy access
from .custom_exceptions import (
    CustomAPIException,
    AuthenticationException,
    AuthorizationException,
    ResourceNotFoundException,
    ValidationException,
    BusinessRuleException,
    ExternalServiceException
)