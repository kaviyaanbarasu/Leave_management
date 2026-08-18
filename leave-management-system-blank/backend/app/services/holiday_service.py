import os
import urllib.parse
import httpx
from datetime import date, timedelta, datetime, timezone
from typing import List, Tuple, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.models.employee import Employee
from app.models.location import Location
from app.models.holiday import Holiday, HolidaySync


GOOGLE_CALENDAR_MAP = {
    "BLR": "en.indian.official#holiday@group.v.calendar.google.com",
    "INDIA": "en.indian.official#holiday@group.v.calendar.google.com",
    "SG": "en.singapore.official#holiday@group.v.calendar.google.com",
    "SINGAPORE": "en.singapore.official#holiday@group.v.calendar.google.com",
    "NY": "en.usa.official#holiday@group.v.calendar.google.com",
    "USA": "en.usa.official#holiday@group.v.calendar.google.com",
    "UNITED STATES": "en.usa.official#holiday@group.v.calendar.google.com",
    "DXB": "en.ae.official#holiday@group.v.calendar.google.com",
    "DUBAI": "en.ae.official#holiday@group.v.calendar.google.com",
    "UAE": "en.ae.official#holiday@group.v.calendar.google.com",
    "LON": "en.uk#holiday@group.v.calendar.google.com",
    "UK": "en.uk#holiday@group.v.calendar.google.com",
    "UNITED KINGDOM": "en.uk#holiday@group.v.calendar.google.com",
}

GOOGLE_CALENDAR_FALLBACK_MAP = {
    "BLR": "en.indian#holiday@group.v.calendar.google.com",
    "INDIA": "en.indian#holiday@group.v.calendar.google.com",
    "SG": "en.singapore#holiday@group.v.calendar.google.com",
    "SINGAPORE": "en.singapore#holiday@group.v.calendar.google.com",
    "NY": "en.usa#holiday@group.v.calendar.google.com",
    "USA": "en.usa#holiday@group.v.calendar.google.com",
    "UNITED STATES": "en.usa#holiday@group.v.calendar.google.com",
    "DXB": "en.ae#holiday@group.v.calendar.google.com",
    "DUBAI": "en.ae#holiday@group.v.calendar.google.com",
    "UAE": "en.ae#holiday@group.v.calendar.google.com",
}

GOOGLE_CALENDAR_NAMES = {
    "BLR": "India Public Holidays",
    "INDIA": "India Public Holidays",
    "SG": "Singapore Public Holidays",
    "SINGAPORE": "Singapore Public Holidays",
    "NY": "United States Public Holidays",
    "USA": "United States Public Holidays",
    "UNITED STATES": "United States Public Holidays",
    "DXB": "UAE Public Holidays",
    "DUBAI": "UAE Public Holidays",
    "UAE": "UAE Public Holidays",
    "LON": "UK Public Holidays",
}


class HolidayProvider:
    """Base Holiday Provider Interface"""
    def get_holidays(self, location_id: str, year: int, db: Session) -> List[Holiday]:
        raise NotImplementedError


class DatabaseHolidayProvider(HolidayProvider):
    """Database-backed Operational Holiday Provider"""
    def get_holidays(self, location_id: str, year: int, db: Session) -> List[Holiday]:
        start_of_year = date(year, 1, 1)
        end_of_year = date(year, 12, 31)
        return (
            db.query(Holiday)
            .filter(
                Holiday.location_id == location_id,
                Holiday.date >= start_of_year,
                Holiday.date <= end_of_year,
            )
            .order_by(Holiday.date)
            .all()
        )


