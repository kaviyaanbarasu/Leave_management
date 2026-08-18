from app.routers.employees import router as employees_router
from app.routers.locations import router as locations_router
from app.routers.leave_types import router as leave_types_router
from app.routers.holidays import router as holidays_router
from app.routers.accrual_policies import router as accrual_policies_router
from app.routers.leave_requests import router as leave_requests_router

__all__ = [
    "employees_router",
    "locations_router",
    "leave_types_router",
    "holidays_router",
    "accrual_policies_router",
    "leave_requests_router",
]
