import re
from xml.etree.ElementTree import fromstring

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

router = APIRouter()


# --------------------------------------------------
# XML / JSON REQUEST HELPERS
# --------------------------------------------------


def parse_cpi_xml(xml_data: bytes, partial=False):
    """
    Parse XML generated for the SAP CPI OData V2 adapter.

    Supports:
    1. Atom XML entry
    2. CPI generated Employees / Employee XML structure
    """

    try:
        root = fromstring(xml_data)

        # First, try the Atom XML format.
        if root.tag.endswith("entry"):
            if not partial:
                return parse_employee_xml(xml_data)

            properties = root.find(f".//{{{METADATA_NS}}}properties")

            if properties is None:
                raise ValueError("Employee properties not found.")

            salary = properties.find(f"{{{DATA_NS}}}Salary")

            if salary is None or salary.text is None:
                raise ValueError("Salary is required for PATCH.")

            return {"Salary": float(salary.text)}

        # Handle CPI generated XML structure:
        # Employees -> Employee -> EmployeeID, Salary

        employee_node = None

        if root.tag.endswith("Employee"):
            employee_node = root
        else:
            for node in root.iter():
                if node.tag.endswith("Employee"):
                    employee_node = node
                    break

        if employee_node is None:
            raise ValueError("Employee element not found in XML.")

        employee_data = {}

        for node in employee_node:
            field_name = node.tag.split("}")[-1]

            if node.text is not None:
                value = node.text.strip()

                if field_name == "Salary":
                    value = float(value)

                employee_data[field_name] = value

        if partial:
            if "Salary" not in employee_data:
                raise ValueError("Salary is required for PATCH.")

            return {"Salary": employee_data["Salary"]}

        return employee_data

    except Exception as error:
        raise ValueError(f"Invalid employee XML: {error}") from error


async def read_request_data(request: Request, partial=False):
    """Read employee data from JSON or XML."""

    body = await request.body()

    content_type = request.headers.get("content-type", "").lower()

    if not body:
        raise HTTPException(
            status_code=400,
            detail="Request body is empty.",
        )

    if "json" in content_type:
        try:
            import json

            return json.loads(body)

        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON request body.",
            )

    if "xml" in content_type or "atom" in content_type:
        try:
            return parse_cpi_xml(body, partial=partial)

        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail=str(error),
            )

    raise HTTPException(
        status_code=415,
        detail="Supported content types are JSON and XML.",
    )


def is_xml_response(accept: str):
    """Check whether the client requests XML."""

    accept = accept.lower()

    return "application/atom+xml" in accept or "application/xml" in accept


def xml_entry_response(employee, status_code=200):
    """Return an employee as Atom XML."""

    return Response(
        content=create_employee_entry(employee),
        status_code=status_code,
        media_type="application/atom+xml",
    )


# --------------------------------------------------
# DEPARTMENT FILTER
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
# GET ALL EMPLOYEES
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
# GET EMPLOYEE BY ID
# --------------------------------------------------


@router.get("/Employees('{employee_id}')")
@router.get("/Employees(EmployeeID='{employee_id}')")
def get_employee(
    employee_id: str,
    request: Request,
):
    employee = EmployeeService.get_employee(employee_id)

    if is_xml_response(request.headers.get("accept", "")):
        return xml_entry_response(employee)

    return ODataResponse.single(employee)


# --------------------------------------------------
# POST CREATE EMPLOYEE
# --------------------------------------------------


@router.post("/Employees")
async def create_employee(request: Request):

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
# PUT UPDATE EMPLOYEE
# --------------------------------------------------


@router.put("/Employees('{employee_id}')")
@router.put("/Employees(EmployeeID='{employee_id}')")
async def update_employee(
    employee_id: str,
    request: Request,
):

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
# PATCH UPDATE EMPLOYEE SALARY
# --------------------------------------------------


@router.patch("/Employees('{employee_id}')")
@router.patch("/Employees(EmployeeID='{employee_id}')")
async def patch_employee(
    employee_id: str,
    request: Request,
):

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
# DELETE EMPLOYEE
# --------------------------------------------------


@router.delete("/Employees('{employee_id}')")
@router.delete("/Employees(EmployeeID='{employee_id}')")
def delete_employee(employee_id: str):

    EmployeeService.delete_employee(employee_id)

    return ODataResponse.deleted()
