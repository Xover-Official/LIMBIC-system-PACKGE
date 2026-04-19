import asyncio
import logging
import multiprocessing
import functools
from typing import Any, Callable, Dict, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class Tool(BaseModel):
    name: str
    description: str
    func: Callable
    schema: Optional[Dict[str, Any]] = None
    is_sandboxed: bool = False

def _run_in_sandbox(func, params, result_queue):
    try:
        result = func(**params)
        result_queue.put({"success": True, "result": result})
    except Exception as e:
        result_queue.put({"success": False, "error": str(e)})

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register_tool(self, name: str, description: str, func: Callable, schema: Optional[Dict[str, Any]] = None, sandboxed: bool = False):
        self.tools[name] = Tool(name=name, description=description, func=func, schema=schema, is_sandboxed=sandboxed)
        logger.info(f"Registered tool: {name} (sandboxed={sandboxed})")

    async def execute(self, name: str, params: Dict[str, Any]) -> Any:
        if name not in self.tools:
            raise ValueError(f"Tool {name} not found in registry")
        
        tool = self.tools[name]
        logger.info(f"Executing tool {name} with params {params} (sandboxed={tool.is_sandboxed})")
        
        if tool.is_sandboxed:
            return await self._execute_sandboxed(tool, params)
        
        try:
            if asyncio.iscoroutinefunction(tool.func):
                result = await tool.func(**params)
            else:
                result = tool.func(**params)
            return result
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            raise

    async def _execute_sandboxed(self, tool: Tool, params: Dict[str, Any]) -> Any:
        # Multiprocessing for basic sandboxing (separate memory space)
        # Note: True sandboxing would require more isolation (e.g. seccomp, namespaces)
        if asyncio.iscoroutinefunction(tool.func):
            logger.warning(f"Async tool {tool.name} cannot be easily run in multiprocessing sandbox. Running unsandboxed.")
            return await tool.func(**params)

        result_queue = multiprocessing.Queue()
        process = multiprocessing.Process(
            target=_run_in_sandbox, 
            args=(tool.func, params, result_queue)
        )
        process.start()
        
        # Wait for result with a timeout
        loop = asyncio.get_event_loop()
        try:
            # We use a thread to wait for the queue to avoid blocking the event loop
            def wait_for_result():
                return result_queue.get(timeout=30)
            
            res = await loop.run_in_executor(None, wait_for_result)
            process.join()
            
            if res["success"]:
                return res["result"]
            else:
                raise Exception(res["error"])
        except Exception as e:
            process.terminate()
            logger.error(f"Sandbox error executing tool {tool.name}: {e}")
            raise
