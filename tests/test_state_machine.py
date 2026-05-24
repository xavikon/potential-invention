"""
Unit and integration tests for the Module and Data Path State Machines.
"""
import pytest
from src.modules.state_machine import (
    ModuleStateMachine, ModuleState, DataPathStateMachine, DataPathState, StateMachineError
)

def test_module_state_transitions():
    """Verify normal/valid module state transitions."""
    sm = ModuleStateMachine(initial_state=ModuleState.LOW_POWER)
    assert sm.state == ModuleState.LOW_POWER
    
    # LowPower -> HighPower
    sm.transition_to(ModuleState.HIGH_POWER)
    assert sm.state == ModuleState.HIGH_POWER
    
    # HighPower -> LowPower
    sm.transition_to(ModuleState.LOW_POWER)
    assert sm.state == ModuleState.LOW_POWER
    
    # LowPower -> Reset
    sm.transition_to(ModuleState.RESET)
    assert sm.state == ModuleState.RESET
    
    # Reset -> LowPower
    sm.transition_to(ModuleState.LOW_POWER)
    assert sm.state == ModuleState.LOW_POWER


def test_module_illegal_transitions():
    """Verify state machine raises errors on invalid module state transitions."""
    sm = ModuleStateMachine(initial_state=ModuleState.RESET)
    
    # Cannot jump directly from RESET to HIGH_POWER
    with pytest.raises(StateMachineError):
        sm.transition_to(ModuleState.HIGH_POWER)
        
    # Put machine into FAULT
    sm.transition_to(ModuleState.LOW_POWER)
    sm.trigger_fault()
    assert sm.state == ModuleState.FAULT
    
    # Cannot jump directly from FAULT to HIGH_POWER
    with pytest.raises(StateMachineError):
        sm.transition_to(ModuleState.HIGH_POWER)


def test_fault_clearing():
    """Verify fault entry and recovery routes."""
    sm = ModuleStateMachine(initial_state=ModuleState.HIGH_POWER)
    
    # Trigger fault from active state
    sm.trigger_fault()
    assert sm.state == ModuleState.FAULT
    
    # Recover to low power
    sm.clear_fault()
    assert sm.state == ModuleState.LOW_POWER
    
    # Cannot clear fault if not in fault
    with pytest.raises(StateMachineError):
        sm.clear_fault()


def test_data_path_lane_sequencing():
    """Verify standard lane progressive activation sequences."""
    dp = DataPathStateMachine(num_lanes=4)
    assert dp.get_lane_state(0) == DataPathState.DEACTIVATED
    
    # Can transition to ACTIVATED
    dp.transition_lane(0, DataPathState.ACTIVATED)
    assert dp.get_lane_state(0) == DataPathState.ACTIVATED
    
    # Can transition from ACTIVATED to TX_ON
    dp.transition_lane(0, DataPathState.TX_ON)
    assert dp.get_lane_state(0) == DataPathState.TX_ON


def test_data_path_illegal_transitions():
    """Verify lane state transitions raise errors on sequencing violations."""
    dp = DataPathStateMachine(num_lanes=4)
    
    # Cannot jump from DEACTIVATED directly to TX_ON or READY
    with pytest.raises(StateMachineError):
        dp.transition_lane(1, DataPathState.TX_ON)
        
    with pytest.raises(StateMachineError):
        dp.transition_lane(2, DataPathState.READY)
        
    # Invalid lane bounds
    with pytest.raises(StateMachineError):
        dp.get_lane_state(99)
        
    with pytest.raises(StateMachineError):
        dp.transition_lane(-1, DataPathState.ACTIVATED)
