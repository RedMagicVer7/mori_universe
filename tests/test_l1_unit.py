"""
test_l1_unit.py - L1 Unit Tests
================================

Tests individual components in isolation.
Each test focuses on a single unit of functionality.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from everything_becomes_f.counter import UnsignedShortCounter
from everything_becomes_f.electromagnetic_lock import ElectromagneticLock, LockSystem, LockState
from everything_becomes_f.security_camera import SecurityCamera, ClockSyncVulnerability, CameraState
from everything_becomes_f.sealed_room import SealedRoom, MagataQuarters, RoomState
from everything_becomes_f.event_system import EventBus, EventType, Event


# =============================================================================
# Counter Unit Tests
# =============================================================================

class TestUnsignedShortCounter:
    """Unit tests for UnsignedShortCounter."""
    
    def test_initialization_default(self):
        """Counter should initialize to 0."""
        counter = UnsignedShortCounter()
        assert counter.value == 0
        assert counter.hex_value == "0x0000"
        assert counter.overflow_count == 0
    
    def test_initialization_with_value(self):
        """Counter should accept initial value."""
        counter = UnsignedShortCounter(initial_value=100)
        assert counter.value == 100
        assert counter.hex_value == "0x0064"
    
    def test_initialization_invalid_value(self):
        """Counter should reject invalid initial values."""
        with pytest.raises(ValueError):
            UnsignedShortCounter(initial_value=-1)
        with pytest.raises(ValueError):
            UnsignedShortCounter(initial_value=65536)
    
    def test_increment_basic(self, fresh_counter):
        """Basic increment should work."""
        overflow = fresh_counter.increment()
        assert not overflow
        assert fresh_counter.value == 1
    
    def test_increment_by_amount(self, fresh_counter):
        """Increment by specific amount."""
        fresh_counter.increment(100)
        assert fresh_counter.value == 100
    
    def test_increment_negative_rejected(self, fresh_counter):
        """Negative increment should be rejected."""
        with pytest.raises(ValueError):
            fresh_counter.increment(-1)
    
    def test_overflow_detection(self, counter_at_max):
        """Counter should detect overflow at 0xFFFF + 1."""
        assert counter_at_max.value == 0xFFFF  # 65535
        overflow = counter_at_max.increment()
        assert overflow is True
        assert counter_at_max.value == 0  # Wrapped to 0
        assert counter_at_max.overflow_count == 1
    
    def test_overflow_wrapping(self):
        """0xFFFF + 1 = 0x0000 (wraps to zero)."""
        counter = UnsignedShortCounter(initial_value=0xFFFF)
        counter.increment()
        assert counter.value == 0x0000
        assert counter.hex_value == "0x0000"
    
    def test_max_value_constant(self):
        """MAX_VALUE should be 0xFFFF (65535)."""
        assert UnsignedShortCounter.MAX_VALUE == 0xFFFF
        assert UnsignedShortCounter.MAX_VALUE == 65535
    
    def test_hex_value_formatting(self):
        """Hex value should be properly formatted."""
        counter = UnsignedShortCounter(initial_value=0xABCD)
        assert counter.hex_value == "0xABCD"
    
    def test_hours_until_overflow(self, fresh_counter):
        """Should calculate hours until overflow."""
        assert fresh_counter.hours_until_overflow() == 65536  # 0xFFFF + 1
    
    def test_hours_until_overflow_near_max(self, counter_near_overflow):
        """Should be 2 hours at 0xFFFE."""
        assert counter_near_overflow.hours_until_overflow() == 2
    
    def test_years_until_overflow(self, fresh_counter):
        """Should calculate ~7.48 years."""
        years = fresh_counter.years_until_overflow()
        assert 7.4 < years < 7.5
    
    def test_fast_forward_basic(self, fresh_counter):
        """Fast forward should advance counter."""
        overflows = fresh_counter.fast_forward(1000)
        assert overflows == 0
        assert fresh_counter.value == 1000
    
    def test_fast_forward_with_overflow(self, fresh_counter):
        """Fast forward should handle overflow."""
        # Fast forward 65536 hours = exactly 1 overflow
        overflows = fresh_counter.fast_forward(65536)
        assert overflows == 1
        assert fresh_counter.value == 0
    
    def test_fast_forward_multiple_overflows(self, fresh_counter):
        """Fast forward should handle multiple overflows."""
        # Fast forward 131072 hours = 2 overflows
        overflows = fresh_counter.fast_forward(131072)
        assert overflows == 2
        assert fresh_counter.value == 0
    
    def test_overflow_callback(self, fresh_counter):
        """Overflow callback should be called."""
        callback_called = []
        
        def callback(counter):
            callback_called.append(counter.overflow_count)
        
        fresh_counter.register_overflow_callback(callback)
        fresh_counter.set_value(0xFFFF)
        fresh_counter.increment()
        
        assert len(callback_called) == 1
        assert callback_called[0] == 1
    
    def test_is_at_max(self, counter_at_max, fresh_counter):
        """Should detect when at max value."""
        assert counter_at_max.is_at_max()
        assert not fresh_counter.is_at_max()
    
    def test_is_at_zero(self, fresh_counter, counter_at_max):
        """Should detect when at zero."""
        assert fresh_counter.is_at_zero()
        assert not counter_at_max.is_at_zero()


# =============================================================================
# Electromagnetic Lock Unit Tests
# =============================================================================

class TestElectromagneticLock:
    """Unit tests for ElectromagneticLock."""
    
    def test_initialization(self):
        """Lock should initialize as locked and powered."""
        lock = ElectromagneticLock(lock_id="test", location="Test")
        assert lock.is_locked()
        assert lock.is_powered
        assert lock.state == LockState.LOCKED
    
    def test_power_off_unlocks(self, fresh_lock):
        """Cutting power should unlock."""
        fresh_lock.power_off()
        assert not fresh_lock.is_locked()
        assert fresh_lock.is_unlocked()
        assert not fresh_lock.is_powered
    
    def test_power_on_locks(self, fresh_lock):
        """Applying power should lock."""
        fresh_lock.power_off()
        fresh_lock.power_on()
        assert fresh_lock.is_locked()
        assert fresh_lock.is_powered
    
    def test_failsafe_triggers_unlock(self, fresh_lock):
        """Failsafe should unlock regardless of power."""
        fresh_lock.trigger_failsafe()
        assert fresh_lock.is_unlocked()
        assert not fresh_lock.is_powered
    
    def test_state_change_callback(self, fresh_lock):
        """State change callback should be called."""
        states = []
        
        def callback(lock, old, new):
            states.append((old, new))
        
        fresh_lock.register_state_change_callback(callback)
        fresh_lock.power_off()
        
        assert len(states) == 1
        assert states[0] == (LockState.LOCKED, LockState.UNLOCKED)


class TestLockSystem:
    """Unit tests for LockSystem."""
    
    def test_initialization(self):
        """Lock system should initialize empty."""
        system = LockSystem("Test")
        assert system.lock_count == 0
        assert not system.failsafe_triggered
    
    def test_add_lock(self, fresh_lock_system):
        """Should manage multiple locks."""
        assert fresh_lock_system.lock_count == 3
        assert fresh_lock_system.locked_count == 3
    
    def test_all_locked(self, fresh_lock_system):
        """Should detect all locks engaged."""
        assert fresh_lock_system.all_locked()
        fresh_lock_system.locks[0].power_off()
        assert not fresh_lock_system.all_locked()
    
    def test_global_failsafe(self, fresh_lock_system):
        """Global failsafe should unlock all."""
        unlocked = fresh_lock_system.trigger_global_failsafe()
        assert unlocked == 3
        assert fresh_lock_system.all_unlocked()
        assert fresh_lock_system.failsafe_triggered


# =============================================================================
# Security Camera Unit Tests
# =============================================================================

class TestSecurityCamera:
    """Unit tests for SecurityCamera."""
    
    def test_initialization(self):
        """Camera should initialize as active."""
        camera = SecurityCamera(camera_id="test", location="Test")
        assert camera.is_active()
        assert camera.state == CameraState.ACTIVE
    
    def test_record_minute(self, fresh_camera):
        """Should record minute segments."""
        segment = fresh_camera.record_minute(0, 30)
        assert segment.hour_index == 0
        assert segment.minute_index == 30
        assert not segment.is_blind_spot
    
    def test_create_blind_spot(self, fresh_camera):
        """Should create blind spot."""
        segment = fresh_camera.create_blind_spot(0, 15)
        assert segment.is_blind_spot
        assert fresh_camera.has_blind_spots()
    
    def test_blind_spots_list(self, fresh_camera):
        """Should track all blind spots."""
        fresh_camera.create_blind_spot(0, 10)
        fresh_camera.create_blind_spot(0, 20)
        fresh_camera.record_minute(0, 30)
        
        blind_spots = fresh_camera.get_blind_spots()
        assert len(blind_spots) == 2


class TestClockSyncVulnerability:
    """Unit tests for ClockSyncVulnerability."""
    
    def test_initialization(self, clock_vulnerability):
        """Should initialize with cameras."""
        assert len(clock_vulnerability.cameras) == 2
        assert not clock_vulnerability.is_exploited
    
    def test_exploit(self, clock_vulnerability):
        """Exploit should create blind spots on all cameras."""
        affected = clock_vulnerability.exploit(10, 30)
        assert affected == 2
        assert clock_vulnerability.is_exploited
        assert clock_vulnerability.blind_spot_time == (10, 30)
    
    def test_drift_constant(self):
        """Drift should be 1 minute."""
        assert ClockSyncVulnerability.DRIFT_MINUTES == 1


# =============================================================================
# Sealed Room Unit Tests
# =============================================================================

class TestSealedRoom:
    """Unit tests for SealedRoom."""
    
    def test_initialization(self):
        """Room should initialize as sealed."""
        room = SealedRoom(room_id="test", name="Test Room")
        assert room.is_sealed
        assert room.state == RoomState.SEALED
        assert room.occupant_present
    
    def test_add_door(self, sealed_room):
        """Should have doors."""
        assert len(sealed_room.doors) == 1
    
    def test_breach(self, sealed_room):
        """Breach should change state."""
        sealed_room.breach(hour=100)
        assert sealed_room.is_breached
        assert sealed_room.state == RoomState.BREACHED
        assert sealed_room.breach_time == 100
    
    def test_escape(self, sealed_room):
        """Escape requires breach first."""
        # Can't escape sealed room
        assert not sealed_room.escape()
        
        # Breach then escape
        sealed_room.breach(100)
        assert sealed_room.escape(101)
        assert sealed_room.state == RoomState.ESCAPED
        assert not sealed_room.occupant_present


class TestMagataQuarters:
    """Unit tests for MagataQuarters."""
    
    def test_initialization(self, magata_quarters):
        """Quarters should initialize properly."""
        assert magata_quarters.is_sealed
        assert magata_quarters.has_network_access
        assert magata_quarters.can_program
        assert magata_quarters.main_lock.is_locked()
    
    def test_confinement_constants(self):
        """Should have correct confinement duration."""
        assert MagataQuarters.CONFINEMENT_YEARS == 15
        # ~131,490 hours
        assert MagataQuarters.CONFINEMENT_HOURS > 130000
    
    def test_overflow_escape(self, magata_quarters):
        """Overflow should enable escape."""
        success = magata_quarters.trigger_overflow_escape(65536)
        assert success
        assert magata_quarters.state == RoomState.ESCAPED
        assert magata_quarters.main_lock.is_unlocked()


# =============================================================================
# Event System Unit Tests
# =============================================================================

class TestEventBus:
    """Unit tests for EventBus."""
    
    def test_initialization(self):
        """Event bus should initialize empty."""
        bus = EventBus("Test")
        assert bus.get_event_count() == 0
    
    def test_emit_and_subscribe(self, event_bus):
        """Should emit events to subscribers."""
        received = []
        
        def handler(event):
            received.append(event)
        
        event_bus.subscribe(EventType.COUNTER_OVERFLOW, handler)
        event_bus.emit(EventType.COUNTER_OVERFLOW, source="test")
        
        assert len(received) == 1
        assert received[0].event_type == EventType.COUNTER_OVERFLOW
    
    def test_subscribe_all(self, event_bus):
        """Should receive all events."""
        received = []
        
        def handler(event):
            received.append(event)
        
        event_bus.subscribe_all(handler)
        event_bus.emit(EventType.SYSTEM_STARTED, source="test")
        event_bus.emit(EventType.COUNTER_OVERFLOW, source="test")
        
        assert len(received) == 2
    
    def test_event_history(self, event_bus):
        """Should maintain event history."""
        event_bus.emit(EventType.SYSTEM_STARTED, source="test")
        event_bus.emit(EventType.COUNTER_OVERFLOW, source="test")
        
        assert event_bus.get_event_count() == 2
        assert event_bus.has_event(EventType.COUNTER_OVERFLOW)
    
    def test_pause_resume(self, event_bus):
        """Pausing should stop event delivery."""
        received = []
        
        def handler(event):
            received.append(event)
        
        event_bus.subscribe_all(handler)
        event_bus.pause()
        event_bus.emit(EventType.SYSTEM_STARTED, source="test")
        
        assert len(received) == 0
        
        event_bus.resume()
        event_bus.emit(EventType.SYSTEM_STARTED, source="test")
        
        assert len(received) == 1


class TestEventType:
    """Unit tests for EventType enumeration."""
    
    def test_core_events_exist(self):
        """Core event types should exist."""
        assert EventType.COUNTER_OVERFLOW is not None
        assert EventType.LOCKS_RELEASED is not None
        assert EventType.ROOM_BREACHED is not None
        assert EventType.SYSTEM_CRASH is not None
    
    def test_camera_events_exist(self):
        """Camera event types should exist."""
        assert EventType.CAMERA_BLIND_SPOT is not None
        assert EventType.CLOCK_SYNC_ERROR is not None


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
