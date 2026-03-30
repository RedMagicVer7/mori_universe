"""
conftest.py - Shared pytest fixtures for all test levels.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from everything_becomes_f.counter import UnsignedShortCounter
from everything_becomes_f.electromagnetic_lock import ElectromagneticLock, LockSystem
from everything_becomes_f.security_camera import SecurityCamera, ClockSyncVulnerability
from everything_becomes_f.sealed_room import SealedRoom, MagataQuarters, RoomState
from everything_becomes_f.event_system import EventBus, EventType
from everything_becomes_f.red_magic_system import RedMagicSystem, SystemState, create_standard_facility
from everything_becomes_f.runtime import EverythingBecomesFRuntime, Phase


# =============================================================================
# Counter Fixtures
# =============================================================================

@pytest.fixture
def fresh_counter():
    """A fresh counter starting at 0."""
    return UnsignedShortCounter()


@pytest.fixture
def counter_near_overflow():
    """A counter near overflow (at 0xFFFE = 65534)."""
    counter = UnsignedShortCounter()
    counter.set_value(0xFFFE)
    return counter


@pytest.fixture
def counter_at_max():
    """A counter at maximum value (0xFFFF = 65535)."""
    counter = UnsignedShortCounter()
    counter.set_value(0xFFFF)
    return counter


# =============================================================================
# Lock Fixtures
# =============================================================================

@pytest.fixture
def fresh_lock():
    """A fresh electromagnetic lock in locked state."""
    return ElectromagneticLock(lock_id="test_lock", location="Test Location")


@pytest.fixture
def fresh_lock_system():
    """A fresh lock system with 3 locks."""
    system = LockSystem("Test Lock System")
    system.create_lock("lock_1", "Door 1")
    system.create_lock("lock_2", "Door 2")
    system.create_lock("lock_3", "Door 3")
    return system


# =============================================================================
# Camera Fixtures
# =============================================================================

@pytest.fixture
def fresh_camera():
    """A fresh security camera."""
    return SecurityCamera(camera_id="test_cam", location="Test Location")


@pytest.fixture
def camera_with_recordings():
    """A camera with some recordings."""
    camera = SecurityCamera(camera_id="test_cam", location="Test Location")
    for hour in range(3):
        for minute in range(60):
            camera.record_minute(hour, minute)
    return camera


@pytest.fixture
def clock_vulnerability():
    """Clock sync vulnerability with cameras."""
    cameras = [
        SecurityCamera(camera_id="cam_1", location="Location 1"),
        SecurityCamera(camera_id="cam_2", location="Location 2"),
    ]
    return ClockSyncVulnerability(cameras)


# =============================================================================
# Room Fixtures
# =============================================================================

@pytest.fixture
def sealed_room():
    """A basic sealed room."""
    room = SealedRoom(room_id="test_room", name="Test Room")
    lock = ElectromagneticLock(lock_id="room_lock", location="Room Door")
    room.create_door("main_door", "Main Door", is_one_way=True, lock=lock)
    return room


@pytest.fixture
def magata_quarters():
    """Magata's sealed quarters."""
    return MagataQuarters()


# =============================================================================
# Event System Fixtures
# =============================================================================

@pytest.fixture
def event_bus():
    """A fresh event bus."""
    return EventBus("Test Event Bus")


@pytest.fixture
def event_bus_with_history():
    """An event bus with some event history."""
    bus = EventBus("Test Event Bus")
    bus.emit(EventType.SYSTEM_INITIALIZED, source="test")
    bus.emit(EventType.SYSTEM_STARTED, source="test")
    bus.emit(EventType.COUNTER_INCREMENT, source="test", hour=1)
    return bus


# =============================================================================
# System Fixtures
# =============================================================================

@pytest.fixture
def fresh_system():
    """A fresh Red Magic system."""
    return RedMagicSystem("Test System")


@pytest.fixture
def initialized_system():
    """An initialized Red Magic system."""
    system = RedMagicSystem("Test System")
    system.initialize()
    return system


@pytest.fixture
def running_system():
    """A running Red Magic system."""
    system = RedMagicSystem("Test System")
    system.initialize()
    system.start()
    return system


@pytest.fixture
def standard_facility():
    """Standard facility setup with all components."""
    return create_standard_facility()


@pytest.fixture
def system_near_overflow():
    """A system near overflow."""
    system = create_standard_facility()
    system.start()
    system.counter.set_value(0xFFFE)  # 2 hours from overflow
    return system


# =============================================================================
# Runtime Fixtures
# =============================================================================

@pytest.fixture
def fresh_runtime():
    """A fresh runtime."""
    return EverythingBecomesFRuntime()


@pytest.fixture
def started_runtime():
    """A runtime that has been started."""
    runtime = EverythingBecomesFRuntime()
    runtime.start()
    return runtime


# =============================================================================
# Helper Functions
# =============================================================================

def collect_events(event_bus: EventBus, event_type: EventType = None):
    """Helper to collect events from bus."""
    collected = []
    
    def handler(event):
        collected.append(event)
    
    if event_type:
        event_bus.subscribe(event_type, handler)
    else:
        event_bus.subscribe_all(handler)
    
    return collected


@pytest.fixture
def event_collector():
    """Factory fixture for event collection."""
    return collect_events
