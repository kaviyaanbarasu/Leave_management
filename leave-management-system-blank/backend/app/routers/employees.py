from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.employee import Employee
from app.models.location import Location
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from app.schemas.leave_request import EmployeeBalanceResponse, BalanceAdjustmentRequest
from app.services.balance_service import balance_service

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    # Verify unique employee_id
    existing_id = db.query(Employee).filter(Employee.employee_id == payload.employee_id).first()
    if existing_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Employee with ID '{payload.employee_id}' already exists",
        )

    # Verify unique email
    existing_email = db.query(Employee).filter(Employee.email == payload.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Employee with email '{payload.email}' already exists",
        )

    # Verify location exists
    location = db.query(Location).filter(Location.location_id == payload.location_id).first()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location '{payload.location_id}' not found",
        )

    employee = Employee(
        employee_id=payload.employee_id,
        name=payload.name,
        email=payload.email,
        department=payload.department,
        designation=payload.designation,
        grade=payload.grade,
        location_id=payload.location_id,
        joining_date=payload.joining_date,
        status=payload.status,
        role=payload.role or "EMPLOYEE",
        password=payload.password or "password123",
        manager_id=payload.manager_id,
    )
    db.add(employee)
    db.flush()

    # Automatically initialize balances for all active leave types in employee's location
    balance_service.initialize_employee_balances(employee.employee_id, employee.location_id, db)

    db.commit()
    db.refresh(employee)
    return employee


@router.get("", response_model=List[EmployeeResponse])
def list_employees(db: Session = Depends(get_db)):
    return db.query(Employee).order_by(Employee.employee_id).all()


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(employee_id: str, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee '{employee_id}' not found",
        )
    return employee


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(employee_id: str, payload: EmployeeUpdate, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee '{employee_id}' not found",
        )

    if payload.email and payload.email != employee.email:
        existing_email = db.query(Employee).filter(Employee.email == payload.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Employee with email '{payload.email}' already exists",
            )
        employee.email = payload.email

    if payload.location_id:
        location = db.query(Location).filter(Location.location_id == payload.location_id).first()
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Location '{payload.location_id}' not found",
            )
        employee.location_id = payload.location_id
        # Also ensure balances for new location leave types are initialized
        balance_service.initialize_employee_balances(employee.employee_id, payload.location_id, db)

    if payload.name is not None:
        employee.name = payload.name
    if payload.department is not None:
        employee.department = payload.department
    if payload.designation is not None:
        employee.designation = payload.designation
    if payload.grade is not None:
        employee.grade = payload.grade
    if payload.joining_date is not None:
        employee.joining_date = payload.joining_date
    if payload.status is not None:
        employee.status = payload.status
    if payload.role is not None:
        employee.role = payload.role
    if payload.password is not None:
        employee.password = payload.password
    if payload.manager_id is not None:
        employee.manager_id = payload.manager_id

    db.commit()
    db.refresh(employee)
    return employee


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(employee_id: str, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee '{employee_id}' not found",
        )
    db.delete(employee)
    db.commit()
    return None


@router.get("/{employee_id}/balance", response_model=EmployeeBalanceResponse)
def get_employee_balance(employee_id: str, db: Session = Depends(get_db)):
    try:
        return balance_service.get_employee_balances(employee_id, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/{employee_id}/adjust-balance", response_model=EmployeeBalanceResponse)
def adjust_employee_balance(employee_id: str, payload: BalanceAdjustmentRequest, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee '{employee_id}' not found",
        )

    balance_service.adjust_balance(
        employee_id=employee_id,
        leave_type_id=payload.leave_type_id,
        adjustment_days=payload.adjustment_days,
        db=db,
    )
    db.commit()
    return balance_service.get_employee_balances(employee_id, db)
