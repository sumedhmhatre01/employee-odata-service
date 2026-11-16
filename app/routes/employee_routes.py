import re

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Request,
    Response,
    Header,
)

from app.models.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeePatch,
)

from app.services.employee_service import EmployeeService

from app.utils.odata_response import ODataResponse

from app.utils.odata_xml import (
    create_employee_entry,
    create_employee_feed,
    parse_employee_xml,
    DATA_NS,
    METADATA_NS,
)

from xml.etree.ElementTree import fromstring

router = APIRouter()


# --------------------------------------------------
# Request Format Helpers
# --------------------------------------------------


async def read_request_data(request: Request, partial=False):
    """
    Read employee data from JSON or Atom XML.
    """

    body = await request.body()

    content_type = request.headers.get("content-type", "").lower()

    if not body:
        raise HTTPException(
            status_code=400,
            detail="Request body is empty.",
        )

    if "json" in content_type:
        try:
            return await request.json()

        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON request body.",
            )

    if "xml" in content_type or "atom" in content_type:
        try:
            if not partial:
                return parse_employee_xml(body)

            root = fromstring(body)

            properties = root.find(f".//{{{METADATA_NS}}}properties")

            if properties is None:
                raise ValueError("Employee properties not found in XML.")

            salary = properties.find(f"{{{DATA_NS}}}Salary")

            if salary is None or salary.text is None:
                raise ValueError("Salary is required for PATCH.")

            return {"Salary": float(salary.text)}

        except Exception as error:
            raise HTTPException(
                status_code=400,
                detail=str(error),
            )

    raise HTTPException(
        status_code=415,
        detail="Supported content types are JSON and Atom XML.",
    )


def is_xml_response(accept: str):
    """
    Check whether the client requests an XML response.
    """

    accept = accept.lower()

    return "application/atom+xml" in accept or "application/xml" in accept


def xml_entry_response(employee, status_code=200):
    """Return one employee as an Atom XML entry."""

    return Response(
        content=create_employee_entry(employee),
        status_code=status_code,
        media_type="application/atom+xml",
    )


# --------------------------------------------------
# Department Filter
# --------------------------------------------------


def extract_department_filter(filter_expression):
    """Extract Department filter from OData V2 query."""

    if not filter_expression:
        return None

    pattern = r"^Department\s+eq\s+'([^']+)'$"

    match = re.fullmatch(
        pattern,
        filter_expression.strip(),
        re.IGNORECASE,
    )

    if not match:
        raise HTTPException(
            status_code=400,
            detail="Supported filter: Department eq 'IT'",
        )

    return match.group(1)


# --------------------------------------------------
# GET All Employees
# --------------------------------------------------


@router.get(
    "/Employees",
    responses={200: {"content": {"application/atom+xml": {}}}},
)
def get_employees(
    request: Request,
    accept: str = Header(
        default="application/json",
        alias="Accept",
    ),
    filter_expression: str | None = Query(
        default=None,
        alias="$filter",
    ),
):
    """Retrieve all employees or filter by department."""

    department = extract_department_filter(filter_expression)

    employees = EmployeeService.get_all_employees(department)

    if is_xml_response(accept):
        return Response(
            content=create_employee_feed(employees),
            status_code=200,
            media_type="application/atom+xml",
        )

    return ODataResponse.collection(employees)


# --------------------------------------------------
# GET Employee By ID
# --------------------------------------------------


@router.get("/Employees('{employee_id}')")
def get_employee(
    employee_id: str,
    request: Request,
):
    """Retrieve one employee by ID."""

    employee = EmployeeService.get_employee(employee_id)

    if is_xml_response(request.headers.get("accept", "")):
        return xml_entry_response(employee)

    return ODataResponse.single(employee)


# --------------------------------------------------
# POST Create Employee
# --------------------------------------------------


@router.post("/Employees")
async def create_employee(request: Request):
    """Create employee using JSON or Atom XML."""

    employee_data = await read_request_data(request)

    try:
        employee = EmployeeCreate(**employee_data)

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    created_employee = EmployeeService.create_employee(employee)

    if is_xml_response(request.headers.get("accept", "")):
        return xml_entry_response(
            created_employee,
            status_code=201,
        )

    return ODataResponse.created(created_employee)


# --------------------------------------------------
# PUT Update Employee
# --------------------------------------------------


@router.put("/Employees('{employee_id}')")
async def update_employee(
    employee_id: str,
    request: Request,
):
    """Replace employee details."""

    employee_data = await read_request_data(request)

    try:
        employee = EmployeeUpdate(**employee_data)

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    updated_employee = EmployeeService.update_employee(
        employee_id,
        employee,
    )

    if is_xml_response(request.headers.get("accept", "")):
        return xml_entry_response(updated_employee)

    return ODataResponse.single(updated_employee)


# --------------------------------------------------
# PATCH Update Employee Salary
# --------------------------------------------------


@router.patch("/Employees('{employee_id}')")
async def patch_employee(
    employee_id: str,
    request: Request,
):
    """Partially update employee salary."""

    employee_data = await read_request_data(
        request,
        partial=True,
    )

    try:
        employee = EmployeePatch(**employee_data)

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    updated_employee = EmployeeService.patch_employee(
        employee_id,
        employee,
    )

    if is_xml_response(request.headers.get("accept", "")):
        return xml_entry_response(updated_employee)

    return ODataResponse.single(updated_employee)


# --------------------------------------------------
# DELETE Employee
# --------------------------------------------------


@router.delete("/Employees('{employee_id}')")
def delete_employee(employee_id: str):
    """Delete employee."""

    EmployeeService.delete_employee(employee_id)

    return ODataResponse.deleted()