class GoogleCalendarHolidayProvider:
    """Google Calendar API v3 Holiday Provider for Real-Time Public Holidays"""

    @staticmethod
    def get_calendar_id_for_location(location: Location, fallback: bool = False) -> str:
        mapping = GOOGLE_CALENDAR_FALLBACK_MAP if fallback else GOOGLE_CALENDAR_MAP
        loc_id = location.location_id.upper()
        if loc_id in mapping:
            return mapping[loc_id]

        country = location.country.upper()
        if country in mapping:
            return mapping[country]

        city = location.city.upper()
        if city in mapping:
            return mapping[city]

        # Generic default
        suffix = "official#holiday" if not fallback else "#holiday"
        return f"en.{location.country.lower()}.{suffix}@group.v.calendar.google.com"

    @staticmethod
    def get_calendar_name_for_location(location: Location) -> str:
        loc_id = location.location_id.upper()
        if loc_id in GOOGLE_CALENDAR_NAMES:
            return GOOGLE_CALENDAR_NAMES[loc_id]
        return f"{location.country} Public Holidays"

    @classmethod
    def fetch_holidays(
        cls, calendar_id: str, year: int, api_key: str
    ) -> List[Dict[str, Any]]:
        """
        Fetches official public holidays for the specified year from Google Calendar API v3.
        Supports full UTC year range (2026-01-01 through 2027-01-01 exclusive), singleEvents expansion,
        pagination (nextPageToken), and sanitizes holiday summaries.
        """
        encoded_cal = urllib.parse.quote(calendar_id, safe='')
        url = f"https://www.googleapis.com/calendar/v3/calendars/{encoded_cal}/events"
        
        time_min = f"{year}-01-01T00:00:00Z"
        time_max = f"{year + 1}-01-01T00:00:00Z"
        
        print(f"[GoogleCalendarAPI] Fetching events for calendar={calendar_id}, timeMin={time_min}, timeMax={time_max}, singleEvents=true")

        holidays = []
        page_token = None

        with httpx.Client(timeout=12.0) as client:
            while True:
                params = {
                    "key": api_key,
                    "timeMin": time_min,
                    "timeMax": time_max,
                    "singleEvents": "true",
                    "orderBy": "startTime",
                    "maxResults": 250,
                }
                if page_token:
                    params["pageToken"] = page_token

                res = client.get(url, params=params)
                if res.status_code != 200:
                    try:
                        error_detail = res.json().get("error", {}).get("message", res.text)
                    except Exception:
                        error_detail = res.text
                    print(f"[GoogleCalendarAPI Error] Status {res.status_code}: {error_detail}")
                    raise ValueError(f"Google Calendar API Error ({res.status_code}): {error_detail}")

                data = res.json()
                items = data.get("items", [])
                print(f"[GoogleCalendarAPI] Response: {len(items)} items received on current page. Summary: {data.get('summary')}")

                for item in items:
                    # Ignore cancelled events
                    if item.get("status") == "cancelled":
                        continue

                    start = item.get("start", {})
                    date_str = start.get("date") or (start.get("dateTime", "")[:10])
                    if not date_str:
                        continue
                    try:
                        event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    except ValueError:
                        continue

                    # Filter only events within the target year
                    if event_date.year != year:
                        continue

                    raw_summary = item.get("summary", "Public Holiday")
                    # Clean up encoding artifacts and unicode apostrophes/quotes
                    clean_summary = (
                        raw_summary.replace("\ufffd", "'")
                        .replace("\u2019", "'")
                        .replace("\u2018", "'")
                        .replace("\u201c", '"')
                        .replace("\u201d", '"')
                        .strip()
                    )

                    holidays.append({
                        "external_event_id": item.get("id"),
                        "name": clean_summary,
                        "date": event_date,
                        "type": "PUBLIC",
                        "description": item.get("description", "Official Google Public Holiday"),
                    })

                page_token = data.get("nextPageToken")
                if not page_token:
                    break

        print(f"[GoogleCalendarAPI] Total parsed holidays for {year}: {len(holidays)}")
        return holidays


