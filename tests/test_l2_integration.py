"""
test_l2_integration.py - L2 Integration Tests
===============================================

Tests interactions between components.
Verifies that components work together correctly.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from everything_becomes_f.counter import UnsignedShortCounter
from everything_becomes_f.electromagnetic_lock import ElectromagneticLock, LockSystem
from everything_becomes_f.security_camera import SecurityCamera, ClockSyncVulnerability
from everything_becomes_f.sealed_room import SealedRoom, MagataQuarters, RoomState
from everything_becomes_f.event_system import EventBus, EventType
from everything_becomes_f.red_magic_system import RedMagicSystem, SystemState, create_standard_facility


# =============================================================================
# Counter + Lock Integration Tests
# =============================================================================

class TestCounterLockIntegration:
    """Tests counter overflow triggering lock release."""
    
    def test_overflow_triggers_lock_release(self):
        """Counter overflow should trigger lock failsafe."""
        counter = UnsignedShortCounter()
        lock_system = LockSystem("Test")
        lock_system.create_lock("lock_1", "Door 1")
        lock_system.create_lock("lock_2", "Door 2")
        
        # Register callback to trigger failsafe on overflow
        def on_overflow(c):
            lock_system.trigger_global_failsafe()
        
        counter.register_overflow_callback(on_overflow)
        
        # Verify locks are initially locked
        assert lock_system.all_locked()
        
        # Cause overflow
        counter.set_value(0xFFFF)
        counter.increment()
        
        # Verify locks are now unlocked
        assert lock_system.all_unlocked()
        assert lock_system.failsafe_triggered
    
    def test_fast_forward_to_overflow_unlocks(self):
        """Fast forward to overflow should unlock all locks."""
        counter = UnsignedShortCounter()
        lock_system = LockSystem("Test")
        lock_system.create_lock("lock_1", "Door 1")
        
        def on_overflow(c):
            lock_system.trigger_global_failsafe()
        
        counter.register_overflow_callback(on_overflow)
        
        # Fast forward past overflow
        counter.fast_forward(65536)
        
        assert lock_system.all_unlocked()


# =============================================================================
# Event Propagation Tests
# =============================================================================

class TestEventPropagation:
    """Tests event chain propagation through the system."""
    
    def test_overflow_event_chain(self):
        """Overflow should trigger event chain: overflow → locks → room."""
        event_bus = EventBus("Test")
        events_received = []
        
        # Track all events
        def handler(event):
            events_received.append(event.event_type)
        
        event_bus.subscribe_all(handler)
        
        # Simulate event chain
        event_bus.emit(EventType.COUNTER_OVERFLOW, source="counter")
        event_bus.emit(EventType.FAILSAFE_TRIGGERED, source="system")
        event_bus.emit(EventType.LOCKS_RELEASED, source="locks")
        event_bus.emit(EventType.ROOM_BREACHED, source="room")
        
        assert EventType.COUNTER_OVERFLOW in events_received
        assert EventType.LOCKS_RELEASED in events_received
        assert EventType.ROOM_BREACHED in events_received
        
        # Verify order
        assert events_received.index(EventType.COUNTER_OVERFLOW) < \
               events_received.index(EventType.LOCKS_RELEASED)
        assert events_received.index(EventType.LOCKS_RELEASED) < \
               events_received.index(EventType.ROOM_BREACHED)
    
    def test_event_bus_component_communication(self):
        """Components should communicate via event bus."""
        event_bus = EventBus("Test")
        
        # Counter component
        counter = UnsignedShortCounter()
        
        # Lock component - subscribes to overflow
        lock_system = LockSystem("Test")
        lock_system.create_lock("lock_1", "Door 1")
        
        def on_counter_overflow(event):
            lock_system.trigger_global_failsafe()
            event_bus.emit(EventType.LOCKS_RELEASED, source="lock_system")
        
        event_bus.subscribe(EventType.COUNTER_OVERFLOW, on_counter_overflow)
        
        # Room component - subscribes to locks released
        room = SealedRoom("room_1", "Test Room")
        
        def on_locks_released(event):
            room.breach()
            event_bus.emit(EventType.ROOM_BREACHED, source="room")
        
        event_bus.subscribe(EventType.LOCKS_RELEASED, on_locks_released)
        
        # Trigger the chain by emitting overflow
        event_bus.emit(EventType.COUNTER_OVERFLOW, source="counter")
        
        # Verify end state
        assert lock_system.all_unlocked()
        assert room.is_breached


# =============================================================================
# Clock Sync Vulnerability + Camera Tests
# =============================================================================

class TestClockSyncCameraIntegration:
    """Tests clock sync vulnerability creating camera blind spots."""
    
    def test_vulnerability_creates_blind_spot(self):
        """Exploiting vulnerability should create blind spots on cameras."""
        cameras = [
            SecurityCamera(camera_id="cam_1", location="Room 1"),
            SecurityCamera(camera_id="cam_2", location="Room 2"),
        ]
        
        # Record some footage first
        for cam in cameras:
            for minute in range(60):
                cam.record_minute(100, minute)
        
        vulnerability = ClockSyncVulnerability(cameras)
        
        # Exploit at specific time
        affected = vulnerability.exploit(100, 30)
        
        assert affected == 2
        
        # All cameras should have blind spot at that time
        for cam in cameras:
            assert cam.has_blind_spots()
            blind_spots = cam.get_blind_spots()
            assert any(bs.minute_index == 30 for bs in blind_spots)
    
    def test_reinstall_simulation(self):
        """Simulating reinstall should create blind spot."""
        cameras = [SecurityCamera(camera_id="cam_1", location="Room 1")]
        vulnerability = ClockSyncVulnerability(cameras)
        
        result = vulnerability.simulate_reinstall(50, 15)
        
        assert result["reinstall_triggered"]
        assert result["blind_spot_created"]
        assert result["clock_drift_minutes"] == 1
        assert result["blind_spot_time"] == (50, 15)


# =============================================================================
# Red Magic System Integration Tests
# =============================================================================

class TestRedMagicSystemIntegration:
    """Tests Red Magic system state transitions and component coordination."""
    
    def test_system_state_transitions(self, running_system):
        """System should transition through states correctly."""
        assert running_system.state == SystemState.RUNNING
        
        # Fast forward to overflow
        running_system.fast_forward_to_overflow()
        
        # Should be in SYSTEM_DOWN after overflow
        assert running_system.state == SystemState.SYSTEM_DOWN
    
    def test_system_initializing_to_running(self, initialized_system):
        """System should transition from INITIALIZING to RUNNING."""
        assert initialized_system.state == SystemState.INITIALIZING
        
        initialized_system.start()
        
        assert initialized_system.state == SystemState.RUNNING
    
    def test_overflow_triggers_full_sequence(self, running_system):
        """Overflow should trigger: OVERFLOW_DETECTED → FAILSAFE → SYSTEM_DOWN."""
        # Add a room to the system
        room = MagataQuarters()
        running_system.add_sealed_room(room)
        running_system.add_lock(room.main_lock)
        
        # Fast forward to overflow
        running_system.fast_forward_to_overflow()
        
        # Check final state
        assert running_system.state == SystemState.SYSTEM_DOWN
        assert running_system.lock_system.failsafe_triggered
        assert room.is_breached
    
    def test_system_events_during_overflow(self, running_system):
        """System should emit events during overflow sequence."""
        event_types_received = []
        
        def handler(event):
            event_types_received.append(event.event_type)
        
        running_system.event_bus.subscribe_all(handler)
        
        # Trigger overflow
        running_system.fast_forward_to_overflow()
        
        # Should have key events
        assert EventType.COUNTER_OVERFLOW in event_types_received
        assert EventType.FAILSAFE_TRIGGERED in event_types_received
        assert EventType.LOCKS_RELEASED in event_types_received
        assert EventType.SYSTEM_CRASH in event_types_received
    
    def test_standard_facility_setup(self, standard_facility):
        """Standard facility should have all components configured."""
        assert standard_facility.lock_system.lock_count >= 1
        assert len(standard_facility.cameras) >= 1
        assert len(standard_facility.sealed_rooms) >= 1
        assert standard_facility.state == SystemState.INITIALIZING


# =============================================================================
# Room + Lock Integration Tests
# =============================================================================

class TestRoomLockIntegration:
    """Tests sealed room behavior with electromagnetic locks."""
    
    def test_room_breach_when_locks_released(self, sealed_room):
        """Room should breach when its lock is released."""
        # Get the door's lock
        door = sealed_room.doors[0]
        
        # Release the lock
        door.lock.trigger_failsafe()
        
        # Room should still be sealed (lock release doesn't auto-breach)
        assert sealed_room.is_sealed
        
        # But now breach is possible
        sealed_room.breach()
        assert sealed_room.is_breached
    
    def test_magata_quarters_full_escape_sequence(self, magata_quarters):
        """Full escape sequence through Magata's quarters."""
        # Initial state
        assert magata_quarters.is_sealed
        assert magata_quarters.main_lock.is_locked()
        
        # Trigger overflow escape
        magata_quarters.trigger_overflow_escape(65536)
        
        # Final state
        assert magata_quarters.state == RoomState.ESCAPED
        assert magata_quarters.main_lock.is_unlocked()
        assert not magata_quarters.occupant_present


