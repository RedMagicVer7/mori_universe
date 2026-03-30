"""
red_magic_system.py - Red Magic Security System Core
======================================================

The Red Magic system is the central security system of the
Magata Research Facility. It integrates:
- Timer counter (16-bit unsigned short)
- Electromagnetic locks
- Security cameras
- Sealed room monitoring

Dr. Magata planted a bug in this system: the counter uses
unsigned short which overflows after 65535 hours (~7.5 years),
triggering failsafe and enabling escape.

System states:
INITIALIZING → RUNNING → OVERFLOW_DETECTED → FAILSAFE_TRIGGERED → SYSTEM_DOWN
"""

from enum import Enum, auto
from typing import Optional, List, Callable, Dict, Any
from dataclasses import dataclass

from .counter import UnsignedShortCounter
from .electromagnetic_lock import LockSystem, ElectromagneticLock
from .security_camera import SecurityCamera, ClockSyncVulnerability
from .sealed_room import SealedRoom, MagataQuarters, RoomState
from .event_system import EventBus, EventType, Event


class SystemState(Enum):
    """States of the Red Magic security system."""
    INITIALIZING = auto()       # System starting up
    RUNNING = auto()            # Normal operation
    OVERFLOW_DETECTED = auto()  # Counter overflow detected
    FAILSAFE_TRIGGERED = auto() # Emergency failsafe active
    SYSTEM_DOWN = auto()        # System shut down/crashed


@dataclass
class SystemLog:
    """A log entry in the system."""
    hour: int
    message: str
    level: str = "INFO"  # INFO, WARNING, ERROR, CRITICAL


