from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.employee import Employee
from app.models.leave_type import LeaveType
from app.models.leave_request import EmployeeLeaveBalance
from app.schemas.leave_request import EmployeeBalanceResponse, BalanceItemResponse


class BalanceService:
    def get_or_create_balance(
        self, employee_id: str, leave_type_id: str, db: Session, initial_opening: float = 0.0
    ) -> EmployeeLeaveBalance:
        balance = (
            db.query(EmployeeLeaveBalance)
            .filter(
                EmployeeLeaveBalance.employee_id == employee_id,
                EmployeeLeaveBalance.leave_type_id == leave_type_id,
            )
            .first()
        )
        if not balance:
            balance = EmployeeLeaveBalance(
                employee_id=employee_id,
                leave_type_id=leave_type_id,
                opening_balance=initial_opening,
                accrued=0.0,
                used=0.0,
                pending=0.0,
                adjusted=0.0,
                as_of_date=date.today(),
            )
            db.add(balance)
            db.flush()
        return balance

    def get_employee_balances(self, employee_id: str, db: Session) -> EmployeeBalanceResponse:
        employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
        if not employee:
            raise ValueError(f"Employee {employee_id} not found")

        # Get all leave types available for the employee's location
        leave_types = (
            db.query(LeaveType)
            .filter(
                LeaveType.location_id == employee.location_id,
                LeaveType.is_active == True,
            )
            .all()
        )

        balance_items: List[BalanceItemResponse] = []
        for lt in leave_types:
            bal = (
                db.query(EmployeeLeaveBalance)
                .filter(
                    EmployeeLeaveBalance.employee_id == employee_id,
                    EmployeeLeaveBalance.leave_type_id == lt.leave_type_id,
                )
                .first()
            )
            if not bal:
                bal = self.get_or_create_balance(employee_id, lt.leave_type_id, db)

            available = bal.available_balance
            balance_items.append(
                BalanceItemResponse(
                    leave_type_id=lt.leave_type_id,
                    leave_type_name=lt.name,
                    opening_balance=bal.opening_balance,
                    accrued=bal.accrued,
                    used=bal.used,
                    pending=bal.pending,
                    adjusted=bal.adjusted,
                    available=available,
                )
            )

        return EmployeeBalanceResponse(
            employee_id=employee.employee_id,
            employee_name=employee.name,
            location_id=employee.location_id,
            balances=balance_items,
        )

    def get_available_balance(self, employee_id: str, leave_type_id: str, db: Session) -> float:
        balance = self.get_or_create_balance(employee_id, leave_type_id, db)
        return balance.available_balance

    def reserve_balance(self, employee_id: str, leave_type_id: str, working_days: float, db: Session):
        """
        Atomically reserve pending working days.
        Checks if available balance is sufficient.
        """
        balance = self.get_or_create_balance(employee_id, leave_type_id, db)
        available = balance.available_balance
        if available < working_days:
            raise ValueError(
                f"Insufficient balance. Available: {available:.1f} days, requested: {working_days:.1f} days."
            )

        balance.pending = round(balance.pending + working_days, 2)
        balance.as_of_date = date.today()
        db.flush()

    def release_reservation(self, employee_id: str, leave_type_id: str, working_days: float, db: Session):
        """
        Releases reserved pending balance when a request is cancelled or rejected.
        """
        balance = self.get_or_create_balance(employee_id, leave_type_id, db)
        balance.pending = max(0.0, round(balance.pending - working_days, 2))
        balance.as_of_date = date.today()
        db.flush()


balance_service = BalanceService()