# =============================================================================
# System-Wide Event Tracking Tests
# =============================================================================

class TestSystemWideEvents:
    """Tests event tracking across entire system."""
    
    def test_complete_event_sequence(self, standard_facility):
        """Track complete event sequence from start to crash."""
        events = []
        
        def handler(event):
            events.append(event.event_type.name)
        
        standard_facility.event_bus.subscribe_all(handler)
        
        # Start system
        standard_facility.start()
        
        # Run to overflow
        standard_facility.fast_forward_to_overflow()
        
        # Should have complete sequence
        assert "SYSTEM_STARTED" in events
        assert "COUNTER_OVERFLOW" in events
        assert "FAILSAFE_TRIGGERED" in events
        assert "LOCKS_RELEASED" in events
        assert "SYSTEM_CRASH" in events
    
    def test_event_source_tracking(self, running_system):
        """Events should have correct source attribution."""
        events_by_source = {}
        
        def handler(event):
            source = event.source
            if source not in events_by_source:
                events_by_source[source] = []
            events_by_source[source].append(event.event_type)
        
        running_system.event_bus.subscribe_all(handler)
        running_system.fast_forward_to_overflow()
        
        # Should have events from multiple sources
        assert "UnsignedShortCounter" in events_by_source
        assert "RedMagicSystem" in events_by_source


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
