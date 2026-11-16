import re

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.models.employee import EmployeeCreate, EmployeeUpdate, EmployeePatch

from app.services.employee_service import EmployeeService
from app.utils.odata_response import ODataResponse

router = APIRouter()


def extract_department_filter(filter_expression):
    """Extract Department filter from OData V2 query."""

    if not filter_expression:
        return None

    pattern = r"^Department\s+eq\s+'([^']+)'$"

    match = re.fullmatch(pattern, filter_expression.strip(), re.IGNORECASE)

    if not match:
        raise HTTPException(
            status_code=400, detail="Supported filter: Department eq 'IT'"
        )

    return match.group(1)


@router.get("/Employees")
def get_employees(filter_expression: str | None = Query(default=None, alias="$filter")):
    """Get all employees or filter by department."""

    department = extract_department_filter(filter_expression)

    employees = EmployeeService.get_all_employees(department)

    return ODataResponse.collection(employees)


@router.get("/Employees('{employee_id}')")
def get_employee(employee_id: str):
    """Get employee by ID."""

    employee = EmployeeService.get_employee(employee_id)

    return ODataResponse.single(employee)


@router.post("/Employees", status_code=201)
def create_employee(employee: EmployeeCreate):
    """Create a new employee."""

    created_employee = EmployeeService.create_employee(employee)

    return ODataResponse.created(created_employee)


@router.put("/Employees('{employee_id}')")
def update_employee(employee_id: str, employee: EmployeeUpdate):
    """Replace employee details."""

    updated_employee = EmployeeService.update_employee(employee_id, employee)

    return ODataResponse.single(updated_employee)


@router.patch("/Employees('{employee_id}')")
def patch_employee(employee_id: str, employee: EmployeePatch):
    """Partially update employee details."""

    updated_employee = EmployeeService.patch_employee(employee_id, employee)

    return ODataResponse.single(updated_employee)


@router.delete("/Employees('{employee_id}')")
def delete_employee(employee_id: str):
    """Delete employee."""

    EmployeeService.delete_employee(employee_id)

    return ODataResponse.deleted()
