import asyncio
import pytest
import pytest_asyncio
from limbic.bus import LimbicBus
from limbic.core.endocrine import EndocrineOrchestrator
from limbic.psychology.lattice import PsychologicalLattice
from limbic.generated import limbic_pb2

@pytest_asyncio.fixture
async def setup_systems():
    bus = LimbicBus()
    endocrine = EndocrineOrchestrator(bus)
    lattice = PsychologicalLattice(bus)
    
    # Start tasks
    bus_task = asyncio.create_task(bus.run())
    endocrine_task = asyncio.create_task(endocrine.run())
    lattice_task = asyncio.create_task(lattice.run())
    
    yield bus, endocrine, lattice
    
    # Cancel tasks
    bus_task.cancel()
    endocrine_task.cancel()
    lattice_task.cancel()

@pytest.mark.asyncio
async def test_hormonal_stress_simulation(setup_systems):
    bus, endocrine, lattice = setup_systems
    
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
