from datetime import date, datetime, timezone
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from app.models.employee import Employee
from app.models.leave_type import LeaveType
from app.models.accrual_policy import AccrualPolicy, AccrualRecord
from app.models.leave_request import EmployeeLeaveBalance
from app.services.balance_service import balance_service
from app.schemas.accrual_policy import AccrualRunResponse, AccrualRunItem


class AccrualService:
    def calculate_tenure_months(self, joining_date: date, as_of_date: date) -> int:
        """Calculates completed tenure in months from joining date to as_of_date."""
        if as_of_date < joining_date:
            return 0
        years = as_of_date.year - joining_date.year
        months = as_of_date.month - joining_date.month
        if as_of_date.day < joining_date.day:
            months -= 1
        total_months = years * 12 + months
        return max(0, total_months)

    def find_applicable_policy(
        self, employee: Employee, leave_type_id: str, as_of_date: date, db: Session
    ) -> Optional[AccrualPolicy]:
        """
        Finds the best matching active AccrualPolicy for an employee:
        1. Must match location_id and leave_type_id.
        2. Must match grade (or generic grade=None).
        3. Employee tenure >= policy.tenure_from_months.
        Ranking: Grade match + highest tenure_from_months.
        """
        tenure_months = self.calculate_tenure_months(employee.joining_date, as_of_date)

        policies = (
            db.query(AccrualPolicy)
            .filter(
                AccrualPolicy.location_id == employee.location_id,
                AccrualPolicy.leave_type_id == leave_type_id,
                AccrualPolicy.is_active == True,
                AccrualPolicy.tenure_from_months <= tenure_months,
            )
            .all()
        )

        if not policies:
            return None

        # Filter and rank:
        # Match grade if possible; otherwise match fallback where grade is None or ""
        exact_grade_policies = [p for p in policies if p.grade and p.grade.upper() == (employee.grade or "").upper()]
        if exact_grade_policies:
            exact_grade_policies.sort(key=lambda p: p.tenure_from_months, reverse=True)
            return exact_grade_policies[0]

        generic_policies = [p for p in policies if not p.grade]
        if generic_policies:
            generic_policies.sort(key=lambda p: p.tenure_from_months, reverse=True)
            return generic_policies[0]

        return None

    def calculate_accrual(
        self, employee: Employee, leave_type: LeaveType, as_of_date: date, db: Session
    ) -> Tuple[Optional[AccrualPolicy], float]:
        """Calculates accrual amount for an employee and leave type."""
        if not leave_type.is_accruable or not leave_type.is_active:
            return None, 0.0

        policy = self.find_applicable_policy(employee, leave_type.leave_type_id, as_of_date, db)
        if not policy:
            return None, 0.0

        return policy, policy.monthly_accrual

    def run_monthly_accrual(
        self, year: Optional[int], month: Optional[int], db: Session
    ) -> AccrualRunResponse:
        """
        Executes monthly accrual across all active employees.
        Idempotent: Uses AccrualRecord table to prevent multiple accruals for the same month.
        Respects max_balance cap and provides explainable diagnostics.
        """
        now = datetime.now(timezone.utc)
        target_year = year if year is not None else now.year
        target_month = month if month is not None else now.month
        as_of_date = date(target_year, target_month, 28)

        active_employees = db.query(Employee).filter(Employee.status == "ACTIVE").all()
        run_items: List[AccrualRunItem] = []
        total_accrued_count = 0

        for emp in active_employees:
            # Get accruable leave types for employee location
            leave_types = (
                db.query(LeaveType)
                .filter(
                    LeaveType.location_id == emp.location_id,
                    LeaveType.is_active == True,
                    LeaveType.is_accruable == True,
                )
                .all()
            )

            for lt in leave_types:
                # 1. Check idempotency: already accrued this month?
                existing_record = (
                    db.query(AccrualRecord)
                    .filter(
                        AccrualRecord.employee_id == emp.employee_id,
                        AccrualRecord.leave_type_id == lt.leave_type_id,
                        AccrualRecord.year == target_year,
                        AccrualRecord.month == target_month,
                    )
                    .first()
                )

                bal = balance_service.get_or_create_balance(emp.employee_id, lt.leave_type_id, db)
                prev_available = bal.available_balance

                # Find policy (even for skipped/capped records so we can report policy details)
                policy = self.find_applicable_policy(emp, lt.leave_type_id, as_of_date, db)
                policy_name = f"{policy.grade or 'All Grades'} {lt.name} Policy" if policy else "No Policy"

                if existing_record:
                    run_items.append(
                        AccrualRunItem(
                            employee_id=emp.employee_id,
                            employee_name=emp.name,
                            leave_type_id=lt.leave_type_id,
                            leave_type_name=lt.name,
                            grade=emp.grade,
                            policy_id=existing_record.policy_id or (policy.policy_id if policy else None),
                            policy_name=policy_name,
                            policy_grade=policy.grade if policy else None,
                            monthly_accrual=policy.monthly_accrual if policy else 0.0,
                            max_balance=policy.max_balance if policy else 0.0,
                            current_balance=prev_available,
                            actual_accrual=0.0,
                            accrued_amount=0.0,
                            previous_balance=prev_available,
                            new_balance=prev_available,
                            status="SKIPPED_ALREADY_ACCRUED",
                            reason=f"Monthly entitlement for {target_month:02d}/{target_year} was already accrued on {existing_record.accrued_at.strftime('%Y-%m-%d')}.",
                        )
                    )
                    continue

                if not policy:
                    run_items.append(
                        AccrualRunItem(
                            employee_id=emp.employee_id,
                            employee_name=emp.name,
                            leave_type_id=lt.leave_type_id,
                            leave_type_name=lt.name,
                            grade=emp.grade,
                            policy_id=None,
                            policy_name="No Active Policy",
                            policy_grade=None,
                            monthly_accrual=0.0,
                            max_balance=0.0,
                            current_balance=prev_available,
                            actual_accrual=0.0,
                            accrued_amount=0.0,
                            previous_balance=prev_available,
                            new_balance=prev_available,
                            status="NO_POLICY",
                            reason=f"No matching accrual policy found for location {emp.location_id}, grade {emp.grade}.",
                        )
                    )
                    continue

                # 3. Calculate capped accrual
                current_total = bal.opening_balance + bal.accrued + bal.adjusted - bal.used
                if current_total >= policy.max_balance:
                    actual_accrual = 0.0
                    status = "CAPPED_AT_MAX"
                    reason = f"Current balance ({current_total:.2f} days) has reached the maximum policy cap ({policy.max_balance:.2f} days)."
                else:
                    room = policy.max_balance - current_total
                    actual_accrual = round(min(policy.monthly_accrual, room), 2)
                    status = "ACCRUED"
                    if actual_accrual < policy.monthly_accrual:
                        reason = f"Accrued {actual_accrual:.2f} days (partially capped to meet maximum balance {policy.max_balance:.2f} days)."
                    else:
                        reason = f"Accrued {actual_accrual:.2f} days as per {policy_name} ({policy.monthly_accrual:.2f} days/month)."

                # 4. Apply accrual to balance
                bal.accrued = round(bal.accrued + actual_accrual, 2)
                bal.as_of_date = as_of_date

                # 5. Record accrual transaction for idempotency & audit
                accrual_record = AccrualRecord(
                    employee_id=emp.employee_id,
                    leave_type_id=lt.leave_type_id,
                    policy_id=policy.policy_id,
                    year=target_year,
                    month=target_month,
                    accrued_amount=actual_accrual,
                    accrued_at=now,
                )
                db.add(accrual_record)
                db.flush()

                new_available = bal.available_balance
                if actual_accrual > 0:
                    total_accrued_count += 1

                run_items.append(
                    AccrualRunItem(
                        employee_id=emp.employee_id,
                        employee_name=emp.name,
                        leave_type_id=lt.leave_type_id,
                        leave_type_name=lt.name,
                        grade=emp.grade,
                        policy_id=policy.policy_id,
                        policy_name=policy_name,
                        policy_grade=policy.grade,
                        monthly_accrual=policy.monthly_accrual,
                        max_balance=policy.max_balance,
                        current_balance=prev_available,
                        actual_accrual=actual_accrual,
                        accrued_amount=actual_accrual,
                        previous_balance=prev_available,
                        new_balance=new_available,
                        status=status,
                        reason=reason,
                    )
                )

        db.commit()

        return AccrualRunResponse(
            year=target_year,
            month=target_month,
            total_processed=len(run_items),
            total_accrued=total_accrued_count,
            details=run_items,
        )


accrual_service = AccrualService()
