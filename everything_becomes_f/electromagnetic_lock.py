"""
electromagnetic_lock.py - Electromagnetic Lock Control System
===============================================================

Models the electromagnetic locks in the Magata Research Facility.
These locks are fail-safe: they remain locked when powered,
and unlock when power is cut or when system overflow occurs.

When the UnsignedShortCounter overflows, all locks release simultaneously.
"""

from enum import Enum, auto
from typing import List, Optional, Callable
from dataclasses import dataclass, field


class LockState(Enum):
    """States of an electromagnetic lock."""
    LOCKED = auto()      # Normal operation - power on, door sealed
    UNLOCKED = auto()    # Power cut or failsafe triggered
    MALFUNCTIONING = auto()  # Error state


@dataclass
class ElectromagneticLock:
    """
    Represents a single electromagnetic lock.
    
    Electromagnetic locks work on fail-safe principle:
    - Power ON = Lock engaged (door sealed)
    - Power OFF = Lock released (door opens)
    
    This is a security feature: power failure = escape possible.
    Dr. Magata exploited this by causing system overflow = power reset.
    
    Attributes:
        lock_id: Unique identifier for this lock
        location: Physical location description
        is_powered: Whether the lock has power
        state: Current lock state
    """
    lock_id: str
    location: str = "Unknown"
    is_powered: bool = True
    state: LockState = LockState.LOCKED
    _on_state_change_callbacks: List[Callable] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize callback list if needed."""
        if self._on_state_change_callbacks is None:
            self._on_state_change_callbacks = []
    
    def power_on(self) -> None:
        """Apply power to the lock (engages lock)."""
        self.is_powered = True
        old_state = self.state
        self.state = LockState.LOCKED
        if old_state != self.state:
            self._notify_state_change(old_state, self.state)
    
    def power_off(self) -> None:
        """Cut power to the lock (releases lock)."""
        self.is_powered = False
        old_state = self.state
        self.state = LockState.UNLOCKED
        if old_state != self.state:
            self._notify_state_change(old_state, self.state)
    
    def trigger_failsafe(self) -> None:
        """
        Trigger failsafe mechanism.
        
        Called when system overflow occurs.
        Immediately unlocks regardless of power state.
        """
        old_state = self.state
        self.is_powered = False
        self.state = LockState.UNLOCKED
        if old_state != self.state:
            self._notify_state_change(old_state, self.state)
    
    def set_malfunction(self) -> None:
        """Put lock into malfunction state."""
        old_state = self.state
        self.state = LockState.MALFUNCTIONING
        if old_state != self.state:
            self._notify_state_change(old_state, self.state)
    
    def is_locked(self) -> bool:
        """Check if the lock is currently engaged."""
        return self.state == LockState.LOCKED
    
    def is_unlocked(self) -> bool:
        """Check if the lock is currently released."""
        return self.state == LockState.UNLOCKED
    
    def register_state_change_callback(self, callback: Callable) -> None:
        """Register callback for state changes."""
        self._on_state_change_callbacks.append(callback)
    
    def _notify_state_change(self, old_state: LockState, new_state: LockState) -> None:
        """Notify all registered callbacks of state change."""
        for callback in self._on_state_change_callbacks:
            callback(self, old_state, new_state)
    
    def __repr__(self) -> str:
        return f"ElectromagneticLock(id={self.lock_id}, state={self.state.name})"


class LockSystem:
    """
    Manages multiple electromagnetic locks in the facility.
    
    The LockSystem coordinates all locks and can trigger
    a global failsafe that opens all locks simultaneously.
    
    In the novel, when counter overflow occurs:
    1. Red Magic system detects anomaly
    2. Failsafe triggers
    3. ALL electromagnetic locks release
    4. Sealed room becomes accessible
    """
    
    def __init__(self, name: str = "Magata Facility Lock System"):
        """
        Initialize the lock system.
        
        Args:
            name: Name identifier for this lock system
        """
        self.name = name
        self._locks: List[ElectromagneticLock] = []
        self._failsafe_triggered: bool = False
        self._on_failsafe_callbacks: List[Callable[['LockSystem'], None]] = []
    
    def add_lock(self, lock: ElectromagneticLock) -> None:
        """Add a lock to the system."""
        self._locks.append(lock)
    
    def create_lock(self, lock_id: str, location: str = "Unknown") -> ElectromagneticLock:
        """
        Create and add a new lock to the system.
        
        Args:
            lock_id: Unique identifier for the lock
            location: Physical location description
            
        Returns:
            The newly created lock
        """
        lock = ElectromagneticLock(lock_id=lock_id, location=location)
        self.add_lock(lock)
        return lock
    
    def remove_lock(self, lock_id: str) -> Optional[ElectromagneticLock]:
        """Remove a lock from the system by ID."""
        for i, lock in enumerate(self._locks):
            if lock.lock_id == lock_id:
                return self._locks.pop(i)
        return None
    
    def get_lock(self, lock_id: str) -> Optional[ElectromagneticLock]:
        """Get a lock by its ID."""
        for lock in self._locks:
            if lock.lock_id == lock_id:
                return lock
        return None
    
    @property
    def locks(self) -> List[ElectromagneticLock]:
        """Get all locks in the system."""
        return self._locks.copy()
    
    @property
    def lock_count(self) -> int:
        """Get the number of locks in the system."""
        return len(self._locks)
    
    @property
    def locked_count(self) -> int:
        """Get the number of currently locked locks."""
        return sum(1 for lock in self._locks if lock.is_locked())
    
    @property
    def unlocked_count(self) -> int:
        """Get the number of currently unlocked locks."""
        return sum(1 for lock in self._locks if lock.is_unlocked())
    
    @property
    def failsafe_triggered(self) -> bool:
        """Check if failsafe has been triggered."""
        return self._failsafe_triggered
    
    def all_locked(self) -> bool:
        """Check if all locks are in locked state."""
        return all(lock.is_locked() for lock in self._locks)
    
    def all_unlocked(self) -> bool:
        """Check if all locks are in unlocked state."""
        return all(lock.is_unlocked() for lock in self._locks)
    
    def trigger_global_failsafe(self) -> int:
        """
        Trigger failsafe on ALL locks in the system.
        
        This is called when counter overflow occurs.
        All electromagnetic locks release simultaneously.
        
        Returns:
            Number of locks that were unlocked
        """
        self._failsafe_triggered = True
        unlocked_count = 0
        
        for lock in self._locks:
            if lock.is_locked():
                lock.trigger_failsafe()
                unlocked_count += 1
        
        # Notify callbacks
        for callback in self._on_failsafe_callbacks:
            callback(self)
        
        return unlocked_count
    
    def power_on_all(self) -> None:
        """Apply power to all locks (engage all)."""
        for lock in self._locks:
            lock.power_on()
    
    def power_off_all(self) -> None:
        """Cut power to all locks (release all)."""
        for lock in self._locks:
            lock.power_off()
    
    def register_failsafe_callback(self, callback: Callable[['LockSystem'], None]) -> None:
        """Register callback for failsafe trigger event."""
        self._on_failsafe_callbacks.append(callback)
    
    def reset(self) -> None:
        """Reset the system to initial state."""
        self._failsafe_triggered = False
        self.power_on_all()
    
    def get_status(self) -> dict:
        """Get system status as dictionary."""
        return {
            "name": self.name,
            "total_locks": self.lock_count,
            "locked": self.locked_count,
            "unlocked": self.unlocked_count,
            "failsafe_triggered": self._failsafe_triggered,
        }
    
    def __repr__(self) -> str:
        return f"LockSystem(name={self.name}, locks={self.lock_count}, failsafe={self._failsafe_triggered})"
