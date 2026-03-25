"""
Agent Connect Protocol (ACP) module with I/O Mappers.
"""

from typing import Dict, Any, Callable, Optional
import json
import logging

logger = logging.getLogger(__name__)


class IOMapper:
    """
    I/O Mapper for Agent Connect Protocol.
    Maps output values from a source context cleanly into a destination context.
    """

    def __init__(self, mapping_rules: Dict[str, str] = None):
        """
        Initialize the I/O Mapper with a dictionary of rules.
        A rule like: {"dest_key": "source_key"} means that the output's 
        'source_key' will be mapped to the input's 'dest_key'.
        """
        self.mapping_rules = mapping_rules or {}

    def apply(self, output_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply the mapping rules to the given context.
        """
        mapped_input = {}
        for dest_key, source_key in self.mapping_rules.items():
            if source_key in output_context:
                mapped_input[dest_key] = output_context[source_key]
        return mapped_input


class AgentConnectProtocol:
    """
    Implements the Agent Connect Protocol.
    Mediates interaction between two agents using an I/O Mapper.
    """
    
    def __init__(self, mapper: Optional[IOMapper] = None):
        self.mapper = mapper or IOMapper()

    def map_request(self, output_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps an outgoing payload to an appropriate input context for the receiving agent.
        """
        if not self.mapper.mapping_rules:
            # If no specific rules, pass through as direct payload
            return output_payload
        
        return self.mapper.apply(output_payload)

    def map_response(self, response_payload: Dict[str, Any], response_mapper: Optional[IOMapper] = None) -> Dict[str, Any]:
        """
        Maps a response back to the requesting agent.
        """
        if not response_mapper or not response_mapper.mapping_rules:
            return response_payload
            
        return response_mapper.apply(response_payload)
