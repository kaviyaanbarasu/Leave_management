from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.employee import Employee
from app.models.leave_type import LeaveType
from app.models.leave_request import EmployeeLeaveBalance
from app.schemas.leave_request import EmployeeBalanceResponse, BalanceItemResponse


class BalanceService:
    """Provide methods to manage and query employee leave balances."""
    def get_or_create_balance(
        self, employee_id: str, leave_type_id: str, db: Session, initial_opening: float = 0.0
    ) -> EmployeeLeaveBalance:
        """Retrieve an existing employee leave balance or create a new one if none exists.

        Args:
        employee_id (str): Identifier of the employee.
        leave_type_id (str): Identifier of the leave type.
        db (Session): SQLAlchemy session used for database operations.
        initial_opening (float, optional): Opening balance to set when creating a new record. Defaults to 0.0.

        Returns:
        EmployeeLeaveBalance: The existing or newly created balance record.
        """
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
        """Retrieve the leave balances for all active leave types applicable to an employee's location.

        Args:
        employee_id (str): Identifier of the employee.
        db (Session): SQLAlchemy session for database queries.

        Returns:
        EmployeeBalanceResponse: Response object containing employee details and a list of balance items.

        Raises:
        ValueError: If the employee with the given ID does not exist.
        """
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
        """Return the available leave balance for a specific employee and leave type.

        Args:
        employee_id (str): Identifier of the employee.
        leave_type_id (str): Identifier of the leave type.
        db (Session): SQLAlchemy session.

        Returns:
        float: The available balance amount.
        """
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

    def initialize_employee_balances(self, employee_id: str, location_id: str, db: Session, default_opening: float = 10.0):
        """
        Initializes leave balance records for a newly created employee for all leave types in that location.
        """
        leave_types = (
            db.query(LeaveType)
            .filter(
                LeaveType.location_id == location_id,
                LeaveType.is_active == True,
            )
            .all()
        )
        for lt in leave_types:
            self.get_or_create_balance(employee_id, lt.leave_type_id, db, initial_opening=default_opening)
        db.flush()

    def approve_reservation(self, employee_id: str, leave_type_id: str, working_days: float, db: Session):
        """
        Deducts from pending and adds to used when a leave request is approved.
        """
        balance = self.get_or_create_balance(employee_id, leave_type_id, db)
        balance.pending = max(0.0, round(balance.pending - working_days, 2))
        balance.used = round(balance.used + working_days, 2)
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

    def release_balance(self, employee_id: str, leave_type_id: str, working_days: float, db: Session):
        """Release a previously reserved amount of leave balance for an employee.

        Args:
        employee_id (str): Identifier of the employee.
        leave_type_id (str): Identifier of the leave type.
        working_days (float): Number of days to release from the reservation.
        db (Session): SQLAlchemy session.

        Returns:
        Any: The result of the underlying release_reservation operation.
        """
        return self.release_reservation(employee_id, leave_type_id, working_days, db)

    def deduct_balance(self, employee_id: str, leave_type_id: str, working_days: float, db: Session):
        """Deduct (approve) a reserved amount of leave balance for an employee.

        Args:
        employee_id (str): Identifier of the employee.
        leave_type_id (str): Identifier of the leave type.
        working_days (float): Number of days to deduct from the reservation.
        db (Session): SQLAlchemy session.

        Returns:
        Any: The result of the underlying approve_reservation operation.
        """
        return self.approve_reservation(employee_id, leave_type_id, working_days, db)

    def adjust_balance(self, employee_id: str, leave_type_id: str, adjustment_days: float, db: Session) -> EmployeeLeaveBalance:
        """
        Manually adjusts employee leave balance.
        """
        balance = self.get_or_create_balance(employee_id, leave_type_id, db)
        balance.adjusted = round(balance.adjusted + adjustment_days, 2)
        balance.as_of_date = date.today()
        db.flush()
        return balance


balance_service = BalanceService()
