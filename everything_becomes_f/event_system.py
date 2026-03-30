"""
event_system.py - Asynchronous Event System
=============================================

Implements a publish/subscribe event bus for loose coupling
between system components.

Events propagate through the system:
COUNTER_OVERFLOW → LOCKS_RELEASED → CAMERA_BLIND_SPOT → ROOM_BREACHED → SYSTEM_CRASH

This mirrors the novel's plot progression where one event
triggers the next in a chain reaction leading to escape.
"""

from enum import Enum, auto
from typing import Callable, List, Dict, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import time


class EventType(Enum):
    """Types of events in the Red Magic system."""
    
    # Core system events
    SYSTEM_INITIALIZED = auto()
    SYSTEM_STARTED = auto()
    SYSTEM_SHUTDOWN = auto()
    SYSTEM_CRASH = auto()
    
    # Counter events
    COUNTER_INCREMENT = auto()
    COUNTER_OVERFLOW = auto()      # Critical: triggers escape sequence
    COUNTER_RESET = auto()
    
    # Lock events
    LOCK_ENGAGED = auto()
    LOCK_RELEASED = auto()
    LOCKS_RELEASED = auto()        # All locks released (failsafe)
    FAILSAFE_TRIGGERED = auto()
    
    # Camera events
    CAMERA_RECORDING = auto()
    CAMERA_BLIND_SPOT = auto()     # 1-minute surveillance gap
    CLOCK_SYNC_ERROR = auto()
    
    # Room events
    ROOM_SEALED = auto()
    ROOM_BREACHED = auto()         # Security breach detected
    ROOM_ESCAPED = auto()          # Occupant escaped
    
    # Phase events (novel chapters mapped to system states)
    PHASE_TRANSITION = auto()
    PHASE_COMPLETED = auto()


@dataclass
class Event:
    """
    Represents an event in the system.
    
    Events are immutable records of what happened, when, and
    any associated data.
    """
    event_type: EventType
    timestamp: float = field(default_factory=time.time)
    source: str = "unknown"
    data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}
    
    @property
    def type_name(self) -> str:
        """Get event type as string."""
        return self.event_type.name
    
    def __repr__(self) -> str:
        return f"Event({self.event_type.name}, source={self.source})"


# Type alias for event handlers
EventHandler = Callable[[Event], None]


