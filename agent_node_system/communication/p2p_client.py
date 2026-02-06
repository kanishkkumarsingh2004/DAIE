#!/usr/bin/env python3
"""
Decentralized AI Ecosystem - Agent Node System
P2P Communication Client

This module provides the P2P communication functionality for agents to 
communicate directly with other agents in the network using libp2p 
for true decentralization.

Author: Decentralized AI Ecosystem Team
Version: 1.0.0
"""

import logging
import asyncio
from typing import Dict, List, Optional, Callable
from libp2p.crypto.keys import KeyPair
from libp2p.peer.peerinfo import info_from_p2p_addr
from libp2p.peer.id import ID
from libp2p.host.basic_host import BasicHost
from libp2p.network.stream.net_stream_interface import INetStream
from libp2p.identity.identity import Identity
import multiaddr
import base64
import json

logger = logging.getLogger(__name__)

class P2PClient:
    """
    P2P Communication Client
    
    Provides functionality for agents to communicate directly with other agents
    in the network without going through the Central Core System, using libp2p.
    """
    
    def __init__(self, agent_id: str, listen_address: str = "/ip4/0.0.0.0/tcp/0"):
        """
        Initialize the P2P client
        
        Args:
            agent_id: Unique identifier for the agent
            listen_address: Listen address for incoming connections
        """
        self.agent_id = agent_id
        self.listen_address = listen_address
        self.host: Optional[BasicHost] = None
        self.connected_peers: Dict[str, INetStream] = {}
        self.peer_addresses: Dict[str, str] = {}
        self.message_handlers: List[Callable] = []
        self.running = False
        self._listen_task = None
        
        logger.info(f"P2P client initialized for agent: {agent_id}")
    
    async def start(self) -> bool:
        """
        Start the P2P client and begin listening for connections
        
        Returns:
            bool: True if startup successful, False otherwise
        """
        try:
            logger.info(f"Starting P2P client on: {self.listen_address}")
            
            # Create libp2p host
            self.host = await self._create_host()
            
            # Start listening
            await self.host.listen(multiaddr.Multiaddr(self.listen_address))
            
            # Register stream handler
            self.host.get_network().set_stream_handler("/agent-comms/1.0.0", self._handle_stream)
            
            # Start periodic peer discovery
            self.running = True
            self._listen_task = asyncio.create_task(self._periodic_discovery())
            
            logger.info("P2P client started successfully")
            logger.debug(f"Listening on addresses: {[str(ma) for ma in self.host.get_addrs()]}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start P2P client: {e}")
            return False
    
    async def _create_host(self) -> BasicHost:
        """Create and configure a libp2p host"""
        # Generate random key pair
        from libp2p.crypto.rsa import create_new_key_pair
        key_pair = create_new_key_pair()
        
        # Create identity
        identity = Identity(key_pair)
        
        # Create basic host
        host = BasicHost(identity)
        
        return host
    
    async def _handle_stream(self, stream: INetStream):
        """Handle incoming streams from peers"""
        peer_id = str(stream.muxed_conn.peer_id)
        
        logger.info(f"New stream established with peer: {peer_id}")
        
        # Store the stream
        self.connected_peers[peer_id] = stream
        
        # Start reading from stream
        asyncio.create_task(self._read_stream(stream))
    
    async def _read_stream(self, stream: INetStream):
        """Read data from a stream"""
        peer_id = str(stream.muxed_conn.peer_id)
        
        try:
            while True:
                data = await stream.read()
                if not data:
                    break
                    
                # Process received data
                await self._process_received_data(peer_id, data)
                
        except Exception as e:
            logger.error(f"Error reading from stream {peer_id}: {e}")
        finally:
            # Remove from connected peers
            if peer_id in self.connected_peers:
                del self.connected_peers[peer_id]
            logger.info(f"Stream closed with peer: {peer_id}")
    
    async def _process_received_data(self, peer_id: str, data: bytes):
        """Process received data from a peer"""
        try:
            decoded_data = data.decode('utf-8')
            message = json.loads(decoded_data)
            
            logger.debug(f"Message received from peer {peer_id}: {message}")
            
            # Notify all handlers
            for handler in self.message_handlers:
                await handler(peer_id, message)
                
        except Exception as e:
            logger.error(f"Failed to process received data: {e}")
    
    async def connect(self, peer_address: str) -> bool:
        """
        Connect to a peer agent
        
        Args:
            peer_address: Address of the peer to connect to
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to peer: {peer_address}")
            
            ma = multiaddr.Multiaddr(peer_address)
            info = info_from_p2p_addr(ma)
            
            # Connect to peer
            await self.host.connect(info)
            
            # Open stream
            stream = await self.host.new_stream(info.peer_id, ["/agent-comms/1.0.0"])
            
            peer_id = str(info.peer_id)
            self.connected_peers[peer_id] = stream
            self.peer_addresses[peer_id] = peer_address
            
            # Start reading from stream
            asyncio.create_task(self._read_stream(stream))
            
            logger.info(f"Connected to peer: {peer_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to peer {peer_address}: {e}")
            return False
    
    async def disconnect(self, peer_id: str) -> bool:
        """
        Disconnect from a peer agent
        
        Args:
            peer_id: Peer identifier
            
        Returns:
            bool: True if disconnection successful, False otherwise
        """
        try:
            logger.info(f"Disconnecting from peer: {peer_id}")
            
            if peer_id in self.connected_peers:
                stream = self.connected_peers[peer_id]
                await stream.close()
                del self.connected_peers[peer_id]
                
            if peer_id in self.peer_addresses:
                del self.peer_addresses[peer_id]
                
            logger.info(f"Disconnected from peer: {peer_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disconnect from peer {peer_id}: {e}")
            return False
    
    async def send_message(self, peer_id: str, message: Dict) -> bool:
        """
        Send a message to a peer agent
        
        Args:
            peer_id: Peer identifier
            message: Message to send
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        try:
            if peer_id not in self.connected_peers:
                logger.error(f"Not connected to peer: {peer_id}")
                return False
                
            stream = self.connected_peers[peer_id]
            
            # Serialize and send message
            message_bytes = json.dumps(message).encode('utf-8')
            await stream.write(message_bytes)
            await stream.flush()
            
            logger.debug(f"Message sent to peer {peer_id}: {message}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message to peer {peer_id}: {e}")
            return False
    
    async def send_broadcast(self, message: Dict) -> int:
        """
        Send a message to all connected peers
        
        Args:
            message: Message to broadcast
            
        Returns:
            int: Number of peers message was sent to
        """
        sent_count = 0
        
        for peer_id in list(self.connected_peers.keys()):
            if await self.send_message(peer_id, message):
                sent_count += 1
                
        logger.debug(f"Broadcast message sent to {sent_count} peers")
        return sent_count
    
    async def _periodic_discovery(self):
        """Periodically discover new peers in the network"""
        logger.info("Starting peer discovery")
        
        while self.running:
            try:
                logger.debug("Performing peer discovery...")
                
                # TODO: Implement actual peer discovery (DHT, mDNS, etc.)
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Peer discovery failed: {e}")
                await asyncio.sleep(30)
    
    async def search_peers(self, criteria: Dict) -> List[str]:
        """
        Search for peers matching specific criteria
        
        Args:
            criteria: Search criteria
            
        Returns:
            List[str]: List of peer identifiers matching the criteria
        """
        # TODO: Implement actual peer search functionality
        logger.debug(f"Searching peers with criteria: {criteria}")
        return list(self.connected_peers.keys())
    
    def add_message_handler(self, handler: Callable):
        """
        Add a message handler
        
        Args:
            handler: Callback function to handle incoming messages
        """
        self.message_handlers.append(handler)
        logger.debug("Message handler added")
    
    def get_connected_peers(self) -> List[str]:
        """
        Get list of connected peers
        
        Returns:
            list: List of connected peer identifiers
        """
        return list(self.connected_peers.keys())
    
    def get_peer_address(self, peer_id: str) -> Optional[str]:
        """
        Get the address of a specific peer
        
        Args:
            peer_id: Peer identifier
            
        Returns:
            str: Peer address or None if not found
        """
        return self.peer_addresses.get(peer_id)
    
    def is_connected(self, peer_id: str) -> bool:
        """
        Check if connected to a specific peer
        
        Args:
            peer_id: Peer identifier
            
        Returns:
            bool: True if connected to peer, False otherwise
        """
        return peer_id in self.connected_peers
    
    def get_listening_addresses(self) -> List[str]:
        """
        Get the addresses the host is listening on
        
        Returns:
            List[str]: List of listening addresses
        """
        if self.host:
            return [str(ma) for ma in self.host.get_addrs()]
        return []
    
    def get_peer_id(self) -> str:
        """
        Get the host's peer ID
        
        Returns:
            str: Host peer ID
        """
        if self.host:
            return str(self.host.get_id())
        return ""
    
    async def stop(self):
        """Stop the P2P client"""
        logger.info("Stopping P2P client...")
        
        self.running = False
        
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        for peer_id in list(self.connected_peers.keys()):
            await self.disconnect(peer_id)
        
        if self.host:
            await self.host.close()
        
        logger.info("P2P client stopped")

