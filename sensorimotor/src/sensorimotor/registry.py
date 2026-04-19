import asyncio
import logging
from typing import Any, Callable, Dict, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class Tool(BaseModel):
    name: str
    description: str
    func: Callable
    schema: Optional[Dict[str, Any]] = None

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register_tool(self, name: str, description: str, func: Callable, schema: Optional[Dict[str, Any]] = None):
        self.tools[name] = Tool(name=name, description=description, func=func, schema=schema)
        logger.info(f"Registered tool: {name}")

    async def execute(self, name: str, params: Dict[str, Any]) -> Any:
        if name not in self.tools:
            raise ValueError(f"Tool {name} not found in registry")
        
        tool = self.tools[name]
        logger.info(f"Executing tool {name} with params {params}")
        
        try:
            if asyncio.iscoroutinefunction(tool.func):
                result = await tool.func(**params)
            else:
                result = tool.func(**params)
            return result
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            raise
