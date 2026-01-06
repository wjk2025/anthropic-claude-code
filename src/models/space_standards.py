"""Space standards definitions for office programming."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class SpaceType(str, Enum):
    """Types of office spaces."""

    # Individual workspaces
    PRIVATE_OFFICE_LARGE = "private_office_large"
    PRIVATE_OFFICE_MEDIUM = "private_office_medium"
    PRIVATE_OFFICE_SMALL = "private_office_small"
    WORKSTATION_LARGE = "workstation_large"
    WORKSTATION_STANDARD = "workstation_standard"
    WORKSTATION_COMPACT = "workstation_compact"
    HOTELING_STATION = "hoteling_station"

    # Meeting spaces
    CONFERENCE_LARGE = "conference_large"
    CONFERENCE_MEDIUM = "conference_medium"
    CONFERENCE_SMALL = "conference_small"
    HUDDLE_ROOM = "huddle_room"
    PHONE_BOOTH = "phone_booth"

    # Support spaces
    RECEPTION = "reception"
    WAITING_AREA = "waiting_area"
    BREAK_ROOM = "break_room"
    KITCHEN = "kitchen"
    COPY_PRINT_AREA = "copy_print_area"
    MAIL_ROOM = "mail_room"
    STORAGE = "storage"
    SERVER_ROOM = "server_room"
    WELLNESS_ROOM = "wellness_room"

    # Specialty spaces
    TRAINING_ROOM = "training_room"
    LIBRARY = "library"
    FOCUS_ROOM = "focus_room"
    COLLABORATION_AREA = "collaboration_area"


class SpaceStandard(BaseModel):
    """Definition of a space type and its standard size."""

    space_type: SpaceType
    name: str = Field(description="Display name for the space type")
    square_feet: float = Field(gt=0, description="Standard square footage")
    description: str = Field(default="", description="Description of the space")
    capacity: Optional[int] = Field(default=None, description="Number of people the space can accommodate")
    is_shared: bool = Field(default=False, description="Whether this is a shared space")
    typical_ratio: Optional[str] = Field(
        default=None,
        description="Typical ratio (e.g., '1 per 20 employees')"
    )

    class Config:
        use_enum_values = True


# Industry standard space sizes (based on BOMA and industry best practices)
DEFAULT_SPACE_STANDARDS: dict[SpaceType, SpaceStandard] = {
    # Private offices
    SpaceType.PRIVATE_OFFICE_LARGE: SpaceStandard(
        space_type=SpaceType.PRIVATE_OFFICE_LARGE,
        name="Large Private Office",
        square_feet=225,
        description="Executive or senior management office",
        capacity=1,
        is_shared=False
    ),
    SpaceType.PRIVATE_OFFICE_MEDIUM: SpaceStandard(
        space_type=SpaceType.PRIVATE_OFFICE_MEDIUM,
        name="Medium Private Office",
        square_feet=150,
        description="Manager or senior professional office",
        capacity=1,
        is_shared=False
    ),
    SpaceType.PRIVATE_OFFICE_SMALL: SpaceStandard(
        space_type=SpaceType.PRIVATE_OFFICE_SMALL,
        name="Small Private Office",
        square_feet=100,
        description="Standard private office",
        capacity=1,
        is_shared=False
    ),

    # Workstations
    SpaceType.WORKSTATION_LARGE: SpaceStandard(
        space_type=SpaceType.WORKSTATION_LARGE,
        name="Large Workstation",
        square_feet=80,
        description="Large open workstation (8x10)",
        capacity=1,
        is_shared=False
    ),
    SpaceType.WORKSTATION_STANDARD: SpaceStandard(
        space_type=SpaceType.WORKSTATION_STANDARD,
        name="Standard Workstation",
        square_feet=64,
        description="Standard open workstation (8x8)",
        capacity=1,
        is_shared=False
    ),
    SpaceType.WORKSTATION_COMPACT: SpaceStandard(
        space_type=SpaceType.WORKSTATION_COMPACT,
        name="Compact Workstation",
        square_feet=48,
        description="Compact benching workstation (6x8)",
        capacity=1,
        is_shared=False
    ),
    SpaceType.HOTELING_STATION: SpaceStandard(
        space_type=SpaceType.HOTELING_STATION,
        name="Hoteling Station",
        square_feet=42,
        description="Shared/hoteling workstation",
        capacity=1,
        is_shared=True,
        typical_ratio="1 per 3 remote workers"
    ),

    # Meeting spaces
    SpaceType.CONFERENCE_LARGE: SpaceStandard(
        space_type=SpaceType.CONFERENCE_LARGE,
        name="Large Conference Room",
        square_feet=600,
        description="Board room / large meeting room (16-20 people)",
        capacity=20,
        is_shared=True,
        typical_ratio="1 per 100 employees"
    ),
    SpaceType.CONFERENCE_MEDIUM: SpaceStandard(
        space_type=SpaceType.CONFERENCE_MEDIUM,
        name="Medium Conference Room",
        square_feet=300,
        description="Standard conference room (10-12 people)",
        capacity=12,
        is_shared=True,
        typical_ratio="1 per 40 employees"
    ),
    SpaceType.CONFERENCE_SMALL: SpaceStandard(
        space_type=SpaceType.CONFERENCE_SMALL,
        name="Small Conference Room",
        square_feet=150,
        description="Small meeting room (6-8 people)",
        capacity=8,
        is_shared=True,
        typical_ratio="1 per 25 employees"
    ),
    SpaceType.HUDDLE_ROOM: SpaceStandard(
        space_type=SpaceType.HUDDLE_ROOM,
        name="Huddle Room",
        square_feet=80,
        description="Quick meeting space (3-4 people)",
        capacity=4,
        is_shared=True,
        typical_ratio="1 per 15 employees"
    ),
    SpaceType.PHONE_BOOTH: SpaceStandard(
        space_type=SpaceType.PHONE_BOOTH,
        name="Phone Booth",
        square_feet=35,
        description="Private phone/video call booth",
        capacity=1,
        is_shared=True,
        typical_ratio="1 per 10 employees"
    ),

    # Support spaces
    SpaceType.RECEPTION: SpaceStandard(
        space_type=SpaceType.RECEPTION,
        name="Reception",
        square_feet=150,
        description="Reception desk area",
        capacity=2,
        is_shared=True
    ),
    SpaceType.WAITING_AREA: SpaceStandard(
        space_type=SpaceType.WAITING_AREA,
        name="Waiting Area",
        square_feet=200,
        description="Guest waiting/lobby area",
        capacity=8,
        is_shared=True
    ),
    SpaceType.BREAK_ROOM: SpaceStandard(
        space_type=SpaceType.BREAK_ROOM,
        name="Break Room",
        square_feet=300,
        description="Employee break/lunch room",
        is_shared=True,
        typical_ratio="15 SF per employee (min 200 SF)"
    ),
    SpaceType.KITCHEN: SpaceStandard(
        space_type=SpaceType.KITCHEN,
        name="Kitchen/Pantry",
        square_feet=200,
        description="Kitchen/pantry area",
        is_shared=True,
        typical_ratio="1 per floor"
    ),
    SpaceType.COPY_PRINT_AREA: SpaceStandard(
        space_type=SpaceType.COPY_PRINT_AREA,
        name="Copy/Print Area",
        square_feet=100,
        description="Copy center and printing area",
        is_shared=True,
        typical_ratio="1 per 30 employees"
    ),
    SpaceType.MAIL_ROOM: SpaceStandard(
        space_type=SpaceType.MAIL_ROOM,
        name="Mail Room",
        square_feet=120,
        description="Mail and package handling",
        is_shared=True
    ),
    SpaceType.STORAGE: SpaceStandard(
        space_type=SpaceType.STORAGE,
        name="Storage",
        square_feet=150,
        description="General storage area",
        is_shared=True,
        typical_ratio="5-10 SF per employee"
    ),
    SpaceType.SERVER_ROOM: SpaceStandard(
        space_type=SpaceType.SERVER_ROOM,
        name="Server/IT Room",
        square_feet=150,
        description="IT infrastructure and servers",
        is_shared=True
    ),
    SpaceType.WELLNESS_ROOM: SpaceStandard(
        space_type=SpaceType.WELLNESS_ROOM,
        name="Wellness/Mother's Room",
        square_feet=80,
        description="Private wellness or lactation room",
        capacity=1,
        is_shared=True,
        typical_ratio="1 per 50 employees"
    ),

    # Specialty spaces
    SpaceType.TRAINING_ROOM: SpaceStandard(
        space_type=SpaceType.TRAINING_ROOM,
        name="Training Room",
        square_feet=500,
        description="Training and presentation room",
        capacity=25,
        is_shared=True,
        typical_ratio="1 per 150 employees"
    ),
    SpaceType.LIBRARY: SpaceStandard(
        space_type=SpaceType.LIBRARY,
        name="Library/Resource Room",
        square_feet=200,
        description="Quiet reference and resource area",
        capacity=6,
        is_shared=True
    ),
    SpaceType.FOCUS_ROOM: SpaceStandard(
        space_type=SpaceType.FOCUS_ROOM,
        name="Focus Room",
        square_feet=60,
        description="Quiet individual focus space",
        capacity=1,
        is_shared=True,
        typical_ratio="1 per 20 employees"
    ),
    SpaceType.COLLABORATION_AREA: SpaceStandard(
        space_type=SpaceType.COLLABORATION_AREA,
        name="Collaboration Area",
        square_feet=250,
        description="Open collaboration/lounge space",
        capacity=10,
        is_shared=True,
        typical_ratio="10-15 SF per employee"
    ),
}


def get_standard(space_type: SpaceType) -> SpaceStandard:
    """Get the default standard for a space type."""
    return DEFAULT_SPACE_STANDARDS[space_type]


def get_all_workspace_types() -> list[SpaceType]:
    """Get all individual workspace types."""
    return [
        SpaceType.PRIVATE_OFFICE_LARGE,
        SpaceType.PRIVATE_OFFICE_MEDIUM,
        SpaceType.PRIVATE_OFFICE_SMALL,
        SpaceType.WORKSTATION_LARGE,
        SpaceType.WORKSTATION_STANDARD,
        SpaceType.WORKSTATION_COMPACT,
        SpaceType.HOTELING_STATION,
    ]


def get_all_meeting_types() -> list[SpaceType]:
    """Get all meeting space types."""
    return [
        SpaceType.CONFERENCE_LARGE,
        SpaceType.CONFERENCE_MEDIUM,
        SpaceType.CONFERENCE_SMALL,
        SpaceType.HUDDLE_ROOM,
        SpaceType.PHONE_BOOTH,
    ]


def get_all_support_types() -> list[SpaceType]:
    """Get all support space types."""
    return [
        SpaceType.RECEPTION,
        SpaceType.WAITING_AREA,
        SpaceType.BREAK_ROOM,
        SpaceType.KITCHEN,
        SpaceType.COPY_PRINT_AREA,
        SpaceType.MAIL_ROOM,
        SpaceType.STORAGE,
        SpaceType.SERVER_ROOM,
        SpaceType.WELLNESS_ROOM,
    ]
