from datetime import date, timedelta
from typing import List, Tuple, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.employee import Employee
from app.models.location import Location
from app.models.holiday import Holiday


class HolidayProvider:
    """Base Holiday Provider Interface"""
    def get_holidays(self, location_id: str, year: int, db: Session) -> List[Holiday]:
        raise NotImplementedError


class DatabaseHolidayProvider(HolidayProvider):
    """Database-backed Holiday Provider"""
    def get_holidays(self, location_id: str, year: int, db: Session) -> List[Holiday]:
        start_of_year = date(year, 1, 1)
        end_of_year = date(year, 12, 31)
        return (
            db.query(Holiday)
            .filter(
                Holiday.location_id == location_id,
                Holiday.date >= start_of_year,
                Holiday.date <= end_of_year
            )
            .order_by(Holiday.date)
            .all()
        )


class HolidayService:
    def __init__(self, provider: Optional[HolidayProvider] = None):
        self.provider = provider or DatabaseHolidayProvider()

    def is_holiday(self, location_id: str, check_date: date, db: Session) -> bool:
        """Checks if a specific date is a holiday for the given location."""
        holiday = (
            db.query(Holiday)
            .filter(Holiday.location_id == location_id, Holiday.date == check_date)
            .first()
        )
        return holiday is not None

    def get_holiday_details(self, location_id: str, check_date: date, db: Session) -> Optional[Holiday]:
        return (
            db.query(Holiday)
            .filter(Holiday.location_id == location_id, Holiday.date == check_date)
            .first()
        )

    def is_weekend(self, location: Location, check_date: date) -> bool:
        """
        Determines if the given date falls on a weekend for the specified location.
        Uses the location's configured weekend_days (list of integers 0=Monday..6=Sunday).
        Default fallback: Saturday (5) and Sunday (6).
        """
        weekend_days = location.weekend_days if location and location.weekend_days is not None else [5, 6]
        return check_date.weekday() in weekend_days

    def is_working_day(self, employee: Employee, check_date: date, db: Session) -> bool:
        """
        Determines if the date is a working day for the given employee.
        Returns False if it is a configured weekend or a location-specific holiday.
        """
        if not employee.location:
            location = db.query(Location).filter(Location.location_id == employee.location_id).first()
        else:
            location = employee.location

        if self.is_weekend(location, check_date):
            return False

        if self.is_holiday(employee.location_id, check_date, db):
            return False

        return True

    def calculate_working_days(
        self, employee_id: str, start_date: date, end_date: date, db: Session
    ) -> Tuple[int, float, List[Dict[str, Any]]]:
        """
        Calculates working days for an employee across a date range.
        Returns:
            (total_calendar_days, working_days, day_breakdown)
        """
        employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
        if not employee:
            raise ValueError(f"Employee {employee_id} not found")

        location = db.query(Location).filter(Location.location_id == employee.location_id).first()
        if not location:
            raise ValueError(f"Location {employee.location_id} not found")

        total_calendar_days = (end_date - start_date).days + 1
        if total_calendar_days <= 0:
            raise ValueError("Start date must be before or equal to end date")

        # Fetch all holidays for this location in the date range in one query
        holidays_in_range = {
            h.date: h.name
            for h in db.query(Holiday)
            .filter(
                Holiday.location_id == location.location_id,
                Holiday.date >= start_date,
                Holiday.date <= end_date,
            )
            .all()
        }

        weekend_days = set(location.weekend_days if location.weekend_days is not None else [5, 6])
        working_days = 0.0
        day_breakdown = []

        curr_date = start_date
        while curr_date <= end_date:
            is_wknd = curr_date.weekday() in weekend_days
            is_hol = curr_date in holidays_in_range
            is_work = not is_wknd and not is_hol

            if is_work:
                working_days += 1.0

            day_breakdown.append({
                "date": curr_date.isoformat(),
                "day_name": curr_date.strftime("%A"),
                "is_weekend": is_wknd,
                "is_holiday": is_hol,
                "holiday_name": holidays_in_range.get(curr_date),
                "is_working_day": is_work,
            })

            curr_date += timedelta(days=1)

        return total_calendar_days, working_days, day_breakdown


holiday_service = HolidayService()
