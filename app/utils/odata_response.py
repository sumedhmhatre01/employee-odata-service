from fastapi.responses import JSONResponse


class ODataResponse:

    # OData V2 service configuration
    SERVICE_ROOT = "/odata/v2/"
    ENTITY_TYPE = "EmployeeService.Employee"

    @classmethod
    def add_metadata(cls, employee):
        """Add OData V2 metadata to an employee record."""

        employee_data = employee.copy()

        employee_id = employee_data["EmployeeID"]

        employee_data["__metadata"] = {
            "uri": (f"{cls.SERVICE_ROOT}Employees('{employee_id}')"),
            "type": cls.ENTITY_TYPE,
        }

        return employee_data

    @classmethod
    def collection(cls, data):
        """Format multiple records in OData V2 format."""

        employees = [cls.add_metadata(employee) for employee in data]

        return JSONResponse(
            content={"d": {"results": employees}},
            status_code=200,
        )

    @classmethod
    def single(cls, data):
        """Format a single record in OData V2 format."""

        employee = cls.add_metadata(data)

        return JSONResponse(
            content={"d": employee},
            status_code=200,
        )

    @classmethod
    def created(cls, data):
        """Return successful creation response."""

        employee = cls.add_metadata(data)

        return JSONResponse(
            content={"d": employee},
            status_code=201,
        )

    @staticmethod
    def deleted():
        """Return successful deletion response."""

        return JSONResponse(
            content=None,
            status_code=204,
        )

    @staticmethod
    def error(message, code="400", status_code=400):
        """Format errors in OData V2 style."""

        return JSONResponse(
            content={
                "error": {
                    "code": str(code),
                    "message": {
                        "lang": "en-US",
                        "value": str(message),
                    },
                }
            },
            status_code=status_code,
        )
