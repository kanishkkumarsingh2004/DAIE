"""
NATS JetStream provider for decentralized communication
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, Optional

import nats
from nats.js.errors import BadRequestError

from daie.agents.message import AgentMessage
from daie.config import SystemConfig

logger = logging.getLogger(__name__)


class NatsProvider:
    """
    NATS JetStream provider for agent communication.
    Provides message queuing, offline support, and efficient broadcasting.
    """

    def __init__(self, config: SystemConfig):
        self.config = config
        self.nc: Optional[nats.NATS] = None
        self.js: Optional[Any] = None
        self._subscriptions: Dict[str, Any] = {}
        self._is_connected = False
        self._stream_name = "DAIE_MESSAGES"
        self._subjects = ["daie.agents.*", "daie.groups.*", "daie.broadcast"]

    async def connect(self):
        """Connect to NATS and setup JetStream"""
        try:
            self.nc = await nats.connect(
                self.config.nats_url,
                reconnect_time_wait=2,
                max_reconnect_attempts=getattr(self.config, "connection_retries", 5),
            )
            self.js = self.nc.jetstream()

            # Ensure stream exists for persistent messaging
            await self._setup_stream()

            self._is_connected = True
            logger.info(f"Connected to NATS at {self.config.nats_url}")
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            self._is_connected = False
            raise

    async def _setup_stream(self):
        """Setup JetStream stream if not exists"""
        if not self.js:
            return

        try:
            # Enhanced stream config with retention limits
            await self.js.add_stream(
                name=self._stream_name,
                subjects=self._subjects,
                max_msgs=getattr(self.config, "nats_max_msgs", 100000),
                max_bytes=getattr(self.config, "nats_max_bytes", 1024 * 1024 * 1024),  # 1GB
                max_age=getattr(self.config, "nats_max_age", 3600 * 24 * 7),  # 7 days
            )
            logger.debug(f"Created NATS stream: {self._stream_name}")
        except BadRequestError:
            # Stream might already exist with different config or same
            try:
                await self.js.update_stream(name=self._stream_name, subjects=self._subjects)
                logger.debug(f"Updated NATS stream: {self._stream_name}")
            except Exception as e:
                logger.error(f"Failed to setup NATS stream: {e}")

    async def subscribe_agent(self, agent_id: str, callback: Callable[[AgentMessage], Any]):
        """Subscribe to messages for a specific agent with offline support"""
        if not self.js:
            return

        subject = f"daie.agents.{agent_id}"
        durable_name = f"agent_{agent_id.replace('-', '_')}"

        try:
            # Use a durable consumer so messages are queued while agent is offline
            sub = await self.js.subscribe(
                subject,
                durable=durable_name,
                cb=lambda msg: self._on_message(msg, callback),
                manual_ack=True,
            )
            self._subscriptions[agent_id] = sub
            logger.info(f"Subscribed agent {agent_id} to NATS subject {subject}")
        except Exception as e:
            logger.error(f"Failed to subscribe agent {agent_id}: {e}")

    async def subscribe_group(
        self, group_id: str, agent_id: str, callback: Callable[[AgentMessage], Any]
    ):
        """Subscribe an agent to a group subject"""
        if not self.js:
            return

        subject = f"daie.groups.{group_id}"
        # Use group-specific durable name combined with agent_id to allow multiple agents in same group
        durable_name = f"group_{group_id.replace('.', '_')}_{agent_id.replace('-', '_')}"

        try:
            sub = await self.js.subscribe(
                subject,
                durable=durable_name,
                cb=lambda msg: self._on_message(msg, callback),
                manual_ack=True,
            )
            subscription_key = f"group:{group_id}:{agent_id}"
            self._subscriptions[subscription_key] = sub
            logger.info(f"Subscribed agent {agent_id} to group {group_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to subscribe agent {agent_id} to group {group_id}: {e}")
            return False

    async def unsubscribe_group(self, group_id: str, agent_id: str):
        """Unsubscribe an agent from a group"""
        subscription_key = f"group:{group_id}:{agent_id}"
        if subscription_key in self._subscriptions:
            try:
                sub = self._subscriptions.pop(subscription_key)
                await sub.unsubscribe()
                logger.info(f"Unsubscribed agent {agent_id} from group {group_id}")
            except Exception as e:
                logger.error(f"Error unsubscribing agent from group: {e}")

    async def _on_message(self, nats_msg, callback):
        """Internal callback to handle NATS messages"""
        try:
            data = json.loads(nats_msg.data.decode())
            message = AgentMessage.from_dict(data)

            # Call back to communication manager / agent
            if asyncio.iscoroutinefunction(callback):
                await callback(message)
            else:
                callback(message)

            # Acknowledge message after successful processing
            await nats_msg.ack()
        except Exception as e:
            logger.error(f"Error processing NATS message: {e}")
            # Potentially nack if error is transient
            await nats_msg.nak()

    async def publish(self, message: AgentMessage):
        """Publish a message to an agent or broadcast"""
        if not self.js:
            logger.warning("NATS not connected, cannot publish")
            return False

        subject = (
            "daie.broadcast" if message.receiver_id == "*" else f"daie.agents.{message.receiver_id}"
        )

        try:
            payload = json.dumps(message.to_dict()).encode()
            await self.js.publish(subject, payload)
            logger.debug(f"Published message to {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish to NATS: {e}")
            return False

    async def disconnect(self):
        """Close NATS connection"""
        if self.nc:
            await self.nc.close()
            self._is_connected = False
            logger.info("Disconnected from NATS")

    @property
    def is_connected(self) -> bool:
        """Check if NATS is connected"""
        return self.nc is not None and self.nc.is_connected
