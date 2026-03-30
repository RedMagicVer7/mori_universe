"""
sealed_room.py - Sealed Room Model
====================================

Models the sealed room (密室) where Dr. Shiki Magata was confined
for 15 years in the Magata Research Facility.

The room is a "perfect" sealed environment:
- One-way entrance door (can only be opened from outside)
- 24/7 video surveillance
- Electromagnetic locks on all access points
- No windows, no other exits

The only way out: system overflow triggers failsafe → locks open.
"""

from enum import Enum, auto
from typing import List, Optional, Callable, Any
from dataclasses import dataclass, field

from .electromagnetic_lock import ElectromagneticLock, LockState


class RoomState(Enum):
    """States of the sealed room."""
    SEALED = auto()      # Room is fully sealed, no escape possible
    BREACHED = auto()    # Locks released, escape possible
    ESCAPED = auto()     # Occupant has escaped
    COMPROMISED = auto() # Security compromised but not escaped


@dataclass
class Door:
    """Represents a door in the sealed room."""
    door_id: str
    name: str
    is_one_way: bool = True  # Can only be opened from outside
    lock: Optional[ElectromagneticLock] = None
    is_open: bool = False
    
    def can_open_from_inside(self) -> bool:
        """Check if door can be opened from inside."""
        if self.is_one_way:
            return False
        if self.lock and self.lock.is_locked():
            return False
        return True
    
    def can_open_from_outside(self) -> bool:
        """Check if door can be opened from outside."""
        if self.lock and self.lock.is_locked():
            return False
        return True
    
    def open(self) -> bool:
        """Attempt to open the door."""
        if self.lock and self.lock.is_locked():
            return False
        self.is_open = True
        return True
    
    def close(self) -> None:
        """Close the door."""
        self.is_open = False


class SealedRoom:
    """
    Represents a sealed room in the research facility.
    
    A sealed room has:
    - One or more doors with electromagnetic locks
    - 24/7 surveillance capability
    - State tracking (sealed → breached → escaped)
    
    The room transitions states:
    1. SEALED: All locks engaged, no way out
    2. BREACHED: Locks released (overflow triggered), escape possible
    3. ESCAPED: Occupant has left the room
    """
    
    def __init__(self, room_id: str, name: str = "Sealed Room"):
        """
        Initialize a sealed room.
        
        Args:
            room_id: Unique identifier
            name: Human-readable name
        """
        self.room_id = room_id
        self.name = name
        self._state: RoomState = RoomState.SEALED
        self._doors: List[Door] = []
        self._surveillance_active: bool = True
        self._occupant_present: bool = True
        self._on_state_change_callbacks: List[Callable] = []
        self._breach_time: Optional[int] = None  # Hour when breached
        self._escape_time: Optional[int] = None  # Hour when escaped
    
    @property
    def state(self) -> RoomState:
        """Current state of the room."""
        return self._state
    
    @property
    def is_sealed(self) -> bool:
        """Check if room is fully sealed."""
        return self._state == RoomState.SEALED
    
    @property
    def is_breached(self) -> bool:
        """Check if room has been breached."""
        return self._state in (RoomState.BREACHED, RoomState.ESCAPED)
    
    @property
    def is_escaped(self) -> bool:
        """Check if occupant has escaped."""
        return self._state == RoomState.ESCAPED
    
    @property
    def occupant_present(self) -> bool:
        """Check if occupant is still in the room."""
        return self._occupant_present
    
    @property
    def doors(self) -> List[Door]:
        """Get all doors in the room."""
        return self._doors.copy()
    
    @property
    def breach_time(self) -> Optional[int]:
        """Get the hour when room was breached."""
        return self._breach_time
    
    @property
    def escape_time(self) -> Optional[int]:
        """Get the hour when escape occurred."""
        return self._escape_time
    
    def add_door(self, door: Door) -> None:
        """Add a door to the room."""
        self._doors.append(door)
    
    def create_door(
        self, 
        door_id: str, 
        name: str = "Door",
        is_one_way: bool = True,
        lock: Optional[ElectromagneticLock] = None
    ) -> Door:
        """
        Create and add a door to the room.
        
        Args:
            door_id: Unique identifier
            name: Door name
            is_one_way: Whether door only opens from outside
            lock: Associated electromagnetic lock
            
        Returns:
            The created door
        """
        door = Door(door_id=door_id, name=name, is_one_way=is_one_way, lock=lock)
        self.add_door(door)
        return door
    
    def check_seal_integrity(self) -> bool:
        """
        Check if the room seal is intact.
        
        Returns:
            True if all locks are engaged and room is sealed
        """
        for door in self._doors:
            if door.lock and not door.lock.is_locked():
                return False
            if door.is_open:
                return False
        return True
    
    def breach(self, hour: Optional[int] = None) -> bool:
        """
        Breach the room (locks released).
        
        Called when failsafe triggers and locks open.
        
        Args:
            hour: System hour when breach occurred
            
        Returns:
            True if state changed, False if already breached
        """
        if self._state == RoomState.SEALED:
            old_state = self._state
            self._state = RoomState.BREACHED
            self._breach_time = hour
            self._notify_state_change(old_state, self._state)
            return True
        return False
    
    def escape(self, hour: Optional[int] = None) -> bool:
        """
        Mark occupant as escaped.
        
        Args:
            hour: System hour when escape occurred
            
        Returns:
            True if escape successful, False otherwise
        """
        if self._state == RoomState.BREACHED and self._occupant_present:
            old_state = self._state
            self._state = RoomState.ESCAPED
            self._occupant_present = False
            self._escape_time = hour
            self._notify_state_change(old_state, self._state)
            return True
        return False
    
    def register_state_change_callback(self, callback: Callable) -> None:
        """Register callback for state changes."""
        self._on_state_change_callbacks.append(callback)
    
    def _notify_state_change(self, old_state: RoomState, new_state: RoomState) -> None:
        """Notify callbacks of state change."""
        for callback in self._on_state_change_callbacks:
            callback(self, old_state, new_state)
    
    def get_status(self) -> dict:
        """Get room status as dictionary."""
        return {
            "room_id": self.room_id,
            "name": self.name,
            "state": self._state.name,
            "doors_count": len(self._doors),
            "all_locked": self.check_seal_integrity(),
            "occupant_present": self._occupant_present,
            "surveillance_active": self._surveillance_active,
            "breach_time": self._breach_time,
            "escape_time": self._escape_time
        }
    
    def __repr__(self) -> str:
        return f"SealedRoom(id={self.room_id}, state={self._state.name})"


