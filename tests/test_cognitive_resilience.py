import asyncio
import pytest
import pytest_asyncio
from limbic.bus import LimbicBus
from limbic.core.endocrine import EndocrineOrchestrator
from limbic.psychology.lattice import PsychologicalLattice
from limbic.pfc.acc import ACC
from limbic.pfc.executive_control import ExecutiveControl
from limbic.generated import limbic_pb2

@pytest_asyncio.fixture
async def setup_systems():
    bus = LimbicBus()
    endocrine = EndocrineOrchestrator(bus)
    lattice = PsychologicalLattice(bus)
    acc = ACC(bus)
    executive = ExecutiveControl(bus)
    
    # Start tasks
    bus_task = asyncio.create_task(bus.run())
    endocrine_task = asyncio.create_task(endocrine.run())
    lattice_task = asyncio.create_task(lattice.run())
    acc_task = asyncio.create_task(acc.run())
    executive_task = asyncio.create_task(executive.run())
    
    yield bus, endocrine, lattice, acc, executive
    
    # Cancel tasks
    bus_task.cancel()
    endocrine_task.cancel()
    lattice_task.cancel()
    acc_task.cancel()
    executive_task.cancel()

@pytest.mark.asyncio
async def test_hormonal_stress_simulation(setup_systems):
    bus, endocrine, lattice, acc, executive = setup_systems
    
    # Initial state check
    assert endocrine.hormones["cortisol"] >= 0.2
    assert lattice.ego_coherence == 1.0
    
    # Simulate high frequency stress stimuli
    for _ in range(10):
        # We need to simulate what causes cortisol to spike
        # Based on handle_engine_active
        await bus.publish("ENGINE_ACTIVE", {"name": "FEAR", "level": 0.9})
        
        # Based on handle_override for ego coherence
        await bus.publish("LIMBIC_OVERRIDE", {"suppress": ["hunger", "thirst", "rest"]})
        
        await asyncio.sleep(0.1)
    
    # Give some time for processing
    await asyncio.sleep(0.5)
    
    # Check if cortisol spiked
    assert endocrine.hormones["cortisol"] > 0.4
    
    # Check if adrenaline spiked
    assert endocrine.hormones["adrenaline"] > 0.3
    
    # Check if ego_coherence dropped
    assert lattice.ego_coherence < 1.0
    
    # Test recovery
    await asyncio.sleep(2)
    
    # Cortisol should start decaying (though might take longer than 2s to reach baseline)
    # But it should be lower than its peak
    current_cortisol = endocrine.hormones["cortisol"]
    # Wait another second to ensure decay
    await asyncio.sleep(1)
    assert endocrine.hormones["cortisol"] <= current_cortisol

@pytest.mark.asyncio
async def test_choice_difficulty_and_stalemate(setup_systems):
    bus, endocrine, lattice, acc, executive = setup_systems

    # Simulate two plans with very similar utilities
    pid = "test_cycle_1"

    # Published utilities for two different actions
    await bus.publish("UTILITY_ASSIGNED", {
        "id": pid,
        "plan": {"action": "EXPLORE"},
        "utility": 0.5
    })
    await bus.publish("UTILITY_ASSIGNED", {
        "id": pid,
        "plan": {"action": "COOPERATE"},
        "utility": 0.51 # Very close to 0.5
    })

    # Give it a moment to process in ACC
    await asyncio.sleep(0.1)

    # ACC should have signaled high effort due to choice difficulty
    assert executive.effort_level >= 0.8

    # The executive should now arbitrate.
    # Because effort is high and diff is small, it should hit deliberative stalemate
    # We need to wait for the deliberation window
    await asyncio.sleep(1.5) # window = 0.2 + 0.8 * 0.8 = 0.84

    # We can check if a STAY action was published
    # Since we can't easily check published events without a subscriber in the test,
    # let's subscribe to ACTION_COMMAND
    actions = []
    async def track_action(data):
        actions.append(data)
    bus.subscribe("ACTION_COMMAND", track_action)

    # Re-run arbitration by sending same utilities for a new PID
    pid2 = "test_cycle_2"
    await bus.publish("UTILITY_ASSIGNED", {
        "id": pid2,
        "plan": {"action": "EXPLORE"},
        "utility": 0.5
    })
    await bus.publish("UTILITY_ASSIGNED", {
        "id": pid2,
        "plan": {"action": "COOPERATE"},
        "utility": 0.51
    })

    await asyncio.sleep(1.5)

    # Check if STAY was chosen for pid2
    assert any(a["action"] == "STAY" and a["id"] == pid2 for a in actions)
