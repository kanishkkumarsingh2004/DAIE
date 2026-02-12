"""
Test script for Node with examples and practical applications.

This test module demonstrates:
1. Basic node creation and initialization
2. Node lifecycle management (start/stop)
3. Agent management (add/remove agents)
4. Peer node connections
5. Resource management
6. Method chaining for fluent API
7. Node status reporting
8. Practical use cases in a decentralized AI ecosystem
"""

import pytest
from daie.core.node import Node


class TestNodeCreation:
    """Tests for Node creation with various configurations."""

    def test_basic_node_creation(self, mock_logger):
        """Test creating a basic node with required parameters."""
        node = Node(node_id="node-001", name="Alpha Node")
        
        assert node.node_id == "node-001"
        assert node.name == "Alpha Node"
        assert node.is_active is False
        assert node.agents == []
        assert node.connections == []

    def test_node_creation_with_defaults(self, mock_logger):
        """Test node creation using only node_id."""
        node = Node(node_id="node-002")
        
        assert node.node_id == "node-002"
        assert node.name == "Unknown Node"
        assert node.is_active is False

    def test_node_immutability_on_copy(self, mock_logger):
        """Test that agents and connections return copies to prevent external mutation."""
        node = Node(node_id="node-003", name="Test Node")
        
        agents = node.agents
        agents.append("external-agent")
        
        assert node.agents == []
        
        connections = node.connections
        connections.append("external-node")
        
        assert node.connections == []


class TestNodeLifecycle:
    """Tests for Node start/stop lifecycle operations."""

    def test_node_start(self, mock_logger):
        """Test starting a node."""
        node = Node(node_id="node-001", name="Alpha Node")
        
        assert node.is_active is False
        node.start()
        assert node.is_active is True

    def test_node_stop(self, mock_logger):
        """Test stopping a node."""
        node = Node(node_id="node-001", name="Alpha Node")
        node.start()
        
        assert node.is_active is True
        node.stop()
        assert node.is_active is False

    def test_node_double_start(self, mock_logger):
        """Test that starting an already active node doesn't cause issues."""
        node = Node(node_id="node-001", name="Alpha Node")
        node.start()
        node.start()
        
        assert node.is_active is True

    def test_node_double_stop(self, mock_logger):
        """Test that stopping an already inactive node doesn't cause issues."""
        node = Node(node_id="node-001", name="Alpha Node")
        node.stop()
        node.stop()
        
        assert node.is_active is False


class TestAgentManagement:
    """Tests for managing agents on a node."""

    def test_add_single_agent(self, mock_logger):
        """Test adding a single agent to a node."""
        node = Node(node_id="node-001", name="Alpha Node")
        
        node.add_agent("agent-nova-001")
        
        assert "agent-nova-001" in node.agents
        assert node.agent_count == 1

    def test_add_multiple_agents(self, mock_logger):
        """Test adding multiple agents to a node."""
        node = Node(node_id="node-001", name="Alpha Node")
        
        node.add_agent("agent-nova-001")
        node.add_agent("agent-nova-002")
        node.add_agent("agent-alex-001")
        
        assert node.agent_count == 3
        assert "agent-nova-001" in node.agents
        assert "agent-nova-002" in node.agents
        assert "agent-alex-001" in node.agents

    def test_add_duplicate_agent(self, mock_logger):
        """Test that adding the same agent twice doesn't create duplicates."""
        node = Node(node_id="node-001", name="Alpha Node")
        
        node.add_agent("agent-nova-001")
        node.add_agent("agent-nova-001")
        
        assert node.agent_count == 1

    def test_remove_agent(self, mock_logger):
        """Test removing an agent from a node."""
        node = Node(node_id="node-001", name="Alpha Node")
        node.add_agent("agent-nova-001")
        node.add_agent("agent-nova-002")
        
        node.remove_agent("agent-nova-001")
        
        assert "agent-nova-001" not in node.agents
        assert node.agent_count == 1
        assert "agent-nova-002" in node.agents

    def test_remove_nonexistent_agent(self, mock_logger):
        """Test removing an agent that doesn't exist doesn't cause errors."""
        node = Node(node_id="node-001", name="Alpha Node")
        
        node.remove_agent("nonexistent-agent")
        
        assert node.agent_count == 0

    def test_has_agent(self, mock_logger):
        """Test checking if an agent exists on a node."""
        node = Node(node_id="node-001", name="Alpha Node")
        node.add_agent("agent-nova-001")
        
        assert node.has_agent("agent-nova-001") is True
        assert node.has_agent("nonexistent-agent") is False