class EventBus:
    """
    Publish/Subscribe event bus for system events.
    
    Enables loose coupling between components:
    - Counter doesn't need to know about locks
    - Locks don't need to know about cameras
    - Components communicate through events
    
    Event chain for escape sequence:
    1. COUNTER_OVERFLOW - Counter reaches 0xFFFF + 1
    2. FAILSAFE_TRIGGERED - System detects anomaly
    3. LOCKS_RELEASED - All electromagnetic locks open
    4. CAMERA_BLIND_SPOT - Surveillance gap created
    5. ROOM_BREACHED - Sealed room compromised
    6. ROOM_ESCAPED - Occupant escapes
    7. SYSTEM_CRASH - System shuts down
    """
    
    def __init__(self, name: str = "EventBus"):
        """
        Initialize the event bus.
        
        Args:
            name: Name identifier for this event bus
        """
        self.name = name
        self._subscribers: Dict[EventType, List[EventHandler]] = defaultdict(list)
        self._all_subscribers: List[EventHandler] = []  # Handlers for all events
        self._event_history: List[Event] = []
        self._max_history: int = 1000
        self._paused: bool = False
    
    def subscribe(
        self, 
        event_type: EventType, 
        handler: EventHandler
    ) -> None:
        """
        Subscribe to a specific event type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Function to call when event occurs
        """
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)
    
    def subscribe_all(self, handler: EventHandler) -> None:
        """
        Subscribe to all events.
        
        Args:
            handler: Function to call for any event
        """
        if handler not in self._all_subscribers:
            self._all_subscribers.append(handler)
    
    def unsubscribe(
        self, 
        event_type: EventType, 
        handler: EventHandler
    ) -> bool:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Event type to unsubscribe from
            handler: Handler to remove
            
        Returns:
            True if handler was found and removed
        """
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
            return True
        return False
    
    def unsubscribe_all(self, handler: EventHandler) -> bool:
        """Unsubscribe from all events."""
        if handler in self._all_subscribers:
            self._all_subscribers.remove(handler)
            return True
        return False
    
    def publish(self, event: Event) -> int:
        """
        Publish an event to all subscribers.
        
        Args:
            event: Event to publish
            
        Returns:
            Number of handlers that received the event
        """
        if self._paused:
            return 0
        
        # Record in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        handlers_called = 0
        
        # Call specific subscribers
        for handler in self._subscribers[event.event_type]:
            handler(event)
            handlers_called += 1
        
        # Call all-event subscribers
        for handler in self._all_subscribers:
            handler(event)
            handlers_called += 1
        
        return handlers_called
    
    def emit(
        self, 
        event_type: EventType, 
        source: str = "unknown",
        **data
    ) -> Event:
        """
        Create and publish an event.
        
        Convenience method combining event creation and publishing.
        
        Args:
            event_type: Type of event
            source: Source component name
            **data: Additional event data
            
        Returns:
            The created and published event
        """
        event = Event(
            event_type=event_type,
            source=source,
            data=data
        )
        self.publish(event)
        return event
    
    def get_history(
        self, 
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        Get event history.
        
        Args:
            event_type: Filter by event type (None for all)
            limit: Maximum events to return
            
        Returns:
            List of events (most recent first)
        """
        if event_type is None:
            return self._event_history[-limit:][::-1]
        
        filtered = [e for e in self._event_history if e.event_type == event_type]
        return filtered[-limit:][::-1]
    
    def get_event_count(self, event_type: Optional[EventType] = None) -> int:
        """Get count of events in history."""
        if event_type is None:
            return len(self._event_history)
        return sum(1 for e in self._event_history if e.event_type == event_type)
    
    def has_event(self, event_type: EventType) -> bool:
        """Check if event type has occurred."""
        return any(e.event_type == event_type for e in self._event_history)
    
    def pause(self) -> None:
        """Pause event publishing."""
        self._paused = True
    
    def resume(self) -> None:
        """Resume event publishing."""
        self._paused = False
    
    @property
    def is_paused(self) -> bool:
        """Check if event bus is paused."""
        return self._paused
    
    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()
    
    def clear_subscribers(self) -> None:
        """Remove all subscribers."""
        self._subscribers.clear()
        self._all_subscribers.clear()
    
    def get_subscriber_count(self, event_type: Optional[EventType] = None) -> int:
        """Get count of subscribers."""
        if event_type is None:
            total = sum(len(handlers) for handlers in self._subscribers.values())
            return total + len(self._all_subscribers)
        return len(self._subscribers[event_type])
    
    def get_status(self) -> dict:
        """Get event bus status."""
        return {
            "name": self.name,
            "paused": self._paused,
            "event_count": len(self._event_history),
            "subscriber_count": self.get_subscriber_count(),
            "max_history": self._max_history
        }
    
    def __repr__(self) -> str:
        return f"EventBus(name={self.name}, events={len(self._event_history)})"


def create_escape_event_chain(event_bus: EventBus, hour: int) -> List[Event]:
    """
    Create the canonical event chain for escape sequence.
    
    This is the event sequence that occurs when counter overflows:
    1. Counter overflow detected
    2. Failsafe triggered
    3. All locks released
    4. Camera blind spot (optional)
    5. Room breached
    6. Escape complete
    7. System crash
    
    Args:
        event_bus: Event bus to publish events on
        hour: System hour when sequence started
        
    Returns:
        List of events in the chain
    """
    events = []
    
    events.append(event_bus.emit(
        EventType.COUNTER_OVERFLOW,
        source="UnsignedShortCounter",
        hour=hour,
        value=0,
        hex_value="0x0000"
    ))
    
    events.append(event_bus.emit(
        EventType.FAILSAFE_TRIGGERED,
        source="RedMagicSystem",
        hour=hour,
        reason="counter_overflow"
    ))
    
    events.append(event_bus.emit(
        EventType.LOCKS_RELEASED,
        source="LockSystem",
        hour=hour,
        locks_count=1
    ))
    
    events.append(event_bus.emit(
        EventType.ROOM_BREACHED,
        source="SealedRoom",
        hour=hour,
        room_id="magata_quarters"
    ))
    
    events.append(event_bus.emit(
        EventType.ROOM_ESCAPED,
        source="SealedRoom",
        hour=hour,
        room_id="magata_quarters"
    ))
    
    events.append(event_bus.emit(
        EventType.SYSTEM_CRASH,
        source="RedMagicSystem",
        hour=hour,
        reason="escape_sequence_complete"
    ))
    
    return events
