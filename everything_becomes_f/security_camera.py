"""
security_camera.py - Security Camera and Monitoring System
============================================================

Models the security camera system in the Magata Research Facility.
Includes the critical clock synchronization vulnerability that
creates a one-minute blind spot during Red Magic system reinstallation.

The vulnerability: When Red Magic reinstalls, there's a 1-minute
time drift. The system overwrites that minute's recording,
creating a surveillance blind spot - the perfect window for escape.
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta


class CameraState(Enum):
    """States of a security camera."""
    ACTIVE = auto()       # Camera recording normally
    INACTIVE = auto()     # Camera powered off
    BLIND_SPOT = auto()   # Recording but creating blind spot
    MALFUNCTIONING = auto()


@dataclass
class VideoSegment:
    """Represents a one-minute video recording segment."""
    timestamp: int  # Unix timestamp (hour * 60 + minute)
    minute_index: int  # Minute within the hour (0-59)
    hour_index: int  # Hour index
    is_overwritten: bool = False
    data_exists: bool = True
    
    @property
    def is_blind_spot(self) -> bool:
        """Check if this segment is a blind spot (overwritten)."""
        return self.is_overwritten or not self.data_exists


@dataclass
class SecurityCamera:
    """
    Represents a security camera in the facility.
    
    Records video organized by minute segments.
    24/7 continuous recording with footage organized by minute.
    
    Attributes:
        camera_id: Unique identifier
        location: Physical location
        state: Current camera state
    """
    camera_id: str
    location: str = "Unknown"
    state: CameraState = CameraState.ACTIVE
    _recordings: Dict[int, VideoSegment] = field(default_factory=dict)
    _current_minute: int = 0
    _on_blind_spot_callbacks: List[Callable] = field(default_factory=list)
    
    def __post_init__(self):
        if self._recordings is None:
            self._recordings = {}
        if self._on_blind_spot_callbacks is None:
            self._on_blind_spot_callbacks = []
    
    def record_minute(self, hour: int, minute: int) -> VideoSegment:
        """
        Record a one-minute video segment.
        
        Args:
            hour: Hour index (system runtime hours)
            minute: Minute within the hour (0-59)
            
        Returns:
            The created video segment
        """
        timestamp = hour * 60 + minute
        segment = VideoSegment(
            timestamp=timestamp,
            minute_index=minute,
            hour_index=hour,
            is_overwritten=False,
            data_exists=True
        )
        self._recordings[timestamp] = segment
        self._current_minute = timestamp
        return segment
    
    def get_recording(self, hour: int, minute: int) -> Optional[VideoSegment]:
        """Get a specific minute's recording."""
        timestamp = hour * 60 + minute
        return self._recordings.get(timestamp)
    
    def overwrite_recording(self, hour: int, minute: int) -> Optional[VideoSegment]:
        """
        Overwrite a recording (creates blind spot).
        
        This happens during clock sync vulnerability exploit.
        
        Args:
            hour: Hour index
            minute: Minute within the hour
            
        Returns:
            The overwritten segment, or None if not found
        """
        timestamp = hour * 60 + minute
        if timestamp in self._recordings:
            self._recordings[timestamp].is_overwritten = True
            self._recordings[timestamp].data_exists = False
            self._notify_blind_spot(timestamp)
            return self._recordings[timestamp]
        return None
    
    def create_blind_spot(self, hour: int, minute: int) -> VideoSegment:
        """
        Explicitly create a blind spot at specified time.
        
        Args:
            hour: Hour index
            minute: Minute within hour
            
        Returns:
            The blind spot segment
        """
        timestamp = hour * 60 + minute
        segment = VideoSegment(
            timestamp=timestamp,
            minute_index=minute,
            hour_index=hour,
            is_overwritten=True,
            data_exists=False
        )
        self._recordings[timestamp] = segment
        self._notify_blind_spot(timestamp)
        return segment
    
    def get_blind_spots(self) -> List[VideoSegment]:
        """Get all blind spot segments."""
        return [seg for seg in self._recordings.values() if seg.is_blind_spot]
    
    def has_blind_spots(self) -> bool:
        """Check if any blind spots exist."""
        return any(seg.is_blind_spot for seg in self._recordings.values())
    
    def get_recording_count(self) -> int:
        """Get total number of recorded segments."""
        return len(self._recordings)
    
    def get_valid_recording_count(self) -> int:
        """Get number of valid (non-blind-spot) recordings."""
        return sum(1 for seg in self._recordings.values() if not seg.is_blind_spot)
    
    def register_blind_spot_callback(self, callback: Callable) -> None:
        """Register callback for blind spot creation."""
        self._on_blind_spot_callbacks.append(callback)
    
    def _notify_blind_spot(self, timestamp: int) -> None:
        """Notify callbacks of blind spot creation."""
        for callback in self._on_blind_spot_callbacks:
            callback(self, timestamp)
    
    def activate(self) -> None:
        """Activate the camera."""
        self.state = CameraState.ACTIVE
    
    def deactivate(self) -> None:
        """Deactivate the camera."""
        self.state = CameraState.INACTIVE
    
    def is_active(self) -> bool:
        """Check if camera is active."""
        return self.state == CameraState.ACTIVE
    
    def __repr__(self) -> str:
        return f"SecurityCamera(id={self.camera_id}, state={self.state.name})"


