"""
counter.py - 16-bit Unsigned Short Integer Counter
===================================================

Simulates the C language unsigned short (0-65535) behavior.
This is the core of Dr. Magata's escape mechanism.

When the counter reaches 0xFFFF (65535) and increments by 1,
it overflows back to 0x0000, triggering the failsafe mechanism.
"""

from typing import Callable, List, Optional


class UnsignedShortCounter:
    """
    Simulates C language unsigned short (0-65535).
    
    The counter increments hourly. After 65535 hours (~7.5 years),
    overflow occurs and the value wraps to zero.
    
    65535 hours = 2730.625 days = ~7.48 years
    
    Attributes:
        MAX_VALUE: Maximum value before overflow (0xFFFF = 65535)
        HOURS_PER_YEAR: Average hours per year (365.25 * 24)
    """
    
    MAX_VALUE = 0xFFFF  # 65535
    HOURS_PER_YEAR = 365.25 * 24  # 8766 hours
    
    def __init__(self, initial_value: int = 0):
        """
        Initialize the counter.
        
        Args:
            initial_value: Starting value (0-65535), default 0
        """
        if not 0 <= initial_value <= self.MAX_VALUE:
            raise ValueError(f"Initial value must be between 0 and {self.MAX_VALUE}")
        
        self._value: int = initial_value
        self._overflow_count: int = 0
        self._on_overflow_callbacks: List[Callable[['UnsignedShortCounter'], None]] = []
        self._total_increments: int = 0
    
    @property
    def value(self) -> int:
        """Current counter value (0-65535)."""
        return self._value
    
    @property
    def hex_value(self) -> str:
        """Current value in hexadecimal format (e.g., '0xFFFF')."""
        return f"0x{self._value:04X}"
    
    @property
    def overflow_count(self) -> int:
        """Number of times overflow has occurred."""
        return self._overflow_count
    
    @property
    def total_increments(self) -> int:
        """Total number of increments performed."""
        return self._total_increments
    
    def increment(self, amount: int = 1) -> bool:
        """
        Increment the counter by specified amount.
        
        Uses bitwise AND to simulate unsigned overflow behavior:
        (value + amount) & 0xFFFF
        
        Args:
            amount: Amount to increment (default 1)
            
        Returns:
            True if overflow occurred, False otherwise
        """
        if amount < 0:
            raise ValueError("Increment amount must be non-negative")
        
        self._total_increments += amount
        old_value = self._value
        new_value = self._value + amount
        
        # Check if overflow will occur
        if new_value > self.MAX_VALUE:
            # Calculate how many complete overflows
            overflow_times = new_value // (self.MAX_VALUE + 1)
            self._value = new_value & self.MAX_VALUE  # Bitwise AND for wrap-around
            self._overflow_count += overflow_times
            self._trigger_overflow()
            return True
        
        self._value = new_value
        return False
    
    def fast_forward(self, hours: int) -> int:
        """
        Fast forward the counter by specified hours.
        
        Uses mathematical calculation instead of iteration
        (time complexity O(1) instead of O(n)).
        
        Args:
            hours: Number of hours to fast forward
            
        Returns:
            Number of overflows that occurred during fast forward
        """
        if hours < 0:
            raise ValueError("Hours must be non-negative")
        
        if hours == 0:
            return 0
        
        self._total_increments += hours
        new_value = self._value + hours
        
        if new_value <= self.MAX_VALUE:
            self._value = new_value
            return 0
        
        # Calculate overflows using division
        # (current + hours) / (MAX + 1) gives number of complete cycles
        overflows = new_value // (self.MAX_VALUE + 1)
        self._value = new_value % (self.MAX_VALUE + 1)
        self._overflow_count += overflows
        
        # Trigger overflow callback for each overflow
        for _ in range(overflows):
            self._trigger_overflow()
        
        return overflows
    
    def register_overflow_callback(self, callback: Callable[['UnsignedShortCounter'], None]) -> None:
        """
        Register a callback to be called when overflow occurs.
        
        Args:
            callback: Function to call on overflow, receives counter instance
        """
        self._on_overflow_callbacks.append(callback)
    
    def unregister_overflow_callback(self, callback: Callable[['UnsignedShortCounter'], None]) -> bool:
        """
        Unregister an overflow callback.
        
        Args:
            callback: The callback function to remove
            
        Returns:
            True if callback was found and removed, False otherwise
        """
        try:
            self._on_overflow_callbacks.remove(callback)
            return True
        except ValueError:
            return False
    
    def _trigger_overflow(self) -> None:
        """Invoke all registered overflow callbacks."""
        for callback in self._on_overflow_callbacks:
            callback(self)
    
    def hours_until_overflow(self) -> int:
        """
        Calculate hours remaining until next overflow.
        
        Returns:
            Number of hours until counter wraps to zero
        """
        return self.MAX_VALUE - self._value + 1
    
    def years_until_overflow(self) -> float:
        """
        Calculate years remaining until next overflow.
        
        Returns:
            Approximate years until counter wraps to zero
        """
        return self.hours_until_overflow() / self.HOURS_PER_YEAR
    
    def is_at_max(self) -> bool:
        """Check if counter is at maximum value (0xFFFF)."""
        return self._value == self.MAX_VALUE
    
    def is_at_zero(self) -> bool:
        """Check if counter is at zero."""
        return self._value == 0
    
    def reset(self) -> None:
        """Reset counter to zero without triggering callbacks."""
        self._value = 0
    
    def set_value(self, value: int) -> None:
        """
        Set counter to specific value (for testing/simulation).
        
        Args:
            value: Value to set (0-65535)
        """
        if not 0 <= value <= self.MAX_VALUE:
            raise ValueError(f"Value must be between 0 and {self.MAX_VALUE}")
        self._value = value
    
    def __repr__(self) -> str:
        return (
            f"UnsignedShortCounter(value={self._value}, "
            f"hex={self.hex_value}, overflows={self._overflow_count})"
        )
    
    def __str__(self) -> str:
        return f"Counter: {self.hex_value} ({self._value}/65535)"