if __name__ == "__main__":
    # Test P2P client functionality
    logging.basicConfig(level=logging.DEBUG)
    
    async def test_p2p_client():
        try:
            # Create test server
            server = P2PClient("server-agent")
            await server.start()
            
            # Create test client
            client = P2PClient("client-agent")
            await client.start()
            
            # Get server addresses
            server_addrs = server.get_listening_addresses()
            server_id = server.get_peer_id()
            
            # Connect client to server
            peer_address = f"{server_addrs[0]}/p2p/{server_id}"
            await client.connect(peer_address)
            
            # Test message handler
            async def message_handler(peer_id, message):
                logger.info(f"Test message received from {peer_id}: {message}")
                
            server.add_message_handler(message_handler)
            
            # Test message sending
            test_message = {"type": "test", "content": "Hello from client!", "timestamp": 123456}
            await client.send_message(server_id, test_message)
            
            await asyncio.sleep(1)
            
            # Test broadcast
            broadcast_message = {"type": "broadcast", "content": "Hello everyone!", "timestamp": 123457}
            await client.send_broadcast(broadcast_message)
            
            await asyncio.sleep(1)
            
            # Test get connected peers
            server_peers = server.get_connected_peers()
            client_peers = client.get_connected_peers()
            
            logger.info(f"Server connected to: {server_peers}")
            logger.info(f"Client connected to: {client_peers}")
            
            # Test disconnection
            await client.disconnect(server_id)
            
            await asyncio.sleep(1)
            
            logger.info("✅ P2P client test completed successfully!")
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
        finally:
            if 'server' in locals():
                await server.stop()
            if 'client' in locals():
                await client.stop()
    
    asyncio.run(test_p2p_client())