class HolidayService:
    def __init__(self, provider: Optional[HolidayProvider] = None):
        self.provider = provider or DatabaseHolidayProvider()

    def get_sync_status(self, location_id: str, year: int, db: Session) -> Dict[str, Any]:
        """
        Retrieves the current synchronization metadata for a location and year.
        """
        location = db.query(Location).filter(Location.location_id == location_id).first()
        if not location:
            raise ValueError(f"Location '{location_id}' not found")

        calendar_id = GoogleCalendarHolidayProvider.get_calendar_id_for_location(location)
        calendar_name = GoogleCalendarHolidayProvider.get_calendar_name_for_location(location)
        # Check active API key in environment
        active_key = os.getenv("GOOGLE_CALENDAR_API_KEY") or settings.GOOGLE_CALENDAR_API_KEY
        has_key = bool(active_key and active_key.strip())

        sync_rec = (
            db.query(HolidaySync)
            .filter(HolidaySync.location_id == location_id, HolidaySync.year == year)
            .first()
        )

        holiday_count = (
            db.query(Holiday)
            .filter(
                Holiday.location_id == location_id,
                Holiday.date >= date(year, 1, 1),
                Holiday.date <= date(year, 12, 31),
            )
            .count()
        )

        if sync_rec:
            return {
                "location_id": location_id,
                "location_name": location.name,
                "year": year,
                "calendar_id": sync_rec.calendar_id,
                "calendar_name": calendar_name,
                "last_synced_at": sync_rec.last_synced_at,
                "sync_status": sync_rec.sync_status,
                "holiday_count": holiday_count,
                "has_api_key": has_key,
                "error_message": sync_rec.error_message,
            }

        return {
            "location_id": location_id,
            "location_name": location.name,
            "year": year,
            "calendar_id": calendar_id,
            "calendar_name": calendar_name,
            "last_synced_at": None,
            "sync_status": "NOT_SYNCED" if holiday_count == 0 else "USING_CACHED",
            "holiday_count": holiday_count,
            "has_api_key": has_key,
            "error_message": None,
        }

    def check_or_auto_sync(self, location_id: str, year: int, db: Session):
        """
        Automatically performs Google Holiday synchronization if never synced before and API key is present.
        If Google API is unreachable, logs status and gracefully allows PostgreSQL operational cache to be used.
        """
        active_key = os.getenv("GOOGLE_CALENDAR_API_KEY") or settings.GOOGLE_CALENDAR_API_KEY
        if not active_key:
            return

        sync_rec = (
            db.query(HolidaySync)
            .filter(HolidaySync.location_id == location_id, HolidaySync.year == year)
            .first()
        )

        if not sync_rec or sync_rec.sync_status not in ["SYNCED"]:
            try:
                self.sync_holidays_from_google(location_id, year, api_key=None, db=db, auto=True)
            except Exception as e:
                print(f"[HolidayService] Auto-sync notice for {location_id} ({year}): {e}")

    def sync_holidays_from_google(
        self,
        location_id: str,
        year: int,
        api_key: Optional[str],
        db: Session,
        auto: bool = False,
    ) -> Dict[str, Any]:
        """
        Synchronizes official public holidays for a location and year from Google Calendar API v3 into PostgreSQL.
        Guarantees:
        1. Never claims success if 0 events returned; marks SYNC_FAILED with actionable diagnosis.
        2. Preserves existing PostgreSQL cache on failed or 0-event sync.
        3. Never deletes manual holidays (source='MANUAL').
        4. Tries official calendar first, falls back to general public holiday calendar if needed.
        """
        location = db.query(Location).filter(Location.location_id == location_id).first()
        if not location:
            raise ValueError(f"Location '{location_id}' not found")

        active_key = api_key or os.getenv("GOOGLE_CALENDAR_API_KEY") or settings.GOOGLE_CALENDAR_API_KEY
        now = datetime.now(timezone.utc)

        # Existing count in PostgreSQL cache
        cached_count = (
            db.query(Holiday)
            .filter(
                Holiday.location_id == location_id,
                Holiday.date >= date(year, 1, 1),
                Holiday.date <= date(year, 12, 31),
            )
            .count()
        )

        calendar_id = GoogleCalendarHolidayProvider.get_calendar_id_for_location(location)
        calendar_name = GoogleCalendarHolidayProvider.get_calendar_name_for_location(location)

        # Retrieve or create sync record
        sync_rec = (
            db.query(HolidaySync)
            .filter(HolidaySync.location_id == location_id, HolidaySync.year == year)
            .first()
        )
        if not sync_rec:
            sync_rec = HolidaySync(
                location_id=location_id,
                year=year,
                calendar_id=calendar_id,
                sync_status="SYNCING",
                last_synced_at=now,
            )
            db.add(sync_rec)
            db.flush()

        if not active_key or not active_key.strip():
            sync_rec.sync_status = "USING_CACHED" if cached_count > 0 else "SYNC_FAILED"
            sync_rec.error_message = "Google Calendar API key is not configured in backend .env. Using cached PostgreSQL holidays."
            sync_rec.last_synced_at = now
            sync_rec.holiday_count = cached_count
            db.commit()

            if not auto and cached_count == 0:
                raise ValueError(
                    "Google Calendar API Key is missing. Please set GOOGLE_CALENDAR_API_KEY in backend/.env"
                )

            return {
                "status": "warning",
                "location_id": location_id,
                "location_name": location.name,
                "year": year,
                "calendar_id": calendar_id,
                "calendar_name": calendar_name,
                "synced_count": 0,
                "total_holidays": cached_count,
                "sync_status": sync_rec.sync_status,
                "message": sync_rec.error_message,
            }

        # Step 1: Call Google Calendar API (Primary official calendar)
        google_holidays = []
        try:
            google_holidays = GoogleCalendarHolidayProvider.fetch_holidays(calendar_id, year, active_key)
            if len(google_holidays) == 0:
                # Try fallback general calendar
                fallback_cal = GoogleCalendarHolidayProvider.get_calendar_id_for_location(location, fallback=True)
                if fallback_cal != calendar_id:
                    print(f"[HolidayService] Primary calendar returned 0 events; trying fallback calendar: {fallback_cal}")
                    google_holidays = GoogleCalendarHolidayProvider.fetch_holidays(fallback_cal, year, active_key)
                    if len(google_holidays) > 0:
                        calendar_id = fallback_cal
                        sync_rec.calendar_id = fallback_cal
        except Exception as ex:
            sync_rec.sync_status = "USING_CACHED" if cached_count > 0 else "SYNC_FAILED"
            sync_rec.error_message = f"Google Calendar API error: {str(ex)}. Using cached PostgreSQL holidays."
            sync_rec.last_synced_at = now
            sync_rec.holiday_count = cached_count
            db.commit()
            if not auto:
                raise ex
            return {
                "status": "warning",
                "location_id": location_id,
                "location_name": location.name,
                "year": year,
                "calendar_id": calendar_id,
                "calendar_name": calendar_name,
                "synced_count": 0,
                "total_holidays": cached_count,
                "sync_status": sync_rec.sync_status,
                "message": sync_rec.error_message,
            }

        # Step 2: Validate returned events count
        # DO NOT treat 0 events as success and DO NOT delete cached holidays on 0 events
        if len(google_holidays) == 0:
            sync_rec.sync_status = "SYNC_FAILED"
            sync_rec.error_message = f"Google Calendar returned 0 holiday events for {location.name} ({location.country}) in {year}. Preserving {cached_count} cached PostgreSQL holidays."
            sync_rec.last_synced_at = now
            sync_rec.holiday_count = cached_count
            db.commit()
            return {
                "status": "warning",
                "location_id": location_id,
                "location_name": location.name,
                "year": year,
                "calendar_id": calendar_id,
                "calendar_name": calendar_name,
                "synced_count": 0,
                "total_holidays": cached_count,
                "sync_status": "SYNC_FAILED",
                "message": sync_rec.error_message,
            }

        # Step 3: Valid events returned (>0) -> Safe Reconciliation & Ingestion
        incoming_event_ids = set()
        incoming_dates = set()
        synced_count = 0

        for g_hol in google_holidays:
            ext_id = g_hol.get("external_event_id")
            if ext_id:
                incoming_event_ids.add(ext_id)
            incoming_dates.add(g_hol["date"])

            # Match by external_event_id first, then by (location, date)
            existing = None
            if ext_id:
                existing = (
                    db.query(Holiday)
                    .filter(
                        Holiday.location_id == location.location_id,
                        Holiday.external_event_id == ext_id,
                    )
                    .first()
                )
            if not existing:
                existing = (
                    db.query(Holiday)
                    .filter(
                        Holiday.location_id == location.location_id,
                        Holiday.date == g_hol["date"],
                    )
                    .first()
                )

            if existing:
                existing.name = g_hol["name"]
                existing.description = g_hol["description"]
                existing.type = g_hol["type"]
                existing.source = "GOOGLE"
                if ext_id:
                    existing.external_event_id = ext_id
            else:
                new_h = Holiday(
                    location_id=location.location_id,
                    name=g_hol["name"],
                    date=g_hol["date"],
                    type=g_hol["type"],
                    description=g_hol["description"],
                    source="GOOGLE",
                    external_event_id=ext_id,
                )
                db.add(new_h)
            synced_count += 1

        # Clean up obsolete Google-sourced holidays that are no longer in Google's feed for this year
        # (Preserves all manual holidays with source == 'MANUAL')
        existing_google_holidays = (
            db.query(Holiday)
            .filter(
                Holiday.location_id == location.location_id,
                Holiday.source == "GOOGLE",
                Holiday.date >= date(year, 1, 1),
                Holiday.date <= date(year, 12, 31),
            )
            .all()
        )
        for old_gh in existing_google_holidays:
            if old_gh.external_event_id and old_gh.external_event_id not in incoming_event_ids:
                db.delete(old_gh)
            elif not old_gh.external_event_id and old_gh.date not in incoming_dates:
                db.delete(old_gh)

        db.flush()

        # Update sync metadata
        total_holidays = (
            db.query(Holiday)
            .filter(
                Holiday.location_id == location_id,
                Holiday.date >= date(year, 1, 1),
                Holiday.date <= date(year, 12, 31),
            )
            .count()
        )
        sync_rec.sync_status = "SYNCED"
        sync_rec.last_synced_at = now
        sync_rec.holiday_count = total_holidays
        sync_rec.error_message = None

        db.commit()

        return {
            "status": "success",
            "location_id": location_id,
            "location_name": location.name,
            "year": year,
            "calendar_id": calendar_id,
            "calendar_name": calendar_name,
            "synced_count": synced_count,
            "total_holidays": total_holidays,
            "sync_status": "SYNCED",
            "last_synced_at": now.isoformat(),
            "message": f"Successfully synced {synced_count} official holidays from Google Calendar into PostgreSQL.",
        }

    def is_holiday(self, location_id: str, check_date: date, db: Session) -> bool:
        """Checks if a specific date is a holiday for the given location using PostgreSQL cache."""
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
