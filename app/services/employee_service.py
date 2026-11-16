from fastapi import HTTPException, status

from app.models.employee import EmployeeCreate, EmployeeUpdate, EmployeePatch

from app.storage.employee_repository import EmployeeRepository


class EmployeeService:

    @staticmethod
    def get_all_employees(department=None):
        """Retrieve all employees or filter by department."""

        employees = EmployeeRepository.get_all()

        if department:
            employees = [
                employee
                for employee in employees
                if employee["Department"].lower() == department.lower()
            ]

        return employees

    @staticmethod
    def get_employee(employee_id):
        """Retrieve employee by ID."""

        employee = EmployeeRepository.get_by_id(employee_id)

        if employee is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee {employee_id} not found.",
            )

        return employee

    @staticmethod
    def create_employee(employee: EmployeeCreate):
        """Create a new employee."""

        existing_employee = EmployeeRepository.get_by_id(employee.EmployeeID)

        if existing_employee:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Employee ID {employee.EmployeeID} already exists.",
            )

        return EmployeeRepository.create(employee)

    @staticmethod
    def update_employee(employee_id, employee: EmployeeUpdate):
        """Update complete employee details."""

        existing_employee = EmployeeRepository.get_by_id(employee_id)

        if existing_employee is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee {employee_id} not found.",
            )

        updated_data = employee.model_dump(exclude_unset=True)

        required_fields = {"Name", "Department", "Salary"}

        if not required_fields.issubset(updated_data):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="PUT requires Name, Department and Salary.",
            )

        if any(value is None for value in updated_data.values()):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Employee fields cannot be null.",
            )

        return EmployeeRepository.update(employee_id, updated_data)

    @staticmethod
    def patch_employee(employee_id, employee: EmployeePatch):
        """Partially update employee salary."""

        existing_employee = EmployeeRepository.get_by_id(employee_id)

        if existing_employee is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee {employee_id} not found.",
            )

        updated_data = employee.model_dump(exclude_unset=True)

        if not updated_data or updated_data.get("Salary") is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Salary is required for PATCH.",
            )

        return EmployeeRepository.update(employee_id, updated_data)

    @staticmethod
    def delete_employee(employee_id):
        """Delete employee by ID."""

        deleted_employee = EmployeeRepository.delete(employee_id)

        if deleted_employee is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee {employee_id} not found.",
            )

        return deleted_employee