class TestPeerConnections:
    """Tests for managing peer node connections."""

    def test_connect_to_peer(self, mock_logger):
        """Test connecting to a peer node."""
        node = Node(node_id="node-001", name="Alpha Node")
        
        node.connect("node-002")
        
        assert node.is_connected("node-002") is True
        assert node.connection_count == 1

    def test_connect_to_multiple_peers(self, mock_logger):
        """Test connecting to multiple peer nodes."""
        node = Node(node_id="node-001", name="Alpha Node")
        
        node.connect("node-002")
        node.connect("node-003")
        node.connect("node-004")
        
        assert node.connection_count == 3
        assert node.is_connected("node-002") is True
        assert node.is_connected("node-003") is True
        assert node.is_connected("node-004") is True

    def test_disconnect_from_peer(self, mock_logger):
        """Test disconnecting from a peer node."""
        node = Node(node_id="node-001", name="Alpha Node")
        node.connect("node-002")
        node.connect("node-003")
        
        node.disconnect("node-002")
        
        assert node.is_connected("node-002") is False
        assert node.connection_count == 1
        assert node.is_connected("node-003") is True

    def test_disconnect_nonexistent_peer(self, mock_logger):
        """Test disconnecting from a peer that doesn't exist doesn't cause errors."""
        node = Node(node_id="node-001", name="Alpha Node")
        
        node.disconnect("nonexistent-node")
        
        assert node.connection_count == 0

    def test_self_connection_prevention(self, mock_logger):
        """Test that a node cannot connect to itself."""
        node = Node(node_id="node-001", name="Alpha Node")
        
        node.connect("node-001")
        
        assert node.connection_count == 0

    def test_duplicate_connection_prevention(self, mock_logger):
        """Test that connecting to the same peer twice doesn't create duplicates."""
        node = Node(node_id="node-001", name="Alpha Node")
        
        node.connect("node-002")
        node.connect("node-002")
        
        assert node.connection_count == 1


class TestResourceManagement:
    """Tests for managing node resources."""

    def test_set_single_resource(self, mock_logger):
        """Test setting a single resource on a node."""
        node = Node(node_id="node-001", name="Alpha Node")
        
        node.set_resource("cpu_cores", 8)
        
        assert node.get_resource("cpu_cores") == 8

    def test_set_multiple_resources(self, mock_logger):
        """Test setting multiple resources on a node."""
        node = Node(node_id="node-001", name="Alpha Node")
        
        node.set_resource("cpu_cores", 8)
        node.set_resource("memory_gb", 32)
        node.set_resource("storage_tb", 2)
        node.set_resource("gpu_available", True)
        
        assert node.get_resource("cpu_cores") == 8
        assert node.get_resource("memory_gb") == 32
        assert node.get_resource("storage_tb") == 2
        assert node.get_resource("gpu_available") is True

    def test_get_resource_with_default(self, mock_logger):
        """Test getting a resource with a default value if not found."""
        node = Node(node_id="node-001", name="Alpha Node")
        
        assert node.get_resource("nonexistent", "default_value") == "default_value"
        assert node.get_resource("nonexistent", 0) == 0
        assert node.get_resource("nonexistent", None) is None

    def test_get_resource_info(self, mock_logger):
        """Test getting all resources as a dictionary."""
        node = Node(node_id="node-001", name="Alpha Node")
        node.set_resource("cpu_cores", 8)
        node.set_resource("memory_gb", 32)
        
        resources = node.get_resource_info()
        
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert resources["cpu_cores"] == 8
        assert resources["memory_gb"] == 32


class TestMethodChaining:
    """Tests for method chaining - a key feature of the Node API."""

    def test_method_chaining_start(self, mock_logger):
        """Test that start can be called and node is active."""
        node = Node(node_id="node-001", name="Alpha Node")
        
        result = node.start()
        
        # Note: start() doesn't return self, so we verify node state directly
        assert node.is_active is True
        
    def test_method_chaining_add_agent(self, mock_logger):
        """Test method chaining for add_agent."""
        node = Node(node_id="node-001", name="Alpha Node")
        
        result = node.add_agent("agent-nova-001")
        
        assert result is node
        assert node.agent_count == 1

    def test_method_chaining_connect(self, mock_logger):
        """Test method chaining for connect."""
        node = Node(node_id="node-001", name="Alpha Node")
        
        result = node.connect("node-002")
        
        assert result is node
        assert node.connection_count == 1

    def test_method_chaining_set_resource(self, mock_logger):
        """Test method chaining for set_resource."""
        node = Node(node_id="node-001", name="Alpha Node")
        
        result = node.set_resource("cpu_cores", 8)
        
        assert result is node
        assert node.get_resource("cpu_cores") == 8

    def test_comprehensive_method_chaining(self, mock_logger):
        """Test comprehensive method chaining for fluent API."""
        node = Node(node_id="node-001", name="Alpha Node")
        
        # Chain the methods that support chaining
        (node
         .add_agent("agent-nova-001")
         .add_agent("agent-nova-002")
         .connect("node-002")
         .connect("node-003")
         .set_resource("cpu_cores", 8)
         .set_resource("memory_gb", 32))
        
        # Start separately since it doesn't return self
        node.start()
        
        assert node.is_active is True
        assert node.agent_count == 2
        assert node.connection_count == 2
        assert node.get_resource("cpu_cores") == 8
        assert node.get_resource("memory_gb") == 32


