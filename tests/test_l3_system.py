"""
test_l3_system.py - L3 System Tests
=====================================

End-to-end system tests.
Tests complete simulation scenarios from start to finish.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from everything_becomes_f.counter import UnsignedShortCounter
from everything_becomes_f.sealed_room import MagataQuarters, RoomState
from everything_becomes_f.event_system import EventType
from everything_becomes_f.red_magic_system import RedMagicSystem, SystemState, create_standard_facility
from everything_becomes_f.runtime import EverythingBecomesFRuntime, Phase, PHASE_INFO


# =============================================================================
# 15-Year Simulation Tests
# =============================================================================

class TestFifteenYearSimulation:
    """Tests simulating the full 15-year (65535 hours) period."""
    
    def test_full_simulation_fast_forward(self, started_runtime):
        """Fast forward through complete simulation."""
        # Initial state
        assert started_runtime.current_phase == Phase.COLD_BOOT
        assert started_runtime.counter_value == 0
        
        # Run to overflow
        state = started_runtime.run_to_overflow()
        
        # Should be completed
        assert state.is_completed
        assert started_runtime.system.state == SystemState.SYSTEM_DOWN
    
    def test_65535_hours_equals_overflow(self):
        """65535 hours should trigger exactly one overflow."""
        counter = UnsignedShortCounter()
        
        # Fast forward exactly 65535 hours (to max value)
        counter.fast_forward(65535)
        assert counter.value == 0xFFFF
        assert counter.overflow_count == 0
        
        # One more hour triggers overflow
        counter.increment()
        assert counter.value == 0
        assert counter.overflow_count == 1
    
    def test_7_5_years_calculation(self):
        """Verify 65535 hours ≈ 7.5 years."""
        hours = 65535
        hours_per_year = 365.25 * 24  # 8766 hours
        years = hours / hours_per_year
        
        assert 7.4 < years < 7.5  # ~7.48 years
    
    def test_fast_forward_efficiency(self):
        """Fast forward should be O(1), not O(n)."""
        import time
        
        counter = UnsignedShortCounter()
        
        # Time fast forward of 1 million hours
        start = time.time()
        counter.fast_forward(1_000_000)
        elapsed = time.time() - start
        
        # Should be nearly instant (< 0.1 seconds)
        assert elapsed < 0.1
        
        # Should have correct overflow count
        expected_overflows = 1_000_000 // 65536
        assert counter.overflow_count == expected_overflows


# =============================================================================
# Sealed Room Escape Tests
# =============================================================================

class TestSealedRoomEscape:
    """Tests complete escape from sealed room."""
    
    def test_magata_escape_end_to_end(self, started_runtime):
        """Full escape scenario for Magata."""
        # Get Magata's quarters
        magata = None
        for room in started_runtime.system.sealed_rooms:
            if isinstance(room, MagataQuarters):
                magata = room
                break
        
        assert magata is not None
        assert magata.is_sealed
        assert magata.main_lock.is_locked()
        
        # Run to overflow
        started_runtime.run_to_overflow()
        
        # Verify escape
        assert magata.is_breached or magata.state == RoomState.ESCAPED
    
    def test_room_state_transitions(self, started_runtime):
        """Room should transition: SEALED → BREACHED → ESCAPED."""
        magata = None
        for room in started_runtime.system.sealed_rooms:
            if isinstance(room, MagataQuarters):
                magata = room
                break
        
        # Track states
        states = [magata.state]
        
        def on_state_change(room, old, new):
            states.append(new)
        
        magata.register_state_change_callback(on_state_change)
        
        # Run simulation
        started_runtime.run_to_overflow()
        
        # Should have SEALED → BREACHED at minimum
        assert RoomState.SEALED in states
        assert RoomState.BREACHED in states or RoomState.ESCAPED in states


# =============================================================================
# "Everything Becomes F" Verification Tests
# =============================================================================

class TestEverythingBecomesF:
    """Tests verification of 'Everything Becomes F' condition."""
    
    def test_final_state_verification(self, fresh_runtime):
        """Verify everything becomes F (0xFFFF → 0x0000)."""
        # Run complete simulation
        fresh_runtime.run()
        
        # Verify the condition
        verification = fresh_runtime.verify_everything_becomes_f()
        
        assert verification["everything_becomes_f"] is True
        assert verification["verification"]["counter_overflow_occurred"] is True
        assert verification["verification"]["system_is_down"] is True
    
    def test_0xFFFF_is_four_fs(self):
        """0xFFFF should be 'FFFF' - four Fs."""
        counter = UnsignedShortCounter(initial_value=0xFFFF)
        hex_value = counter.hex_value
        
        # Should contain exactly 4 Fs
        assert hex_value == "0xFFFF"
        assert hex_value.count('F') == 4
    
    def test_overflow_resets_to_zero(self):
        """After overflow, value should be 0x0000."""
        counter = UnsignedShortCounter(initial_value=0xFFFF)
        counter.increment()
        
        assert counter.value == 0
        assert counter.hex_value == "0x0000"
    
    def test_system_terminates_on_f(self, started_runtime):
        """System should terminate when everything becomes F."""
        started_runtime.run_to_overflow()
        
        assert started_runtime.system.state == SystemState.SYSTEM_DOWN
        assert started_runtime.is_completed


# =============================================================================
# Runtime Phase Tests
# =============================================================================

class TestRuntimePhases:
    """Tests runtime phase progression."""
    
    def test_all_phases_execute(self, fresh_runtime):
        """All phases should execute in order."""
        phase_history = []
        
        def on_phase_change(rt, old, new):
            phase_history.append(new)
        
        fresh_runtime.register_phase_change_callback(on_phase_change)
        
        # Run complete simulation
        fresh_runtime.run()
        
        # Should have all phases
        assert Phase.COLD_BOOT in phase_history
        assert Phase.KERNEL_ACCESS in phase_history
        assert Phase.IO_BOUNDARY in phase_history
        assert Phase.MEMORY_RECURSION in phase_history
        assert Phase.LOGIC_EXPLOSION in phase_history
    
    def test_phase_info_accuracy(self):
        """Phase info should have correct metadata."""
        for phase in Phase:
            if phase == Phase.TERMINATED:
                continue
            
            info = PHASE_INFO[phase]
            assert info.name_en != ""
            assert info.name_ja != ""
            assert info.hours_start >= 0
            assert info.hours_end >= info.hours_start
    
    def test_logic_explosion_triggers_completion(self, started_runtime):
        """LOGIC_EXPLOSION phase should complete simulation."""
        # Execute phases up to logic explosion
        started_runtime.execute_phase(Phase.COLD_BOOT)
        started_runtime.execute_phase(Phase.KERNEL_ACCESS)
        started_runtime.execute_phase(Phase.IO_BOUNDARY)
        started_runtime.execute_phase(Phase.MEMORY_RECURSION)
        started_runtime.execute_phase(Phase.LOGIC_EXPLOSION)
        
        assert started_runtime.is_completed
        assert started_runtime.current_phase == Phase.TERMINATED


# =============================================================================
# Full System State Tests
# =============================================================================

class TestFullSystemState:
    """Tests complete system state at various points."""
    
    def test_initial_system_state(self, fresh_runtime):
        """Initial state should be fully operational."""
        system = fresh_runtime.system
        
        # System not yet started
        assert system.state == SystemState.INITIALIZING
        
        # Counter at zero
        assert system.counter.value == 0
        
        # Locks engaged
        if system.lock_system.lock_count > 0:
            assert system.lock_system.all_locked()
    
    def test_mid_simulation_state(self, started_runtime):
        """State at mid-point of simulation."""
        # Fast forward to middle
        started_runtime.system.fast_forward(32000)  # About halfway
        
        # Should still be running
        assert started_runtime.system.state == SystemState.RUNNING
        
        # Counter should be at correct value
        assert started_runtime.system.counter.value == 32000
        
        # Locks should still be engaged
        assert not started_runtime.system.lock_system.failsafe_triggered
    
    def test_final_system_state(self, started_runtime):
        """Final state after complete simulation."""
        started_runtime.run_to_overflow()
        
        system = started_runtime.system
        
        # System down
        assert system.state == SystemState.SYSTEM_DOWN
        
        # Counter wrapped
        assert system.counter.overflow_count >= 1
        
        # Failsafe triggered
        assert system.lock_system.failsafe_triggered
        
        # All locks released
        assert system.lock_system.all_unlocked()
    
    def test_full_status_report(self, started_runtime):
        """Full status should contain all information."""
        started_runtime.run_to_overflow()
        
        status = started_runtime.get_full_status()
        
        # Runtime info
        assert "runtime" in status
        assert status["runtime"]["is_completed"] is True
        
        # System info
        assert "system" in status
        assert status["system"]["state"] == "SYSTEM_DOWN"
        
        # Counter info
        assert status["system"]["counter"]["overflows"] >= 1


# =============================================================================
# Event Complete Sequence Tests
# =============================================================================

class TestCompleteEventSequence:
    """Tests complete event sequence through simulation."""
    
    def test_full_event_log(self, started_runtime):
        """Capture and verify complete event log."""
        all_events = []
        
        def handler(event):
            all_events.append({
                "type": event.event_type.name,
                "source": event.source
            })
        
        started_runtime.system.event_bus.subscribe_all(handler)
        
        # Run simulation
        started_runtime.run_to_overflow()
        
        # Verify critical events occurred
        event_types = [e["type"] for e in all_events]
        
        # Must have these events
        critical_events = [
            "COUNTER_OVERFLOW",
            "FAILSAFE_TRIGGERED",
            "LOCKS_RELEASED",
            "SYSTEM_CRASH"
        ]
        
        for event_name in critical_events:
            assert event_name in event_types, f"Missing critical event: {event_name}"
    
    def test_event_order_integrity(self, started_runtime):
        """Events should occur in correct order."""
        event_sequence = []
        
        def handler(event):
            event_sequence.append(event.event_type)
        
        started_runtime.system.event_bus.subscribe_all(handler)
        started_runtime.run_to_overflow()
        
        # Find positions
        if EventType.COUNTER_OVERFLOW in event_sequence:
            overflow_pos = event_sequence.index(EventType.COUNTER_OVERFLOW)
            
            if EventType.FAILSAFE_TRIGGERED in event_sequence:
                failsafe_pos = event_sequence.index(EventType.FAILSAFE_TRIGGERED)
                assert overflow_pos < failsafe_pos
            
            if EventType.LOCKS_RELEASED in event_sequence:
                locks_pos = event_sequence.index(EventType.LOCKS_RELEASED)
                assert overflow_pos < locks_pos


# =============================================================================
# Novel Accuracy Tests
# =============================================================================

class TestNovelAccuracy:
    """Tests accuracy to the novel's plot details."""
    
    def test_counter_uses_unsigned_short(self):
        """Counter should use 16-bit unsigned range."""
        assert UnsignedShortCounter.MAX_VALUE == 0xFFFF
        assert UnsignedShortCounter.MAX_VALUE == 65535
    
    def test_overflow_mechanism_accurate(self):
        """Overflow should work like C unsigned short."""
        counter = UnsignedShortCounter(initial_value=0xFFFF)
        
        # In C: unsigned short x = 65535; x++; results in x = 0
        counter.increment()
        
        assert counter.value == 0
    
    def test_time_period_accurate(self):
        """Time to overflow should be ~7.5 years."""
        hours_to_overflow = 65536  # 0xFFFF + 1
        hours_per_year = 365.25 * 24
        years = hours_to_overflow / hours_per_year
        
        # Should be approximately 7.5 years
        assert 7.4 < years < 7.6
    
    def test_confinement_duration(self):
        """Magata was confined for 15 years."""
        assert MagataQuarters.CONFINEMENT_YEARS == 15


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