class RedMagicSystem:
    """
    Red Magic Security System - Core Controller.
    
    Integrates all security subsystems:
    - UnsignedShortCounter: Hour timer (the bug is here)
    - LockSystem: Electromagnetic lock management
    - SecurityCamera: Surveillance system
    - SealedRoom: Room state tracking
    - EventBus: Inter-component communication
    
    The system runs for ~7.5 years until counter overflow,
    then triggers failsafe and enables escape.
    """
    
    # System constants
    OVERFLOW_HOUR = 0xFFFF  # 65535 hours until overflow
    YEARS_TO_OVERFLOW = OVERFLOW_HOUR / (365.25 * 24)  # ~7.48 years
    
    def __init__(self, name: str = "Red Magic Security System"):
        """
        Initialize the Red Magic system.
        
        Args:
            name: System name identifier
        """
        self.name = name
        self._state: SystemState = SystemState.INITIALIZING
        
        # Initialize subsystems
        self._counter: UnsignedShortCounter = UnsignedShortCounter()
        self._lock_system: LockSystem = LockSystem("Red Magic Locks")
        self._event_bus: EventBus = EventBus("Red Magic Events")
        self._cameras: List[SecurityCamera] = []
        self._clock_vulnerability: Optional[ClockSyncVulnerability] = None
        self._sealed_rooms: List[SealedRoom] = []
        
        # System log
        self._logs: List[SystemLog] = []
        
        # State change callbacks
        self._on_state_change_callbacks: List[Callable] = []
        
        # Wire up event handlers
        self._setup_event_handlers()
    
    def _setup_event_handlers(self) -> None:
        """Set up internal event handlers."""
        # Counter overflow triggers failsafe
        self._counter.register_overflow_callback(self._on_counter_overflow)
    
    def _on_counter_overflow(self, counter: UnsignedShortCounter) -> None:
        """Handle counter overflow event."""
        self._log(counter.overflow_count * (self.OVERFLOW_HOUR + 1), 
                  "COUNTER OVERFLOW DETECTED! Value wrapped to 0x0000", "CRITICAL")
        
        # Emit event
        self._event_bus.emit(
            EventType.COUNTER_OVERFLOW,
            source="UnsignedShortCounter",
            hour=self._counter.total_increments,
            overflow_count=counter.overflow_count
        )
        
        # Transition to overflow detected state
        self._transition_to(SystemState.OVERFLOW_DETECTED)
        
        # Trigger failsafe
        self.trigger_failsafe()
    
    @property
    def state(self) -> SystemState:
        """Current system state."""
        return self._state
    
    @property
    def counter(self) -> UnsignedShortCounter:
        """Get the hour counter."""
        return self._counter
    
    @property
    def lock_system(self) -> LockSystem:
        """Get the lock system."""
        return self._lock_system
    
    @property
    def event_bus(self) -> EventBus:
        """Get the event bus."""
        return self._event_bus
    
    @property
    def cameras(self) -> List[SecurityCamera]:
        """Get all cameras."""
        return self._cameras.copy()
    
    @property
    def sealed_rooms(self) -> List[SealedRoom]:
        """Get all sealed rooms."""
        return self._sealed_rooms.copy()
    
    @property
    def current_hour(self) -> int:
        """Get current system hour."""
        return self._counter.value
    
    @property
    def hours_until_overflow(self) -> int:
        """Hours remaining until overflow."""
        return self._counter.hours_until_overflow()
    
    @property
    def years_until_overflow(self) -> float:
        """Years remaining until overflow."""
        return self._counter.years_until_overflow()
    
    @property
    def logs(self) -> List[SystemLog]:
        """Get system logs."""
        return self._logs.copy()
    
    def initialize(self) -> None:
        """Initialize the system."""
        self._state = SystemState.INITIALIZING
        self._log(0, "Red Magic Security System initializing...")
        
        # Emit initialization event
        self._event_bus.emit(
            EventType.SYSTEM_INITIALIZED,
            source="RedMagicSystem"
        )
        
        self._log(0, "System initialization complete")
    
    def start(self) -> None:
        """Start the system (transition to RUNNING)."""
        if self._state == SystemState.INITIALIZING:
            self._transition_to(SystemState.RUNNING)
            self._log(self._counter.value, "System started - RUNNING")
            
            self._event_bus.emit(
                EventType.SYSTEM_STARTED,
                source="RedMagicSystem"
            )
    
    def advance_hour(self) -> bool:
        """
        Advance the system by one hour.
        
        Returns:
            True if overflow occurred
        """
        if self._state != SystemState.RUNNING:
            return False
        
        overflow = self._counter.increment()
        
        # Emit counter increment event
        self._event_bus.emit(
            EventType.COUNTER_INCREMENT,
            source="UnsignedShortCounter",
            hour=self._counter.value,
            hex_value=self._counter.hex_value
        )
        
        return overflow
    
    def fast_forward(self, hours: int) -> int:
        """
        Fast forward the system by specified hours.
        
        Uses O(1) calculation instead of O(n) iteration.
        
        Args:
            hours: Number of hours to advance
            
        Returns:
            Number of overflows that occurred
        """
        if self._state != SystemState.RUNNING:
            return 0
        
        self._log(self._counter.value, f"Fast forwarding {hours} hours...")
        return self._counter.fast_forward(hours)
    
    def fast_forward_to_overflow(self) -> int:
        """
        Fast forward directly to overflow.
        
        Returns:
            Hours that were fast forwarded
        """
        hours_needed = self._counter.hours_until_overflow()
        self._counter.fast_forward(hours_needed)
        return hours_needed
    
    def add_camera(self, camera: SecurityCamera) -> None:
        """Add a camera to the system."""
        self._cameras.append(camera)
        if self._clock_vulnerability:
            self._clock_vulnerability.add_camera(camera)
    
    def create_camera(self, camera_id: str, location: str = "Unknown") -> SecurityCamera:
        """Create and add a camera."""
        camera = SecurityCamera(camera_id=camera_id, location=location)
        self.add_camera(camera)
        return camera
    
    def add_lock(self, lock: ElectromagneticLock) -> None:
        """Add a lock to the system."""
        self._lock_system.add_lock(lock)
    
    def create_lock(self, lock_id: str, location: str = "Unknown") -> ElectromagneticLock:
        """Create and add a lock."""
        return self._lock_system.create_lock(lock_id, location)
    
    def add_sealed_room(self, room: SealedRoom) -> None:
        """Add a sealed room to monitor."""
        self._sealed_rooms.append(room)
    
    def setup_clock_vulnerability(self) -> ClockSyncVulnerability:
        """Set up the clock synchronization vulnerability."""
        self._clock_vulnerability = ClockSyncVulnerability(self._cameras)
        return self._clock_vulnerability
    
    def trigger_failsafe(self) -> None:
        """
        Trigger the system failsafe.
        
        This is called when counter overflow is detected.
        All locks release, rooms become breached.
        """
        self._log(self._counter.value, "FAILSAFE TRIGGERED - All locks releasing", "CRITICAL")
        
        # Transition state
        self._transition_to(SystemState.FAILSAFE_TRIGGERED)
        
        # Emit failsafe event
        self._event_bus.emit(
            EventType.FAILSAFE_TRIGGERED,
            source="RedMagicSystem",
            hour=self._counter.value
        )
        
        # Release all locks
        unlocked = self._lock_system.trigger_global_failsafe()
        self._log(self._counter.value, f"Released {unlocked} locks")
        
        # Emit locks released event
        self._event_bus.emit(
            EventType.LOCKS_RELEASED,
            source="LockSystem",
            hour=self._counter.value,
            locks_count=unlocked
        )
        
        # Breach all sealed rooms
        for room in self._sealed_rooms:
            if room.is_sealed:
                room.breach(self._counter.value)
                self._event_bus.emit(
                    EventType.ROOM_BREACHED,
                    source="SealedRoom",
                    hour=self._counter.value,
                    room_id=room.room_id
                )
        
        # System goes down
        self._transition_to(SystemState.SYSTEM_DOWN)
        self._log(self._counter.value, "SYSTEM DOWN", "CRITICAL")
        
        self._event_bus.emit(
            EventType.SYSTEM_CRASH,
            source="RedMagicSystem",
            hour=self._counter.value,
            reason="failsafe_triggered"
        )
    
    def _transition_to(self, new_state: SystemState) -> None:
        """Transition to a new system state."""
        old_state = self._state
        self._state = new_state
        
        for callback in self._on_state_change_callbacks:
            callback(self, old_state, new_state)
    
    def register_state_change_callback(self, callback: Callable) -> None:
        """Register callback for state changes."""
        self._on_state_change_callbacks.append(callback)
    
    def _log(self, hour: int, message: str, level: str = "INFO") -> None:
        """Add a log entry."""
        self._logs.append(SystemLog(hour=hour, message=message, level=level))
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            "name": self.name,
            "state": self._state.name,
            "counter": {
                "value": self._counter.value,
                "hex": self._counter.hex_value,
                "overflows": self._counter.overflow_count,
                "hours_until_overflow": self._counter.hours_until_overflow(),
                "years_until_overflow": round(self._counter.years_until_overflow(), 2)
            },
            "locks": self._lock_system.get_status(),
            "cameras": len(self._cameras),
            "sealed_rooms": len(self._sealed_rooms),
            "events": self._event_bus.get_event_count(),
            "logs": len(self._logs)
        }
    
    def is_running(self) -> bool:
        """Check if system is in running state."""
        return self._state == SystemState.RUNNING
    
    def is_down(self) -> bool:
        """Check if system is down."""
        return self._state == SystemState.SYSTEM_DOWN
    
    def reset(self) -> None:
        """Reset the system to initial state."""
        self._state = SystemState.INITIALIZING
        self._counter = UnsignedShortCounter()
        self._counter.register_overflow_callback(self._on_counter_overflow)
        self._lock_system.reset()
        self._logs.clear()
        self._event_bus.clear_history()
    
    def __repr__(self) -> str:
        return f"RedMagicSystem(state={self._state.name}, hour={self._counter.hex_value})"


def create_standard_facility() -> RedMagicSystem:
    """
    Create a standard Magata Research Facility setup.
    
    Includes:
    - Red Magic system
    - Magata's sealed quarters
    - Main entrance lock
    - Security cameras
    - Clock sync vulnerability
    
    Returns:
        Configured RedMagicSystem instance
    """
    system = RedMagicSystem("Magata Research Facility - Red Magic")
    
    # Create Magata's quarters
    magata_room = MagataQuarters()
    system.add_sealed_room(magata_room)
    system.add_lock(magata_room.main_lock)
    
    # Create additional locks
    system.create_lock("entrance_lock", "Facility Main Entrance")
    system.create_lock("corridor_lock", "Secure Corridor")
    
    # Create cameras
    system.create_camera("cam_001", "Magata's Room")
    system.create_camera("cam_002", "Corridor A")
    system.create_camera("cam_003", "Main Entrance")
    
    # Setup clock vulnerability
    system.setup_clock_vulnerability()
    
    # Initialize system
    system.initialize()
    
    return system
