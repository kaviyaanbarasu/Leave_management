from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class LeaveTypeBase(BaseModel):
    """Define the base schema for a leave type.

    Args:
        name (str): Name of the leave type (minimum length 1).
        description (Optional[str]): Optional description.
        is_paid (bool): Indicates if the leave type is paid. Defaults to True.
        is_accruable (bool): Indicates if the leave type accrues. Defaults to True.
        is_active (bool): Indicates if the leave type is active. Defaults to True.
    """
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    is_paid: bool = Field(default=True)
    is_accruable: bool = Field(default=True)
    is_active: bool = Field(default=True)


class LeaveTypeCreate(LeaveTypeBase):
    """Define the schema for creating a new leave type.

    Args:
        name (str): Name of the leave type (minimum length 1).
        description (Optional[str]): Optional description.
        is_paid (bool): Indicates if the leave type is paid. Defaults to True.
        is_accruable (bool): Indicates if the leave type accrues. Defaults to True.
        is_active (bool): Indicates if the leave type is active. Defaults to True.
        leave_type_id (str): Identifier for the leave type (minimum length 1).
        location_id (str): Identifier for the location (minimum length 1).
    """
    leave_type_id: str = Field(..., min_length=1)
    location_id: str = Field(..., min_length=1)


class LeaveTypeUpdate(BaseModel):
    """Define the schema for updating a leave type.

    Args:
        name (Optional[str]): Updated name.
        description (Optional[str]): Updated description.
        is_paid (Optional[bool]): Updated paid flag.
        is_accruable (Optional[bool]): Updated accruable flag.
        is_active (Optional[bool]): Updated active flag.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    is_paid: Optional[bool] = None
    is_accruable: Optional[bool] = None
    is_active: Optional[bool] = None


class LeaveTypeResponse(LeaveTypeBase):
    """Define the schema for returning a leave type.

    Args:
        name (str): Name of the leave type.
        description (Optional[str]): Optional description.
        is_paid (bool): Indicates if the leave type is paid.
        is_accruable (bool): Indicates if the leave type accrues.
        is_active (bool): Indicates if the leave type is active.
        leave_type_id (str): Identifier for the leave type.
        location_id (str): Identifier for the location.

    Attributes:
        model_config (ConfigDict): Configuration enabling attribute population from ORM objects.
    """
    leave_type_id: str
    location_id: str

    model_config = ConfigDict(from_attributes=True)
