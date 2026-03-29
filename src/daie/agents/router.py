"""
Intelligent Agent Router Module

Provides LLM-based intelligent routing for selecting the most appropriate agent
to handle a given message based on content analysis.
"""

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class AgentRouter:
    """
    Intelligent agent router that uses LLM to select the best agent for a message.
    
    This router dynamically analyzes available agents and their capabilities,
    then routes messages to the most appropriate agent based on content analysis.
    
    Features:
    - Dynamic agent discovery from agent configs
    - Auto-generated routing prompts based on agent capabilities
    - Flexible agent type handling (works with any agent names)
    - Routing history tracking
    """
    
    def __init__(self, agents: Dict[str, Any], router_agent_name: Optional[str] = None):
        """
        Initialize the router with available agents.
        
        Args:
            agents: Dictionary mapping agent names to agent instances
            router_agent_name: Name of the agent to use for routing decisions.
                             If None, uses the first available agent.
        """
        self.agents = agents
        self.router_agent_name = router_agent_name or (list(agents.keys())[0] if agents else None)
        self._routing_history: List[Dict[str, str]] = []
        self._agent_descriptions: Dict[str, str] = {}
        
        # Auto-generate agent descriptions from configs
        self._build_agent_descriptions()
    
    @classmethod
    def from_agents(cls, agents_list: List[Any], router_agent_name: Optional[str] = None) -> 'AgentRouter':
        """
        Create a router from a list of agents.
        
        This is a convenience method that automatically creates a router
        from a list of agents, without requiring users to manually create
        a dictionary mapping.
        
        Args:
            agents_list: List of agent instances
            router_agent_name: Name of the agent to use for routing decisions.
                             If None, uses the first available agent.
        
        Returns:
            Configured AgentRouter instance
        
        Example:
            >>> from daie.agents import AgentRouter
            >>> # Create agents
            >>> assistant = Agent(config=AgentConfig(name="Assistant", role=AgentRole.GENERAL_PURPOSE))
            >>> coder = Agent(config=AgentConfig(name="Coder", role=AgentRole.SPECIALIZED))
            >>> researcher = Agent(config=AgentConfig(name="Researcher", role=AgentRole.SPECIALIZED))
            >>> # Create router automatically
            >>> router = AgentRouter.from_agents([assistant, coder, researcher])
            >>> # Or with specific router agent
            >>> router = AgentRouter.from_agents([assistant, coder, researcher], router_agent_name="assistant")
        """
        # Convert list to dictionary using agent names as keys
        agents_dict = {}
        for agent in agents_list:
            if hasattr(agent, 'name'):
                agents_dict[agent.name.lower()] = agent
            elif hasattr(agent, 'config') and hasattr(agent.config, 'name'):
                agents_dict[agent.config.name.lower()] = agent
            else:
                # Fallback to using index as key
                agents_dict[f"agent_{len(agents_dict)}"] = agent
        
        return cls(agents=agents_dict, router_agent_name=router_agent_name)
    
    def _build_agent_descriptions(self):
        """
        Automatically build agent descriptions from agent configs.
        
        Extracts information from agent config to create meaningful descriptions
        for the routing prompt.
        """
        for agent_name, agent in self.agents.items():
            try:
                # Try to get agent config
                if hasattr(agent, 'config'):
                    config = agent.config
                    
                    # Build description from config attributes
                    desc_parts = []
                    
                    # Add name if available
                    if hasattr(config, 'name'):
                        desc_parts.append(config.name)
                    
                    # Add role if available
                    if hasattr(config, 'role'):
                        role = config.role
                        if hasattr(role, 'value'):
                            desc_parts.append(f"Role: {role.value}")
                        else:
                            desc_parts.append(f"Role: {role}")
                    
                    # Add system prompt summary if available
                    if hasattr(config, 'system_prompt') and config.system_prompt:
                        # Extract first sentence or first 100 chars
                        prompt = config.system_prompt
                        first_sentence = prompt.split('.')[0] if '.' else prompt[:100]
                        desc_parts.append(f"Specialty: {first_sentence}")
                    
                    # Add personality if available
                    if hasattr(config, 'personality') and config.personality:
                        desc_parts.append(f"Style: {config.personality}")
                    
                    # Join all parts
                    if desc_parts:
                        self._agent_descriptions[agent_name] = ' | '.join(desc_parts)
                    else:
                        # Fallback to agent name
                        self._agent_descriptions[agent_name] = agent_name
                else:
                    # Fallback to agent name if no config
                    self._agent_descriptions[agent_name] = agent_name
                    
            except Exception as e:
                logger.warning(f"Could not extract description for agent '{agent_name}': {e}")
                self._agent_descriptions[agent_name] = agent_name
    
    def _generate_routing_prompt(self, message: str) -> str:
        """
        Dynamically generate routing prompt based on available agents.
        
        Args:
            message: User message to route
        
        Returns:
            Formatted routing prompt
        """
        # Build agent list with descriptions
        agent_list = []
        for agent_name, description in self._agent_descriptions.items():
            agent_list.append(f"- {agent_name}: {description}")
        
        agents_section = "\n".join(agent_list)
        
        # Get list of valid agent names for response
        valid_names = ", ".join(self._agent_descriptions.keys())
        
        # Generate the prompt with clear routing criteria
        prompt = f"""You are an intelligent message router. Analyze the user message and select the BEST agent to handle it.

**Available Agents:**
{agents_section}

**User Message:** "{message}"

**Routing Rules:**
- Choose the agent whose specialty BEST matches the message intent
- If message asks for CODE, PROGRAMMING, or TECHNICAL implementation → select the agent with coding/programming specialty
- If message asks for RESEARCH, ANALYSIS, or DATA → select the agent with research/analysis specialty
- For GENERAL QUESTIONS, EXPLANATIONS, or ADVICE → select the agent with general-purpose specialty

**Instructions:** Respond with ONLY the agent name ({valid_names}). No explanation needed.

**Selected Agent:**"""
        
        return prompt
    
    async def route(self, message: str, agent_type: Optional[str] = None) -> str:
        """
        Route a message to the appropriate agent.
        
        Args:
            message: User message to route
            agent_type: Specific agent type to use, or None/"auto" for intelligent routing
        
        Returns:
            Agent type string (name of the selected agent)
        """
        # If specific agent type is provided, use it
        if agent_type and agent_type != "auto":
            if agent_type in self.agents:
                return agent_type
            else:
                logger.warning(f"Agent type '{agent_type}' not found in available agents. Available: {list(self.agents.keys())}. Falling back to auto-routing.")
        
        # Use intelligent routing
        return await self._intelligent_route(message)
    
    async def _intelligent_route(self, message: str) -> str:
        """
        Use LLM to intelligently select the best agent.
        
        Args:
            message: User message to analyze
        
        Returns:
            Agent type string (name of selected agent)
        """
        # Get the router agent
        router_agent = self.agents.get(self.router_agent_name)
        if not router_agent:
            logger.error(f"Router agent '{self.router_agent_name}' not found. Available: {list(self.agents.keys())}")
            # Fallback to first available agent
            return list(self.agents.keys())[0] if self.agents else None
        
        try:
            # Generate dynamic routing prompt
            prompt = self._generate_routing_prompt(message)
            
            # Temporarily disable streaming to avoid printing routing decision
            from daie.core.llm_manager import get_llm_config
            original_stream = get_llm_config().stream
            get_llm_config().stream = False
            
            try:
                # Get routing decision from LLM
                decision = await router_agent.send_message(prompt)
            finally:
                # Restore original streaming setting
                get_llm_config().stream = original_stream
            
            decision_lower = decision.strip().lower()
            
            # Parse and validate the decision
            agent_type = self._parse_decision(decision_lower)
            
            # Log routing decision
            self._log_routing(message, agent_type, decision)
            
            return agent_type
            
        except Exception as e:
            logger.error(f"Error in intelligent routing: {e}", exc_info=True)
            # Fallback to first available agent
            return list(self.agents.keys())[0] if self.agents else None
    
    def _parse_decision(self, decision: str) -> str:
        """
        Parse and validate the LLM's routing decision.
        
        Args:
            decision: Raw decision string from LLM
        
        Returns:
            Validated agent type string
        """
        # Check for each available agent name in the decision
        for agent_name in self.agents.keys():
            if agent_name.lower() in decision:
                return agent_name
        
        # If no exact match, try partial matching
        for agent_name in self.agents.keys():
            # Check if any part of the agent name appears in the decision
            name_parts = agent_name.lower().split('_')
            for part in name_parts:
                if part in decision:
                    return agent_name
        
        # Fallback to first available agent
        return list(self.agents.keys())[0] if self.agents else None
    
    def _log_routing(self, message: str, agent_type: str, decision: str):
        """Log routing decision for debugging and analysis."""
        log_entry = {
            "message_preview": message[:100] + "..." if len(message) > 100 else message,
            "selected_agent": agent_type,
            "llm_decision": decision.strip()
        }
        self._routing_history.append(log_entry)
        logger.debug(f"Routed to {agent_type}: {message[:50]}...")
    
    def get_routing_history(self) -> List[Dict[str, str]]:
        """Get the history of routing decisions."""
        return self._routing_history.copy()
    
    def clear_routing_history(self):
        """Clear the routing history."""
        self._routing_history.clear()
    
    def get_agent_descriptions(self) -> Dict[str, str]:
        """Get the auto-generated agent descriptions."""
        return self._agent_descriptions.copy()
    
    def update_agent_description(self, agent_name: str, description: str):
        """
        Manually update an agent's description.
        
        Args:
            agent_name: Name of the agent
            description: Custom description to use in routing
        """
        if agent_name in self.agents:
            self._agent_descriptions[agent_name] = description
        else:
            logger.warning(f"Agent '{agent_name}' not found. Available: {list(self.agents.keys())}")


def create_router(agents: Dict[str, Any], router_agent_name: Optional[str] = None) -> AgentRouter:
    """
    Factory function to create an agent router.
    
    Automatically discovers available agents and generates routing logic
    based on agent configurations. Works with any agent types.
    
    Args:
        agents: Dictionary mapping agent names to agent instances
        router_agent_name: Name of the agent to use for routing decisions.
                         If None, automatically uses the first available agent.
    
    Returns:
        Configured AgentRouter instance
    
    Example:
        >>> from daie.agents.router import create_router
        >>> # Works with any agent types
        >>> router = create_router({
        ...     "assistant": assistant_agent,
        ...     "coder": coder_agent,
        ...     "researcher": researcher_agent,
        ...     "writer": writer_agent  # Any custom agent type
        ... })
        >>> agent_type = await router.route("Write a Python function to sort a list")
        >>> # Returns: "coder"
        >>> 
        >>> agent_type = await router.route("Write a creative story")
        >>> # Returns: "writer"
    """
    return AgentRouter(agents=agents, router_agent_name=router_agent_name)
