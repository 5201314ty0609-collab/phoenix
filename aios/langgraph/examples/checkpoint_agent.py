"""
Checkpoint agent example using PHOENIX AIOS LangGraph framework.

Demonstrates:
- State persistence with checkpoints
- Thread-based checkpoint management
- Time-travel debugging
- State recovery
"""

from typing import TypedDict, Annotated
import operator
from aios.langgraph import StateGraph, START, END
from aios.langgraph.core.state import StateReducer, append_reducer
from aios.langgraph.checkpoint import (
    CheckpointManager,
    SQLiteStorage,
    CheckpointConfig,
)


# ============================================================================
# State Definition
# ============================================================================

class CheckpointedState(TypedDict):
    """State with checkpoint support."""
    messages: Annotated[list[dict], operator.add]
    step: int
    data: str
    thread_id: str


# ============================================================================
# Node Functions
# ============================================================================

def step1(state: dict, checkpoint_manager: CheckpointManager) -> dict:
    """First processing step."""
    thread_id = state.get("thread_id", "default")

    # Create checkpoint before processing
    checkpoint_manager.create_checkpoint(
        thread_id=thread_id,
        node_name="step1",
        state=state,
        metadata={"step": "before_step1"},
    )

    return {
        "step": 1,
        "data": "Step 1 complete",
        "messages": [{"role": "system", "content": "Completed step 1"}],
    }


def step2(state: dict, checkpoint_manager: CheckpointManager) -> dict:
    """Second processing step."""
    thread_id = state.get("thread_id", "default")

    # Create checkpoint
    checkpoint_manager.create_checkpoint(
        thread_id=thread_id,
        node_name="step2",
        state=state,
        metadata={"step": "before_step2"},
    )

    return {
        "step": 2,
        "data": "Step 2 complete",
        "messages": [{"role": "system", "content": "Completed step 2"}],
    }


def step3(state: dict, checkpoint_manager: CheckpointManager) -> dict:
    """Third processing step."""
    thread_id = state.get("thread_id", "default")

    # Create checkpoint
    checkpoint_manager.create_checkpoint(
        thread_id=thread_id,
        node_name="step3",
        state=state,
        metadata={"step": "before_step3"},
    )

    return {
        "step": 3,
        "data": "Step 3 complete",
        "messages": [{"role": "system", "content": "Completed step 3"}],
    }


# ============================================================================
# Graph Construction
# ============================================================================

def build_checkpointed_graph(
    checkpoint_manager: CheckpointManager,
) -> StateGraph:
    """Build a graph with checkpoint support.

    Args:
        checkpoint_manager: Checkpoint manager instance.

    Returns:
        Configured StateGraph.
    """
    # Create reducer
    reducer = StateReducer()
    reducer.register("messages", append_reducer)

    # Create graph
    graph = StateGraph(CheckpointedState, reducer=reducer)
    graph.name = "checkpointed_agent"

    # Add nodes with checkpoint manager
    graph.add_node("step1", lambda s: step1(s, checkpoint_manager))
    graph.add_node("step2", lambda s: step2(s, checkpoint_manager))
    graph.add_node("step3", lambda s: step3(s, checkpoint_manager))

    # Add edges
    graph.add_edge(START, "step1")
    graph.add_edge("step1", "step2")
    graph.add_edge("step2", "step3")
    graph.add_edge("step3", END)

    return graph


# ============================================================================
# Time Travel Demo
# ============================================================================

def demonstrate_time_travel(checkpoint_manager: CheckpointManager) -> None:
    """Demonstrate time-travel debugging.

    Args:
        checkpoint_manager: Checkpoint manager instance.
    """
    print("\n=== Time Travel Debugging ===")

    # List all checkpoints
    checkpoints = checkpoint_manager.list_checkpoints()
    print(f"Total checkpoints: {len(checkpoints)}")

    for i, cp in enumerate(checkpoints):
        print(f"  {i+1}. {cp.node_name} at {cp.created_at}")

    # Get checkpoint history
    if checkpoints:
        latest = checkpoints[0]
        print(f"\nHistory for latest checkpoint ({latest.id}):")
        history = checkpoint_manager.get_checkpoint_history(latest.id)
        for cp in history:
            print(f"  - {cp.node_name}: {cp.state.get('data', 'N/A')}")


# ============================================================================
# Recovery Demo
# ============================================================================

def demonstrate_recovery(
    checkpoint_manager: CheckpointManager,
    graph: StateGraph,
) -> None:
    """Demonstrate state recovery.

    Args:
        checkpoint_manager: Checkpoint manager instance.
        graph: Compiled graph.
    """
    print("\n=== State Recovery Demo ===")

    # Simulate a failure by restoring from checkpoint
    thread_id = "recovery-demo"

    # Create initial checkpoint
    initial_state = {
        "messages": [{"role": "user", "content": "Start processing"}],
        "step": 0,
        "data": "Initial state",
        "thread_id": thread_id,
    }

    checkpoint_manager.create_checkpoint(
        thread_id=thread_id,
        node_name="initial",
        state=initial_state,
    )

    # Get latest checkpoint
    latest = checkpoint_manager.get_latest_checkpoint(thread_id)
    if latest:
        print(f"Restored from checkpoint: {latest.id}")
        print(f"State at checkpoint: {latest.state}")

        # Continue from restored state
        compiled = graph.compile()
        result = compiled.invoke(latest.state)
        print(f"Continued execution result: {result['data']}")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    # Setup checkpoint manager
    storage = SQLiteStorage(":memory:")
    config = CheckpointConfig(
        enabled=True,
        auto_checkpoint=True,
        max_checkpoints=10,
    )
    checkpoint_manager = CheckpointManager(storage, config)

    # Build graph
    graph = build_checkpointed_graph(checkpoint_manager)
    compiled = graph.compile()

    # Print graph structure
    print(compiled.get_graph_visualization())
    print()

    # Run with checkpointing
    print("=== Checkpointed Execution ===")
    result = compiled.invoke({
        "messages": [{"role": "user", "content": "Process this"}],
        "step": 0,
        "data": "",
        "thread_id": "demo-thread",
    })
    print(f"Final step: {result['step']}")
    print(f"Final data: {result['data']}")
    print(f"Messages: {len(result['messages'])}")

    # Show checkpoint stats
    stats = checkpoint_manager.get_stats()
    print(f"\nCheckpoint Stats: {stats}")

    # Demonstrate time travel
    demonstrate_time_travel(checkpoint_manager)

    # Demonstrate recovery
    demonstrate_recovery(checkpoint_manager, graph)
