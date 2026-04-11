"""
Vision-Language multi-modal tools for agent perception.
"""

from typing import Any, Dict
from daie.tools.tool import Tool, ToolCategory, ToolMetadata, ToolParameter


class VisionAnalyzeTool(Tool):
    """
    Tool allowing agents to analyze or describe images using their underlying LLM.
    Requires a multi-modal capable LLM (e.g. llava, moondream, gpt-4o).
    """

    def __init__(self):
        metadata = ToolMetadata(
            name="vision_analyze",
            description="Analyze, describe, or answer questions about an image. Provide the image as a base64 string or URL.",
            category=ToolCategory.PERCEPTION,
            parameters=[
                ToolParameter(
                    name="image_data",
                    type="string",
                    description="Base64 encoded image or public URL",
                    required=True,
                ),
                ToolParameter(
                    name="query",
                    type="string",
                    description="What to look for or analyze in the image",
                    required=False,
                    default="Describe this image in detail.",
                ),
            ],
        )
        super().__init__(metadata)
        self._agent_ref = None

    def set_agent(self, agent):
        """Bind tool to an agent for access to its multi-modal LLM."""
        self._agent_ref = agent

    async def _execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        image_data = params.get("image_data")
        query = params.get("query", "Describe this image in detail.")

        if not image_data:
            return {"success": False, "error": "image_data is required"}

        if not self._agent_ref:
            return {"success": False, "error": "Tool not bound to an agent context."}

        try:
            # We use the agent's internal LLM invoke with image support
            from daie.core.llm_manager import get_llm_config

            cfg = get_llm_config()

            # Construct a special prompt for vision analysis
            prompt = f"IMAGE ANALYSIS REQUEST:\n{query}\n\n(The attached image is provided via multi-modal payload)"

            # Call LLM with image support
            # Note: We use the agent's configured LLM directly
            result = await self._agent_ref.llm.ainvoke(
                prompt, images=[image_data], temperature=0.1  # Low temperature for factual analysis
            )

            return {
                "success": True,
                "analysis": result.strip(),
                "image_ref": image_data[:50] + "..." if len(image_data) > 50 else image_data,
            }
        except Exception as e:
            return {"success": False, "error": f"Vision analysis failed: {str(e)}"}
