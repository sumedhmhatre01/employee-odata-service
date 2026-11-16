import json
import threading
from pathlib import Path

from app.models.employee import Employee


class EmployeeRepository:

    BASE_DIR = Path(__file__).resolve().parents[2]
    DATA_FILE = BASE_DIR / "data" / "employees.json"

    _lock = threading.RLock()

    @classmethod
    def _read_data(cls):
        """Read employee records from JSON file."""

        with cls._lock:
            if not cls.DATA_FILE.exists():
                cls.DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
                cls._write_data([])
                return []

            try:
                with open(cls.DATA_FILE, "r", encoding="utf-8") as file:
                    return json.load(file)

            except json.JSONDecodeError as error:
                raise RuntimeError(
                    "Employee JSON file contains invalid data."
                ) from error

    @classmethod
    def _write_data(cls, employees):
        """Save employee records to JSON file."""

        with cls._lock:
            cls.DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

            temp_file = cls.DATA_FILE.with_suffix(".tmp")

            with open(temp_file, "w", encoding="utf-8") as file:
                json.dump(employees, file, indent=4)

            temp_file.replace(cls.DATA_FILE)

    @classmethod
    def get_all(cls):
        """Retrieve all employees."""

        with cls._lock:
            return cls._read_data()

    @classmethod
    def get_by_id(cls, employee_id):
        """Retrieve employee by ID."""

        with cls._lock:
            employees = cls._read_data()

            for employee in employees:
                if employee["EmployeeID"] == employee_id:
                    return employee

            return None

    @classmethod
    def create(cls, employee):
        """Add a new employee."""

        with cls._lock:
            employees = cls._read_data()

            employee_data = employee.model_dump()

            employees.append(employee_data)

            cls._write_data(employees)

            return employee_data

    @classmethod
    def update(cls, employee_id, updated_data):
        """Update employee details."""

        with cls._lock:
            employees = cls._read_data()

            for index, employee in enumerate(employees):

                if employee["EmployeeID"] == employee_id:

                    employees[index].update(updated_data)

                    cls._write_data(employees)

                    return employees[index]

            return None

    @classmethod
    def delete(cls, employee_id):
        """Delete employee by ID."""

        with cls._lock:
            employees = cls._read_data()

            for index, employee in enumerate(employees):

                if employee["EmployeeID"] == employee_id:

                    deleted_employee = employees.pop(index)

                    cls._write_data(employees)

                    return deleted_employee

            return None
