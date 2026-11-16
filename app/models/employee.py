from pydantic import BaseModel, Field, ConfigDict


class Employee(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    EmployeeID: str = Field(..., min_length=1, description="Unique employee ID")

    Name: str = Field(..., min_length=1, description="Employee name")

    Department: str = Field(..., min_length=1, description="Employee department")

    Salary: float = Field(..., ge=0, description="Employee salary")


class EmployeeCreate(Employee):
    pass


class EmployeeUpdate(BaseModel):
    Name: str | None = None
    Department: str | None = None
    Salary: float | None = Field(default=None, ge=0)


class EmployeePatch(BaseModel):
    Salary: float | None = Field(default=None, ge=0)
