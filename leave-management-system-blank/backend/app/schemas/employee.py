from datetime import date
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional


class EmployeeBase(BaseModel):
    """Define the base employee schema.

    Args:
        name (str):
        email (EmailStr):
        department (str):
        designation (str):
        grade (str):
        location_id (str):
        joining_date (date):
        status (str): Defaults to "ACTIVE".
        role (str): Defaults to "EMPLOYEE".
        manager_id (Optional[str]): Optional manager identifier.
    """
    name: str = Field(..., min_length=1)
    email: EmailStr = Field(...)
    department: str = Field(..., min_length=1)
    designation: str = Field(..., min_length=1)
    grade: str = Field(..., min_length=1)
    location_id: str = Field(..., min_length=1)
    joining_date: date = Field(...)
    status: str = Field(default="ACTIVE")
    role: str = Field(default="EMPLOYEE")
    manager_id: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    """Create a new employee record.

    Args:
        name (str):
        email (EmailStr):
        department (str):
        designation (str):
        grade (str):
        location_id (str):
        joining_date (date):
        status (str): Defaults to "ACTIVE".
        role (str): Defaults to "EMPLOYEE".
        manager_id (Optional[str]): Optional manager identifier.
        employee_id (str):
        password (Optional[str]): Defaults to "password123".
    """
    employee_id: str = Field(..., min_length=1)
    password: Optional[str] = Field(default="password123")


class EmployeeUpdate(BaseModel):
    """Update an existing employee record.

    Args:
        name (Optional[str]):
        email (Optional[EmailStr]):
        department (Optional[str]):
        designation (Optional[str]):
        grade (Optional[str]):
        location_id (Optional[str]):
        joining_date (Optional[date]):
        status (Optional[str]):
        role (Optional[str]):
        password (Optional[str]):
        manager_id (Optional[str]):
    """
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    grade: Optional[str] = None
    location_id: Optional[str] = None
    joining_date: Optional[date] = None
    status: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None
    manager_id: Optional[str] = None


class EmployeeResponse(EmployeeBase):
    """Represent an employee response schema.

    Args:
        name (str):
        email (EmailStr):
        department (str):
        designation (str):
        grade (str):
        location_id (str):
        joining_date (date):
        status (str):
        role (str):
        manager_id (Optional[str]):
        employee_id (str):
        manager_name (Optional[str]):
        location_name (Optional[str]):
        country (Optional[str]):
    """
    employee_id: str
    manager_name: Optional[str] = None
    location_name: Optional[str] = None
    country: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
