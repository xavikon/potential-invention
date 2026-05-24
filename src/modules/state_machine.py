"""
CMIS and SFF Pluggable Module State Machines.
Defines module-level and data-path-level state transitions, enforcing standard CMIS behaviors.
"""
import time
from enum import Enum, auto
from typing import Dict, Optional, Set

class ModuleState(Enum):
    """Module-level administrative and operational states as per CMIS 4.0 Chapter 6."""
    RESET = auto()          # Module is undergoing hardware or software reset
    LOW_POWER = auto()      # Module is in low power state; high-speed circuitry disabled; I2C active
    HIGH_POWER = auto()     # Module is fully powered up; high-speed links are operational
    FAULT = auto()          # Module has encountered a critical hardware/software fault


class DataPathState(Enum):
    """Data path operational states for transceiver lanes."""
    DEACTIVATED = auto()    # Data path is disabled; transmitters are powered down
    ACTIVATED = auto()      # Data path is active but not transmitting/receiving data
    TX_ON = auto()          # Transmitter is active and outputting signal
    RX_ON = auto()          # Receiver is active and receiving signal
    READY = auto()          # Both TX and RX are fully operational and transferring data


class StateMachineError(Exception):
    """Base class for state machine transition and boundary errors."""
    pass


class ModuleStateMachine:
    """
    Manages module-level states and transitions, validating operations and simulated timing.
    """
    
    def __init__(self, initial_state: ModuleState = ModuleState.LOW_POWER):
        """Initialize the state machine."""
        self._state = initial_state
        self._transition_times: Dict[tuple, float] = {
            (ModuleState.RESET, ModuleState.LOW_POWER): 0.1,    # seconds
            (ModuleState.LOW_POWER, ModuleState.HIGH_POWER): 0.5,
            (ModuleState.HIGH_POWER, ModuleState.LOW_POWER): 0.2,
        }
        
    @property
    def state(self) -> ModuleState:
        """Get the current module state."""
        return self._state
        
    def transition_to(self, target: ModuleState, simulate_delay: bool = False) -> None:
        """
        Transition the module state to a target state, verifying constraints.
        
        Args:
            target: The destination ModuleState.
            simulate_delay: If True, blocks execution to simulate physical hardware latency.
            
        Raises:
            StateMachineError: If the state transition is illegal under CMIS guidelines.
        """
        current = self._state
        if current == target:
            return
            
        # Illegal Transitions
        if current == ModuleState.RESET and target == ModuleState.HIGH_POWER:
            raise StateMachineError("Illegal transition: Cannot transition from RESET directly to HIGH_POWER.")
        if current == ModuleState.FAULT and target == ModuleState.HIGH_POWER:
            raise StateMachineError("Illegal transition: Cannot exit FAULT state directly to HIGH_POWER. Must go to RESET or LOW_POWER first.")
            
        # Enforce transitions through RESET / Fault recovery
        if target == ModuleState.RESET:
            # Any state can transition to RESET
            pass
            
        # Handle simulated timing delays
        transition_key = (current, target)
        if simulate_delay and transition_key in self._transition_times:
            time.sleep(self._transition_times[transition_key])
            
        self._state = target

    def trigger_fault(self) -> None:
        """Force the module state into FAULT."""
        self._state = ModuleState.FAULT

    def clear_fault(self) -> None:
        """Recover from a fault state into LOW_POWER."""
        if self._state != ModuleState.FAULT:
            raise StateMachineError("Cannot clear fault: Module is not in FAULT state.")
        self._state = ModuleState.LOW_POWER


class DataPathStateMachine:
    """
    Manages state machines for individual transceiver data paths or lanes.
    Ensures lanes are properly initialized and activated in sequence.
    """
    
    def __init__(self, num_lanes: int = 1):
        """
        Initialize lane states.
        
        Args:
            num_lanes: Number of lanes supported by the transceiver.
        """
        self._num_lanes = num_lanes
        self._lane_states: Dict[int, DataPathState] = {
            lane: DataPathState.DEACTIVATED for lane in range(num_lanes)
        }
        
    def get_lane_state(self, lane: int) -> DataPathState:
        """Get the current state of a specific lane."""
        self._validate_lane(lane)
        return self._lane_states[lane]
        
    def transition_lane(self, lane: int, target: DataPathState) -> None:
        """
        Transition a specific lane's state.
        
        Args:
            lane: The lane index.
            target: The destination DataPathState.
            
        Raises:
            StateMachineError: If the lane state transition violates sequencing guidelines.
        """
        self._validate_lane(lane)
        current = self._lane_states[lane]
        
        if current == target:
            return
            
        # Enforce progressive activation sequencing
        if current == DataPathState.DEACTIVATED and target in (DataPathState.TX_ON, DataPathState.RX_ON, DataPathState.READY):
            raise StateMachineError(f"Illegal transition: Lane {lane} must be ACTIVATED before powering transmitters/receivers.")
            
        self._lane_states[lane] = target

    def deactivate_all(self) -> None:
        """Force all lanes back to DEACTIVATED state."""
        for lane in self._lane_states:
            self._lane_states[lane] = DataPathState.DEACTIVATED

    def _validate_lane(self, lane: int) -> None:
        """Helper to validate lane boundaries."""
        if not 0 <= lane < self._num_lanes:
            raise StateMachineError(f"Invalid lane identifier {lane}. Transceiver supports {self._num_lanes} lanes.")