class TestNodeStatus:
    """Tests for node status reporting."""

    def test_inactive_node_status(self, mock_logger):
        """Test status of an inactive node."""
        node = Node(node_id="node-001", name="Alpha Node")
        node.add_agent("agent-nova-001")
        node.connect("node-002")
        node.set_resource("cpu_cores", 8)
        
        status = node.get_status()
        
        assert status["node_id"] == "node-001"
        assert status["name"] == "Alpha Node"
        assert status["status"] == "inactive"
        assert status["agent_count"] == 1
        assert "agent-nova-001" in status["agents"]
        assert status["connection_count"] == 1
        assert "node-002" in status["connections"]
        assert status["resources"]["cpu_cores"] == 8

    def test_active_node_status(self, mock_logger):
        """Test status of an active node."""
        node = Node(node_id="node-001", name="Alpha Node")
        node.start()
        
        status = node.get_status()
        
        assert status["status"] == "active"

    def test_status_reflects_all_changes(self, mock_logger):
        """Test that status reflects all changes made to the node."""
        node = Node(node_id="node-001", name="Alpha Node")
        
        # Make various changes
        node.start()
        node.add_agent("agent-nova-001")
        node.add_agent("agent-alex-001")
        node.connect("node-002")
        node.set_resource("cpu_cores", 16)
        
        status = node.get_status()
        
        assert status["status"] == "active"
        assert status["agent_count"] == 2
        assert status["connection_count"] == 1
        assert status["resources"]["cpu_cores"] == 16


class TestNodeStringRepresentation:
    """Tests for node string representations."""

    def test_str_representation_inactive(self, mock_logger):
        """Test string representation of an inactive node."""
        node = Node(node_id="node-001", name="Alpha Node")
        
        representation = str(node)
        
        assert "node-001" in representation
        assert "Alpha Node" in representation
        assert "inactive" in representation

    def test_str_representation_active(self, mock_logger):
        """Test string representation of an active node."""
        node = Node(node_id="node-001", name="Alpha Node")
        node.start()
        
        representation = str(node)
        
        assert "active" in representation


