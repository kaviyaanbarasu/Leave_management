from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from app.database import get_db
from app.models.employee import Employee

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str  # Can be employee_id or email
    password: Optional[str] = "password123"


class UserProfileResponse(BaseModel):
    employee_id: str
    name: str
    email: str
    department: str
    designation: str
    grade: str
    location_id: str
    role: str
    status: str


class LoginResponse(BaseModel):
    token: str
    user: UserProfileResponse


class PersonaResponse(BaseModel):
    employee_id: str
    name: str
    email: str
    location_id: str
    country: str
    flag: str
    role: str
    department: str
    designation: str
    grade: str


FLAG_MAP = {
    "BLR": "🇮🇳 India",
    "SG": "🇸🇬 Singapore",
    "NY": "🇺🇸 USA",
    "DXB": "🇦🇪 UAE",
    "LON": "🇬🇧 UK",
}


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    query_val = payload.username.strip()
    
    # Match by employee_id or email (case-insensitive)
    employee = (
        db.query(Employee)
        .filter(
            (Employee.employee_id.ilike(query_val)) | (Employee.email.ilike(query_val))
        )
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Employee '{payload.username}' not found. Please check your Employee ID or Email.",
        )

    if employee.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your employee account is inactive. Please contact HR.",
        )

    # Basic password check (default password is 'password123' or 'admin123')
    if employee.password and payload.password:
        if employee.password != payload.password and payload.password not in ["password123", "admin123"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password. (Default password is 'password123')",
            )

    token = f"session-{employee.employee_id}-{employee.role.lower()}"

    user_data = UserProfileResponse(
        employee_id=employee.employee_id,
        name=employee.name,
        email=employee.email,
        department=employee.department,
        designation=employee.designation,
        grade=employee.grade,
        location_id=employee.location_id,
        role=employee.role,
        status=employee.status,
    )

    return LoginResponse(token=token, user=user_data)


@router.get("/personas", response_model=List[PersonaResponse])
def get_personas(db: Session = Depends(get_db)):
    """
    Returns available personas across locations for 1-click testing.
    """
    employees = db.query(Employee).filter(Employee.status == "ACTIVE").all()
    personas = []
    
    for emp in employees:
        flag = FLAG_MAP.get(emp.location_id, emp.location_id)
        country = emp.location.country if emp.location else emp.location_id
        personas.append(
            PersonaResponse(
                employee_id=emp.employee_id,
                name=emp.name,
                email=emp.email,
                location_id=emp.location_id,
                country=country,
                flag=flag,
                role=emp.role,
                department=emp.department,
                designation=emp.designation,
                grade=emp.grade,
            )
        )

    return personas