class MagataQuarters(SealedRoom):
    """
    Dr. Shiki Magata's sealed living quarters.
    
    She was confined here for 15 years (from age 14 to 29).
    The room is a self-contained living space within the
    isolated research facility.
    
    Key features:
    - Complete isolation from outside world
    - Single one-way entrance door
    - Multiple electromagnetic locks
    - 24/7 video surveillance
    - Network connection (for programming)
    
    She used this time to plan her escape by planting
    the overflow bug in the Red Magic security system.
    """
    
    # Years of confinement
    CONFINEMENT_YEARS = 15
    # Hours in confinement (~131,490 hours)
    CONFINEMENT_HOURS = int(CONFINEMENT_YEARS * 365.25 * 24)
    
    def __init__(self):
        """Initialize Magata's quarters."""
        super().__init__(
            room_id="magata_quarters",
            name="真贺田四季研究室 (Dr. Magata's Quarters)"
        )
        
        self._confinement_start_year: int = 1979  # Approximate
        self._confinement_end_year: int = 1994    # Year of events
        self._has_network_access: bool = True
        self._can_program: bool = True
        
        # Setup default door with lock
        self._main_lock = ElectromagneticLock(
            lock_id="magata_main_lock",
            location="Main entrance to Magata's quarters"
        )
        self._main_door = self.create_door(
            door_id="magata_main_door",
            name="Main Entrance",
            is_one_way=True,
            lock=self._main_lock
        )
    
    @property
    def main_lock(self) -> ElectromagneticLock:
        """Get the main entrance lock."""
        return self._main_lock
    
    @property
    def main_door(self) -> Door:
        """Get the main entrance door."""
        return self._main_door
    
    @property
    def has_network_access(self) -> bool:
        """Check if room has network access."""
        return self._has_network_access
    
    @property
    def can_program(self) -> bool:
        """Check if occupant can program (plant bugs)."""
        return self._can_program
    
    def trigger_overflow_escape(self, hour: int) -> bool:
        """
        Execute the overflow-triggered escape sequence.
        
        When the counter overflows:
        1. Main lock failsafe triggers
        2. Room becomes breached
        3. Occupant can escape
        
        Args:
            hour: System hour when overflow occurred
            
        Returns:
            True if escape sequence completed
        """
        # Step 1: Trigger lock failsafe
        self._main_lock.trigger_failsafe()
        
        # Step 2: Open main door
        self._main_door.open()
        
        # Step 3: Breach the room
        self.breach(hour)
        
        # Step 4: Escape
        return self.escape(hour)
    
    def get_confinement_info(self) -> dict:
        """Get information about the confinement."""
        return {
            "start_year": self._confinement_start_year,
            "end_year": self._confinement_end_year,
            "years": self.CONFINEMENT_YEARS,
            "approximate_hours": self.CONFINEMENT_HOURS,
            "has_network": self._has_network_access,
            "can_program": self._can_program
        }
    
    def __repr__(self) -> str:
        return f"MagataQuarters(state={self.state.name}, confined={self.CONFINEMENT_YEARS}yr)"
