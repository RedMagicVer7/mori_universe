"""
runtime.py - Everything Becomes F Runtime Engine
==================================================

Maps the novel's 11 episodes to system state transitions,
simulating the complete narrative arc from system boot
to final "Everything Becomes F" conclusion.

The novel's episodes (色彩 - colors) map to system phases:
- Phase 1 (Cold Boot): White Conference, Amber Court
- Phase 2 (Kernel Access): Magic Red, Seven Diamonds
- Phase 3 (I/O Boundary): Blue Water, Yellow Edge, Silver Boundary
- Phase 4 (Memory Recursion): Green Origin, Purple Memory
- Phase 5 (Logic Explosion): Deep Red Square, Everything Becomes F

The runtime provides a high-level API to execute the complete
simulation from start to finish.
"""

from enum import Enum, auto
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field

from .counter import UnsignedShortCounter
from .electromagnetic_lock import LockSystem
from .security_camera import SecurityCamera, ClockSyncVulnerability
from .sealed_room import MagataQuarters, RoomState
from .event_system import EventBus, EventType, Event
from .red_magic_system import RedMagicSystem, SystemState, create_standard_facility


class Phase(Enum):
    """
    Simulation phases mapped to novel episodes.
    
    Each phase represents a stage in the system lifecycle,
    corresponding to the novel's color-named chapters.
    """
    
    # Phase 1: Cold Boot - System initialization
    # Episodes: White Conference (白い会議), Amber Court (琥珀色の法廷)
    COLD_BOOT = auto()
    
    # Phase 2: Kernel Access - Core system running
    # Episodes: Magic Red (魔術の赤), Seven Diamonds (7つのダイヤモンド)
    KERNEL_ACCESS = auto()
    
    # Phase 3: I/O Boundary - Time passing, approaching limit
    # Episodes: Blue Water (青い水), Yellow Edge (黄色の縁), Silver Boundary (銀色の境界)
    IO_BOUNDARY = auto()
    
    # Phase 4: Memory Recursion - Near overflow, recursion
    # Episodes: Green Origin (緑の原点), Purple Memory (紫色の記憶)
    MEMORY_RECURSION = auto()
    
    # Phase 5: Logic Explosion - Overflow, escape, system crash
    # Episodes: Deep Red Square (深紅の広場), Everything Becomes F (すべてがFになる)
    LOGIC_EXPLOSION = auto()
    
    # Terminal state
    TERMINATED = auto()


@dataclass
class PhaseInfo:
    """Information about a simulation phase."""
    phase: Phase
    name_en: str
    name_ja: str
    episodes: List[str]
    description: str
    hours_start: int = 0
    hours_end: int = 0


# Phase metadata
PHASE_INFO: Dict[Phase, PhaseInfo] = {
    Phase.COLD_BOOT: PhaseInfo(
        phase=Phase.COLD_BOOT,
        name_en="Cold Boot",
        name_ja="コールドブート",
        episodes=["White Conference (白い会議)", "Amber Court (琥珀色の法廷)"],
        description="System initialization. Dr. Magata begins her confinement.",
        hours_start=0,
        hours_end=1000
    ),
    Phase.KERNEL_ACCESS: PhaseInfo(
        phase=Phase.KERNEL_ACCESS,
        name_en="Kernel Access",
        name_ja="カーネルアクセス",
        episodes=["Magic Red (魔術の赤)", "Seven Diamonds (7つのダイヤモンド)"],
        description="Core system running. The bug is planted in Red Magic.",
        hours_start=1000,
        hours_end=20000
    ),
    Phase.IO_BOUNDARY: PhaseInfo(
        phase=Phase.IO_BOUNDARY,
        name_en="I/O Boundary",
        name_ja="入出力境界",
        episodes=["Blue Water (青い水)", "Yellow Edge (黄色の縁)", "Silver Boundary (銀色の境界)"],
        description="Time passes. Counter approaches half-way point.",
        hours_start=20000,
        hours_end=45000
    ),
    Phase.MEMORY_RECURSION: PhaseInfo(
        phase=Phase.MEMORY_RECURSION,
        name_en="Memory Recursion",
        name_ja="記憶の再帰",
        episodes=["Green Origin (緑の原点)", "Purple Memory (紫色の記憶)"],
        description="Near overflow. Memory and time recursive patterns emerge.",
        hours_start=45000,
        hours_end=65534
    ),
    Phase.LOGIC_EXPLOSION: PhaseInfo(
        phase=Phase.LOGIC_EXPLOSION,
        name_en="Logic Explosion",
        name_ja="論理の爆発",
        episodes=["Deep Red Square (深紅の広場)", "Everything Becomes F (すべてがFになる)"],
        description="Counter reaches 0xFFFF. Overflow. Escape. System crash.",
        hours_start=65534,
        hours_end=65536
    ),
    Phase.TERMINATED: PhaseInfo(
        phase=Phase.TERMINATED,
        name_en="Terminated",
        name_ja="終了",
        episodes=[],
        description="System has crashed. Everything has become F.",
        hours_start=65536,
        hours_end=65536
    )
}