class ClockSyncVulnerability:
    """
    Models the clock synchronization vulnerability in Red Magic.
    
    When Red Magic system reinstalls/reboots:
    1. System clock has 1-minute drift
    2. During sync, the current minute's recording is overwritten
    3. This creates a surveillance blind spot
    4. The blind spot can be exploited for undetected movement
    
    This is a key element of Dr. Magata's escape plan:
    The 1-minute blind spot allows her to move without being recorded.
    """
    
    # Time drift during Red Magic reinstallation (1 minute)
    DRIFT_MINUTES = 1
    
    def __init__(self, camera_system: Optional[List[SecurityCamera]] = None):
        """
        Initialize the vulnerability model.
        
        Args:
            camera_system: List of cameras affected by this vulnerability
        """
        self._cameras: List[SecurityCamera] = camera_system or []
        self._exploited: bool = False
        self._blind_spot_hour: Optional[int] = None
        self._blind_spot_minute: Optional[int] = None
    
    def add_camera(self, camera: SecurityCamera) -> None:
        """Add a camera to the vulnerable system."""
        self._cameras.append(camera)
    
    @property
    def cameras(self) -> List[SecurityCamera]:
        """Get all cameras in the vulnerable system."""
        return self._cameras.copy()
    
    @property
    def is_exploited(self) -> bool:
        """Check if vulnerability has been exploited."""
        return self._exploited
    
    @property
    def blind_spot_time(self) -> Optional[tuple]:
        """Get the blind spot time as (hour, minute) tuple."""
        if self._blind_spot_hour is not None:
            return (self._blind_spot_hour, self._blind_spot_minute)
        return None
    
    def exploit(self, current_hour: int, current_minute: int) -> int:
        """
        Exploit the vulnerability to create blind spots.
        
        Called when Red Magic system reinstalls.
        Creates 1-minute blind spot on all cameras.
        
        Args:
            current_hour: Current hour index
            current_minute: Current minute (0-59)
            
        Returns:
            Number of cameras affected
        """
        self._exploited = True
        self._blind_spot_hour = current_hour
        self._blind_spot_minute = current_minute
        
        affected = 0
        for camera in self._cameras:
            if camera.is_active():
                camera.create_blind_spot(current_hour, current_minute)
                affected += 1
        
        return affected
    
    def simulate_reinstall(self, current_hour: int, current_minute: int) -> dict:
        """
        Simulate Red Magic reinstallation process.
        
        During reinstallation:
        1. System temporarily goes down
        2. Clock drift occurs (1 minute)
        3. Recording overlap creates blind spot
        
        Args:
            current_hour: Current system hour
            current_minute: Current minute
            
        Returns:
            Dictionary with simulation results
        """
        affected_cameras = self.exploit(current_hour, current_minute)
        
        return {
            "reinstall_triggered": True,
            "clock_drift_minutes": self.DRIFT_MINUTES,
            "blind_spot_created": True,
            "blind_spot_time": (current_hour, current_minute),
            "affected_cameras": affected_cameras,
            "total_cameras": len(self._cameras)
        }
    
    def get_status(self) -> dict:
        """Get vulnerability status."""
        return {
            "exploited": self._exploited,
            "cameras_count": len(self._cameras),
            "blind_spot_time": self.blind_spot_time,
            "drift_minutes": self.DRIFT_MINUTES
        }
    
    def reset(self) -> None:
        """Reset the vulnerability state."""
        self._exploited = False
        self._blind_spot_hour = None
        self._blind_spot_minute = None
    
    def __repr__(self) -> str:
        return f"ClockSyncVulnerability(exploited={self._exploited}, cameras={len(self._cameras)})"
