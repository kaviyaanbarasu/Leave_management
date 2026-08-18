from datetime import date
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional


class EmployeeBase(BaseModel):
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
    employee_id: str = Field(..., min_length=1)
    password: Optional[str] = Field(default="password123")


class EmployeeUpdate(BaseModel):
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
    employee_id: str
    manager_name: Optional[str] = None
    location_name: Optional[str] = None
    country: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