@dataclass
class RuntimeState:
    """Current state of the runtime."""
    phase: Phase
    system_state: SystemState
    counter_value: int
    counter_hex: str
    is_completed: bool
    events: List[str] = field(default_factory=list)


class EverythingBecomesFRuntime:
    """
    Runtime engine for the Everything Becomes F simulation.
    
    Provides high-level API to run the complete simulation:
    - Phase-by-phase execution
    - Full 15-year simulation
    - Event monitoring
    - State inspection
    
    Usage:
        runtime = EverythingBecomesFRuntime()
        runtime.run()  # Execute full simulation
        
        # Or phase by phase:
        runtime.execute_phase(Phase.COLD_BOOT)
        runtime.execute_phase(Phase.KERNEL_ACCESS)
        # ...
    """
    
    def __init__(self, system: Optional[RedMagicSystem] = None):
        """
        Initialize the runtime.
        
        Args:
            system: RedMagicSystem instance (created if not provided)
        """
        self._system: RedMagicSystem = system or create_standard_facility()
        self._current_phase: Phase = Phase.COLD_BOOT
        self._phase_history: List[Phase] = []
        self._is_running: bool = False
        self._is_completed: bool = False
        self._on_phase_change_callbacks: List[Callable] = []
        self._on_completion_callbacks: List[Callable] = []
        
        # Get Magata's quarters from system
        self._magata_quarters: Optional[MagataQuarters] = None
        for room in self._system.sealed_rooms:
            if isinstance(room, MagataQuarters):
                self._magata_quarters = room
                break
    
    @property
    def system(self) -> RedMagicSystem:
        """Get the underlying Red Magic system."""
        return self._system
    
    @property
    def current_phase(self) -> Phase:
        """Get current simulation phase."""
        return self._current_phase
    
    @property
    def phase_info(self) -> PhaseInfo:
        """Get current phase information."""
        return PHASE_INFO[self._current_phase]
    
    @property
    def is_running(self) -> bool:
        """Check if simulation is running."""
        return self._is_running
    
    @property
    def is_completed(self) -> bool:
        """Check if simulation has completed."""
        return self._is_completed
    
    @property
    def counter_value(self) -> int:
        """Get current counter value."""
        return self._system.counter.value
    
    @property
    def counter_hex(self) -> str:
        """Get current counter value in hex."""
        return self._system.counter.hex_value
    
    def start(self) -> None:
        """Start the simulation."""
        if self._is_running:
            return
        
        self._is_running = True
        self._system.start()
        self._transition_phase(Phase.COLD_BOOT)
    
    def execute_phase(self, phase: Phase) -> bool:
        """
        Execute a specific phase.
        
        Args:
            phase: Phase to execute
            
        Returns:
            True if phase completed successfully
        """
        if self._is_completed:
            return False
        
        if not self._is_running:
            self.start()
        
        self._transition_phase(phase)
        
        info = PHASE_INFO[phase]
        
        # Calculate hours to advance
        current_hour = self._system.counter.value
        if current_hour < info.hours_start:
            # Need to fast forward to phase start
            hours_to_start = info.hours_start - current_hour
            self._system.fast_forward(hours_to_start)
        
        # Fast forward through the phase
        hours_in_phase = info.hours_end - max(current_hour, info.hours_start)
        if hours_in_phase > 0:
            self._system.fast_forward(hours_in_phase)
        
        # Check if this triggers completion
        if phase == Phase.LOGIC_EXPLOSION:
            self._complete_simulation()
        
        return True
    
    def advance_to_next_phase(self) -> Optional[Phase]:
        """
        Advance to the next phase.
        
        Returns:
            The new phase, or None if already completed
        """
        if self._is_completed:
            return None
        
        phases = list(Phase)
        current_index = phases.index(self._current_phase)
        
        if current_index < len(phases) - 1:
            next_phase = phases[current_index + 1]
            self.execute_phase(next_phase)
            return next_phase
        
        return None
    
    def run(self) -> RuntimeState:
        """
        Execute the complete simulation.
        
        Runs through all phases from Cold Boot to Logic Explosion,
        simulating the full ~7.5 year journey to "Everything Becomes F".
        
        Returns:
            Final runtime state
        """
        self.start()
        
        # Execute all phases in order
        for phase in Phase:
            if phase == Phase.TERMINATED:
                break
            self.execute_phase(phase)
        
        return self.get_state()
    
    def run_to_overflow(self) -> RuntimeState:
        """
        Fast forward directly to overflow.
        
        Skips intermediate phases and goes straight to 0xFFFF → 0x0000.
        
        Returns:
            Final runtime state
        """
        if not self._is_running:
            self.start()
        
        # Fast forward to just before overflow
        hours_to_overflow = self._system.counter.hours_until_overflow()
        self._system.fast_forward(hours_to_overflow)
        
        self._transition_phase(Phase.LOGIC_EXPLOSION)
        
        # Complete the simulation
        self._complete_simulation()
        
        return self.get_state()
    
    def _transition_phase(self, new_phase: Phase) -> None:
        """Transition to a new phase."""
        old_phase = self._current_phase
        self._current_phase = new_phase
        self._phase_history.append(new_phase)
        
        # Emit phase transition event
        self._system.event_bus.emit(
            EventType.PHASE_TRANSITION,
            source="Runtime",
            old_phase=old_phase.name,
            new_phase=new_phase.name,
            hour=self._system.counter.value
        )
        
        for callback in self._on_phase_change_callbacks:
            callback(self, old_phase, new_phase)
    
    def _complete_simulation(self) -> None:
        """Mark simulation as completed."""
        self._is_completed = True
        self._is_running = False
        self._current_phase = Phase.TERMINATED
        
        # Handle escape if quarters exist
        if self._magata_quarters and self._magata_quarters.is_breached:
            self._magata_quarters.escape(self._system.counter.value)
            self._system.event_bus.emit(
                EventType.ROOM_ESCAPED,
                source="MagataQuarters",
                hour=self._system.counter.value
            )
        
        for callback in self._on_completion_callbacks:
            callback(self)
    
    def get_state(self) -> RuntimeState:
        """Get current runtime state."""
        recent_events = [
            e.type_name for e in self._system.event_bus.get_history(limit=10)
        ]
        
        return RuntimeState(
            phase=self._current_phase,
            system_state=self._system.state,
            counter_value=self._system.counter.value,
            counter_hex=self._system.counter.hex_value,
            is_completed=self._is_completed,
            events=recent_events
        )
    
    def get_full_status(self) -> Dict[str, Any]:
        """Get comprehensive status."""
        return {
            "runtime": {
                "phase": self._current_phase.name,
                "phase_info": {
                    "name_en": self.phase_info.name_en,
                    "name_ja": self.phase_info.name_ja,
                    "episodes": self.phase_info.episodes,
                    "description": self.phase_info.description
                },
                "is_running": self._is_running,
                "is_completed": self._is_completed,
                "phase_history": [p.name for p in self._phase_history]
            },
            "system": self._system.get_status(),
            "magata_quarters": (
                self._magata_quarters.get_status() 
                if self._magata_quarters else None
            )
        }
    
    def register_phase_change_callback(self, callback: Callable) -> None:
        """Register callback for phase changes."""
        self._on_phase_change_callbacks.append(callback)
    
    def register_completion_callback(self, callback: Callable) -> None:
        """Register callback for simulation completion."""
        self._on_completion_callbacks.append(callback)
    
    def verify_everything_becomes_f(self) -> Dict[str, Any]:
        """
        Verify that "Everything Becomes F" condition is met.
        
        The condition:
        - Counter reached 0xFFFF (65535)
        - Then overflowed to 0x0000
        - System is down
        - Room is escaped (if applicable)
        
        Returns:
            Verification results dictionary
        """
        counter = self._system.counter
        
        # Check if overflow occurred
        overflow_occurred = counter.overflow_count > 0
        
        # Check system state
        system_down = self._system.state == SystemState.SYSTEM_DOWN
        
        # Check escape
        escaped = False
        if self._magata_quarters:
            escaped = self._magata_quarters.state == RoomState.ESCAPED
        
        # The final state after overflow is 0x0000
        # But we want to verify the journey reached 0xFFFF first
        everything_is_f = overflow_occurred and system_down
        
        return {
            "everything_becomes_f": everything_is_f,
            "verification": {
                "counter_overflow_occurred": overflow_occurred,
                "overflow_count": counter.overflow_count,
                "system_state": self._system.state.name,
                "system_is_down": system_down,
                "escaped": escaped,
                "final_counter_value": counter.value,
                "final_counter_hex": counter.hex_value
            },
            "meaning": (
                "0xFFFF (65535) represents the maximum value. "
                "When incremented, it overflows to 0x0000. "
                "In hexadecimal, F is the highest digit. "
                "Everything becoming F means reaching the limit, "
                "then returning to zero - the perfect cycle."
            )
        }
    
    def reset(self) -> None:
        """Reset the runtime to initial state."""
        self._system.reset()
        self._current_phase = Phase.COLD_BOOT
        self._phase_history.clear()
        self._is_running = False
        self._is_completed = False
    
    def __repr__(self) -> str:
        return (
            f"EverythingBecomesFRuntime("
            f"phase={self._current_phase.name}, "
            f"counter={self._system.counter.hex_value}, "
            f"completed={self._is_completed})"
        )