class TestPracticalUseCases:
    """Tests for practical use cases in a decentralized AI ecosystem."""

    def test_setup_computational_node(self, mock_logger):
        """Test setting up a computational node with resources."""
        compute_node = (
            Node(node_id="compute-node-001", name="Compute Node 1")
            .set_resource("cpu_cores", 32)
            .set_resource("memory_gb", 128)
            .set_resource("storage_tb", 4)
            .set_resource("gpu_available", True)
            .set_resource("gpu_count", 4)
        )
        
        assert compute_node.get_resource("cpu_cores") == 32
        assert compute_node.get_resource("memory_gb") == 128
        assert compute_node.get_resource("gpu_available") is True

    def test_setup_agent_host_node(self, mock_logger):
        """Test setting up a node to host AI agents."""
        agent_node = Node(node_id="agent-node-001", name="Agent Host")
        
        # Chain methods that support chaining
        (agent_node
         .add_agent("nova")
         .add_agent("alex")
         .add_agent("assistant")
         .set_resource("agent_capacity", 10))
        
        # Start separately since it doesn't return self
        agent_node.start()
        
        assert agent_node.agent_count == 3
        assert agent_node.is_active is True

    def test_network_topology_simulation(self, mock_logger):
        """Test simulating a simple network topology."""
        # Create nodes
        node_a = Node(node_id="node-a", name="Node A")
        node_b = Node(node_id="node-b", name="Node B")
        node_c = Node(node_id="node-c", name="Node C")
        node_d = Node(node_id="node-d", name="Node D")
        
        # Establish connections (each node initiates its own connections)
        # Duplicate prevention only prevents adding the same peer ID twice
        node_a.connect("node-b")  # a->b
        node_a.connect("node-c")  # a->c
        node_b.connect("node-a")  # b->a (not a duplicate of a->b, different direction)
        node_b.connect("node-c")  # b->c
        node_b.connect("node-d")  # b->d
        node_c.connect("node-a")  # c->a
        node_c.connect("node-b")  # c->b
        node_c.connect("node-d")  # c->d
        node_d.connect("node-b")  # d->b
        node_d.connect("node-c")  # d->c
        
        # Verify connectivity (all nodes can reach each other)
        assert node_a.is_connected("node-b") is True
        assert node_a.is_connected("node-c") is True
        assert node_b.is_connected("node-c") is True
        assert node_b.is_connected("node-d") is True
        assert node_c.is_connected("node-d") is True
        
        # Count connections (directed connections - each node tracks who it connected to)
        assert node_a.connection_count == 2  # a->b, a->c
        assert node_b.connection_count == 3  # b->a, b->c, b->d
        assert node_c.connection_count == 3  # c->a, c->b, c->d
        assert node_d.connection_count == 2  # d->b, d->c

    def test_node_decommissioning(self, mock_logger):
        """Test decommissioning a node from the network."""
        node = Node(node_id="node-001", name="Decommission Node")
        node.start()
        node.add_agent("agent-nova-001")
        node.connect("peer-node")
        node.set_resource("status", "decommissioning")
        
        # Decommission: stop node, remove agents, disconnect peers
        node.stop()
        node.remove_agent("agent-nova-001")
        node.disconnect("peer-node")
        
        assert node.is_active is False
        assert node.agent_count == 0
        assert node.connection_count == 0

    def test_node_health_check(self, mock_logger):
        """Test performing a health check on a node."""
        node = Node(node_id="node-001", name="Health Check Node")
        node.start()
        node.set_resource("cpu_usage", 45.5)
        node.set_resource("memory_usage", 60.2)
        node.set_resource("disk_usage", 75.0)
        
        # Simulate health check
        status = node.get_status()
        
        health_ok = (
            status["status"] == "active" and
            status["resources"]["cpu_usage"] < 80 and
            status["resources"]["memory_usage"] < 90
        )
        
        assert health_ok is True

    def test_distributed_task_execution(self, mock_logger):
        """Test setting up nodes for distributed task execution."""
        # Create worker nodes
        workers = []
        for i in range(3):
            worker = (
                Node(node_id=f"worker-{i:03d}", name=f"Worker {i}")
                .set_resource("cpu_cores", 8)
                .set_resource("memory_gb", 32)
                .add_agent(f"worker-agent-{i}")
            )
            workers.append(worker)
        
        # Create coordinator node
        coordinator = (
            Node(node_id="coordinator-001", name="Coordinator")
            .connect("worker-000")
            .connect("worker-001")
            .connect("worker-002")
        )
        
        # Verify setup
        assert len(workers) == 3
        assert coordinator.connection_count == 3
        
        for worker in workers:
            assert worker.agent_count == 1
            assert worker.get_resource("cpu_cores") == 8

    def test_node_migration_simulation(self, mock_logger):
        """Test simulating agent migration between nodes."""
        source_node = Node(node_id="source-node", name="Source Node")
        target_node = Node(node_id="target-node", name="Target Node")
        
        # Add agent to source
        source_node.add_agent("migrating-agent")
        source_node.set_resource("agent_count", 1)
        
        # Migrate agent
        agent = "migrating-agent"
        source_node.remove_agent(agent)
        target_node.add_agent(agent)
        
        assert "migrating-agent" not in source_node.agents
        assert "migrating-agent" in target_node.agents
        assert source_node.get_resource("agent_count") == 1
        assert target_node.get_resource("agent_count") is None

    def test_fault_tolerant_design(self, mock_logger):
        """Test setting up fault-tolerant node configuration."""
        primary_node = Node(node_id="primary-node", name="Primary")
        secondary_node = Node(node_id="secondary-node", name="Secondary")
        
        # Both nodes have same resources
        primary_node.set_resource("replication_factor", 2)
        secondary_node.set_resource("replication_factor", 2)
        
        # Connect for heartbeat
        primary_node.connect("secondary-node")
        secondary_node.connect("primary-node")
        
        # Simulate primary failure - stopping doesn't remove connections
        # but the primary is no longer active
        primary_node.stop()
        
        # Verify state
        assert primary_node.is_active is False
        assert primary_node.is_connected("secondary-node") is True
        assert secondary_node.is_connected("primary-node") is True
        
        # Secondary can detect primary is down (not active) and take over
        if not primary_node.is_active:
            secondary_node.start()
        assert secondary_node.is_active is True
        
        # Primary can be recovered
        primary_node.start()
        assert primary_node.is_active is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
