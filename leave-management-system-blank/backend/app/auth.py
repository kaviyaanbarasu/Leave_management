from fastapi import Depends, HTTPException, Header, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.employee import Employee


def extract_employee_id_from_token(token: str) -> Optional[str]:
    """
    Parses 'session-{employee_id}-{role}' or 'Bearer session-{employee_id}-{role}'
    or plain employee ID.
    """
    if not token:
        return None
    token = token.strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    if token.startswith("session-"):
        parts = token.split("-")
        if len(parts) >= 2:
            return parts[1]
    return token


def get_current_user(
    authorization: Optional[str] = Header(None),
    x_employee_id: Optional[str] = Header(None, alias="X-Employee-ID"),
    x_user_email: Optional[str] = Header(None, alias="X-User-Email"),
    employee_id: Optional[str] = Query(None, description="Optional employee ID query parameter"),
    db: Session = Depends(get_db),
) -> Optional[Employee]:
    """
    Identifies the authenticated employee from:
    1. Authorization Bearer header
    2. X-Employee-ID header
    3. X-User-Email header
    4. employee_id query parameter
    """
    candidate_id = None

    if authorization:
        candidate_id = extract_employee_id_from_token(authorization)
    elif x_employee_id:
        candidate_id = x_employee_id.strip()
    elif employee_id:
        candidate_id = employee_id.strip()

    if candidate_id:
        emp = (
            db.query(Employee)
            .filter(Employee.employee_id.ilike(candidate_id))
            .first()
        )
        if emp and emp.status == "ACTIVE":
            return emp

    if x_user_email:
        emp = (
            db.query(Employee)
            .filter(Employee.email.ilike(x_user_email.strip()))
            .first()
        )
        if emp and emp.status == "ACTIVE":
            return emp

    return None


def get_current_active_user(
    current_user: Optional[Employee] = Depends(get_current_user),
) -> Employee:
    """
    Enforces authentication. Raises 401 UNAUTHORIZED if no valid authenticated user is found.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in or provide valid credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user
