"""
Everything Becomes F (すべてがFになる / The Perfect Insider)
============================================================

A system simulation based on Hiroshi Mori's novel.

The core puzzle: Genius programmer Dr. Shiki Magata was confined in a sealed
research facility for 15 years. She planted a software bug in the Red Magic
security system - using a 16-bit unsigned short integer for the timer.
Maximum value: 65535 (0xFFFF). Incrementing by 1 each hour, after ~7.5 years
(65535 hours), integer overflow occurs, all electromagnetic locks open,
enabling the perfect escape from the sealed room.

"Everything Becomes F" - In hexadecimal, 65535 = 0xFFFF (four Fs).
When the system reaches its limit, everything returns to zero.
"""

from .counter import UnsignedShortCounter
from .electromagnetic_lock import ElectromagneticLock, LockSystem
from .security_camera import SecurityCamera, ClockSyncVulnerability
from .sealed_room import SealedRoom, MagataQuarters, RoomState
from .event_system import EventBus, EventType
from .red_magic_system import RedMagicSystem, SystemState
from .runtime import EverythingBecomesFRuntime, Phase

__version__ = "1.0.0"
__author__ = "Mori Universe Project"

__all__ = [
    "UnsignedShortCounter",
    "ElectromagneticLock",
    "LockSystem",
    "SecurityCamera",
    "ClockSyncVulnerability",
    "SealedRoom",
    "MagataQuarters",
    "RoomState",
    "EventBus",
    "EventType",
    "RedMagicSystem",
    "SystemState",
    "EverythingBecomesFRuntime",
    "Phase",
]
