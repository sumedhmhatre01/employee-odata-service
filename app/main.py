import os
import secrets

from dotenv import load_dotenv

from fastapi import (
    FastAPI,
    Request,
    HTTPException,
    Depends,
)

from fastapi.security import APIKeyHeader

from fastapi.responses import Response, JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.routes.employee_routes import router as employee_router
from app.utils.odata_metadata import ODATA_METADATA

# --------------------------------------------------
# Load Environment Variables
# --------------------------------------------------

load_dotenv()

API_KEY = os.getenv("API_KEY")


# --------------------------------------------------
# Initialize FastAPI Application
# --------------------------------------------------

app = FastAPI(
    title="Employee Management OData V2 Service",
    description="Mock Employee Management Service for SAP CPI Integration",
    version="1.0.0",
)


# --------------------------------------------------
# Swagger API Key Security Configuration
# --------------------------------------------------

api_key_header = APIKeyHeader(
    name="X-API-Key",
    scheme_name="APIKeyAuthentication",
    description="Enter your Employee API Key",
    auto_error=False,
)


# --------------------------------------------------
# API Key Authentication
# --------------------------------------------------


async def verify_api_key(
    x_api_key: str | None = Depends(api_key_header),
):

    if not API_KEY:
        raise RuntimeError("API_KEY is not configured in the .env file.")

    if not x_api_key or not secrets.compare_digest(
        x_api_key,
        API_KEY,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key.",
        )


# --------------------------------------------------
# OData V2 Error Response Helper
# --------------------------------------------------


def odata_error_response(message, code, status_code):

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": str(code),
                "message": {
                    "lang": "en-US",
                    "value": str(message),
                },
            }
        },
        headers={
            "DataServiceVersion": "2.0",
            "MaxDataServiceVersion": "2.0",
        },
    )


# --------------------------------------------------
# HTTP Exception Handler
# --------------------------------------------------


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
):

    return odata_error_response(
        message=exc.detail,
        code=exc.status_code,
        status_code=exc.status_code,
    )


# --------------------------------------------------
# Request Validation Exception Handler
# --------------------------------------------------


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):

    errors = []

    for error in exc.errors():
        field = " -> ".join(str(item) for item in error["loc"])
        message = error["msg"]
        errors.append(f"{field}: {message}")

    error_message = "; ".join(errors)

    return odata_error_response(
        message=error_message,
        code="400",
        status_code=400,
    )


# --------------------------------------------------
# OData V2 Protocol Middleware
# --------------------------------------------------


@app.middleware("http")
async def odata_protocol_middleware(request: Request, call_next):

    # Validate incoming DataServiceVersion
    data_service_version = request.headers.get("DataServiceVersion")

    if data_service_version:

        try:
            version = float(data_service_version.split(";")[0].strip())

            if version > 2.0:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": {
                            "code": "UnsupportedVersion",
                            "message": {
                                "lang": "en-US",
                                "value": "Only OData V2.0 is supported.",
                            },
                        }
                    },
                    headers={
                        "DataServiceVersion": "2.0",
                        "MaxDataServiceVersion": "2.0",
                    },
                )

        except ValueError:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "InvalidVersion",
                        "message": {
                            "lang": "en-US",
                            "value": "Invalid DataServiceVersion header.",
                        },
                    }
                },
                headers={
                    "DataServiceVersion": "2.0",
                    "MaxDataServiceVersion": "2.0",
                },
            )

    # Process request
    response = await call_next(request)

    # Add OData V2 response headers
    response.headers["DataServiceVersion"] = "2.0"
    response.headers["MaxDataServiceVersion"] = "2.0"
    response.headers["Vary"] = "Accept"

    return response


# --------------------------------------------------
# Register Employee API Routes
# --------------------------------------------------

app.include_router(
    employee_router,
    prefix="/odata/v2",
    tags=["Employees"],
    dependencies=[Depends(verify_api_key)],
)


# --------------------------------------------------
# Home Endpoint
# --------------------------------------------------


@app.get("/")
def home():

    return {
        "message": "Employee Management OData V2 Service",
        "status": "Running",
        "version": "1.0.0",
    }


# --------------------------------------------------
# Health Check Endpoint
# --------------------------------------------------


@app.get("/health")
def health_check():

    return {"status": "healthy"}


# --------------------------------------------------
# OData V2 Service Document Endpoint
# --------------------------------------------------


@app.get("/odata/v2/", include_in_schema=False)
def get_service_document():

    return JSONResponse(
        content={"d": {"EntitySets": ["Employees"]}},
        headers={
            "DataServiceVersion": "2.0",
            "MaxDataServiceVersion": "2.0",
        },
    )


# --------------------------------------------------
# OData V2 Metadata Endpoint
# --------------------------------------------------


@app.get("/odata/v2/$metadata", include_in_schema=False)
def get_odata_metadata():

    return Response(
        content=ODATA_METADATA,
        media_type="application/xml",
        headers={
            "DataServiceVersion": "2.0",
            "MaxDataServiceVersion": "2.0",
        },
    )
