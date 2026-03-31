"""
Configuration Manager for loading/saving JSON configs.
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Optional

from daie.agents.config import AgentConfig, AgentRole
from daie.config.system import SystemConfig

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Manages loading and saving of system and agent configurations via JSON.
    Searches first in `./config/` then in `~/.daie/`.
    Generates default JSON files at runtime if not found.
    """

    def __init__(self, override_dir: Optional[str] = None):
        self._local_dir = Path(os.getcwd()) / "config"
        self._global_dir = Path.home() / ".daie"

        if override_dir:
            self.config_dir = Path(override_dir)
        else:
            # Prefer local if it already exists, otherwise default to local to create it
            if self._local_dir.exists():
                self.config_dir = self._local_dir
            elif self._global_dir.exists():
                self.config_dir = self._global_dir
            else:
                self.config_dir = self._local_dir

        self.agents_file = self.config_dir / "agents.json"
        self.system_file = self.config_dir / "system.json"

    def ensure_directories(self):
        """Create configuration directory if it doesn't exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load_system_config(self) -> SystemConfig:
        """
        Loads the SystemConfig from `system.json`.
        If not found, creates a default one and saves it.
        """
        if not self.system_file.exists():
            logger.info(f"System config not found. Creating default at {self.system_file}")
            self.ensure_directories()
            default_config = SystemConfig()
            self.save_system_config(default_config)
            return default_config

        try:
            with open(self.system_file, "r") as f:
                data = json.load(f)
            return SystemConfig.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load system config: {e}. Falling back to default.")
            return SystemConfig()

    def save_system_config(self, config: SystemConfig) -> bool:
        """Saves a SystemConfig to `system.json`."""
        try:
            self.ensure_directories()
            with open(self.system_file, "w") as f:
                json.dump(config.to_dict(), f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Failed to save system config to {self.system_file}: {e}")
            return False

    def load_agents_config(self) -> List[AgentConfig]:
        """
        Loads multiple AgentConfigs from `agents.json`.
        If not found, creates an empty list (or a default agent) and saves it.
        """
        if not self.agents_file.exists():
            logger.info(f"Agents config not found. Creating default at {self.agents_file}")
            self.ensure_directories()
            # Create a single default agent for bootstrapping
            default_agent = AgentConfig(name="DefaultAgent", role=AgentRole.GENERAL_PURPOSE)
            self.save_agents_config([default_agent])
            return [default_agent]

        try:
            with open(self.agents_file, "r") as f:
                data = json.load(f)

            if not isinstance(data, list):
                logger.error("agents.json should contain a JSON array of agent objects")
                return []

            agents = []
            for agent_data in data:
                try:
                    agents.append(AgentConfig.from_dict(agent_data))
                except Exception as ex:
                    logger.error(f"Skipping an agent config due to error: {ex}")

            return agents
        except Exception as e:
            logger.error(f"Failed to load agents config from {self.agents_file}: {e}")
            return []

    def save_agents_config(self, agents: List[AgentConfig]) -> bool:
        """Saves a list of AgentConfig objects to `agents.json`."""
        try:
            self.ensure_directories()
            data = [agent.to_dict() for agent in agents]
            with open(self.agents_file, "w") as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Failed to save agents config to {self.agents_file}: {e}")
            return False

    def get_agent_config(self, name: str) -> Optional[AgentConfig]:
        """Fetch a specific AgentConfig by name."""
        agents = self.load_agents_config()
        for agent in agents:
            if agent.name == name:
                return agent
        return None

    def upsert_agent_config(self, agent_config: AgentConfig) -> bool:
        """Updates or inserts an AgentConfig by name."""
        agents = self.load_agents_config()
        # check if it exists
        updated = False
        for i, existing_agent in enumerate(agents):
            if existing_agent.name == agent_config.name:
                agents[i] = agent_config
                updated = True
                break

        if not updated:
            agents.append(agent_config)

        return self.save_agents_config(agents)
