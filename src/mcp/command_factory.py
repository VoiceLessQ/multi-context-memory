"""
MCP Multi-Context Memory System
Copyright (c) 2024 VoiceLessQ
https://github.com/VoiceLessQ/multi-context-memory

This file is part of the MCP Multi-Context Memory System.
Licensed under the MIT License. See LICENSE file in the project root.

Project Fingerprint: 7a8f9b3c-mcpmem-voicelessq-2024
Original Author: VoiceLessQ
"""

"""
Command Factory for MCP commands using Factory pattern.
Replaces the monolithic command handling in mcp/server.py.
"""
import logging
from typing import Dict, Type, Optional, List
from .commands.base_command import Command, CommandContext, CommandResult
from .commands.memory_commands import (
    CreateMemoryCommand,
    GetMemoryCommand, 
    UpdateMemoryCommand,
    DeleteMemoryCommand,
    SearchMemoriesCommand,
    GetMemoryStatisticsCommand,
    CreateLargeMemoryCommand,
    BulkCreateMemoriesCommand
)

logger = logging.getLogger(__name__)


class CommandRegistry:
    """
    Registry for MCP commands using Registry pattern.
    Manages command registration and discovery.
    """
    
    def __init__(self):
        self._commands: Dict[str, Type[Command]] = {}
        self._register_default_commands()
    
    def register_command(self, command_class: Type[Command]) -> None:
        """Register a command class."""
        command_instance = command_class()
        command_name = command_instance.command_name
        
        if command_name in self._commands:
            logger.warning(f"Overwriting existing command: {command_name}")
        
        self._commands[command_name] = command_class
        logger.info(f"Registered command: {command_name}")
    
    def unregister_command(self, command_name: str) -> bool:
        """Unregister a command."""
        if command_name in self._commands:
            del self._commands[command_name]
            logger.info(f"Unregistered command: {command_name}")
            return True
        return False
    
    def get_command_class(self, command_name: str) -> Optional[Type[Command]]:
        """Get command class by name."""
        return self._commands.get(command_name)
    
    def list_commands(self) -> List[str]:
        """List all registered command names."""
        return list(self._commands.keys())
    
    def get_command_info(self) -> Dict[str, Dict]:
        """Get information about all registered commands."""
        info = {}
        for name, command_class in self._commands.items():
            command_instance = command_class()
            info[name] = command_instance.get_command_info()
        return info
    
    def _register_default_commands(self) -> None:
        """Register default MCP commands."""
        default_commands = [
            # Memory commands
            CreateMemoryCommand,
            GetMemoryCommand,
            UpdateMemoryCommand,
            DeleteMemoryCommand,
            SearchMemoriesCommand,
            GetMemoryStatisticsCommand,
            CreateLargeMemoryCommand,
            BulkCreateMemoriesCommand,
        ]
        
        for command_class in default_commands:
            self.register_command(command_class)


class CommandFactory:
    """
    Command Factory implementing Factory pattern.
    Creates command instances and handles execution.
    """
    
    def __init__(self, registry: Optional[CommandRegistry] = None):
        self.registry = registry or CommandRegistry()
        self._command_instances: Dict[str, Command] = {}
    
    def create_command(self, command_name: str) -> Optional[Command]:
        """
        Create command instance using Factory pattern.
        Uses singleton pattern for command instances.
        """
        # Return cached instance if available
        if command_name in self._command_instances:
            return self._command_instances[command_name]
        
        # Get command class from registry
        command_class = self.registry.get_command_class(command_name)
        if not command_class:
            logger.error(f"Unknown command: {command_name}")
            return None
        
        try:
            # Create and cache command instance
            command_instance = command_class()
            self._command_instances[command_name] = command_instance
            
            logger.debug(f"Created command instance: {command_name}")
            return command_instance
            
        except Exception as e:
            logger.error(f"Error creating command {command_name}: {e}")
            return None
    
    async def execute_command(
        self,
        command_name: str,
        context: CommandContext,
        data: Dict
    ) -> CommandResult:
        """
        Execute command with error handling and logging.
        """
        try:
            # Create command instance
            command = self.create_command(command_name)
            if not command:
                return CommandResult(
                    success=False,
                    data={},
                    error=f"Unknown command: {command_name}"
                )
            
            # Check if command can be executed
            if not await command.can_execute(context):
                return CommandResult(
                    success=False,
                    data={},
                    error=f"Insufficient permissions for command: {command_name}"
                )
            
            # Execute command
            logger.info(f"Executing command: {command_name} for user: {context.user_id}")
            result = await command.execute(context, data)
            
            # Log result
            if result.success:
                logger.info(f"Command {command_name} executed successfully")
            else:
                logger.warning(f"Command {command_name} failed: {result.error}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing command {command_name}: {e}")
            return CommandResult(
                success=False,
                data={},
                error=f"Command execution error: {str(e)}"
            )
    
    def get_supported_commands(self) -> List[str]:
        """Get list of supported commands."""
        return self.registry.list_commands()
    
    def get_command_help(self, command_name: Optional[str] = None) -> Dict:
        """Get help information for commands."""
        if command_name:
            command = self.create_command(command_name)
            if command:
                return command.get_command_info()
            else:
                return {"error": f"Unknown command: {command_name}"}
        else:
            return self.registry.get_command_info()
    
    def register_custom_command(self, command_class: Type[Command]) -> bool:
        """Register a custom command class."""
        try:
            self.registry.register_command(command_class)
            return True
        except Exception as e:
            logger.error(f"Error registering custom command: {e}")
            return False
    
    def clear_cache(self) -> None:
        """Clear cached command instances."""
        self._command_instances.clear()
        logger.info("Command instance cache cleared")


class CommandInvoker:
    """
    Command Invoker implementing Command pattern.
    Handles command queuing, batching, and async execution.
    """
    
    def __init__(self, factory: CommandFactory):
        self.factory = factory
        self._command_queue: List[tuple] = []
        self._batch_size = 10
    
    async def invoke_command(
        self,
        command_name: str,
        context: CommandContext,
        data: Dict,
        immediate: bool = True
    ) -> CommandResult:
        """
        Invoke command immediately or queue for batch processing.
        """
        if immediate:
            return await self.factory.execute_command(command_name, context, data)
        else:
            # Queue command for batch processing
            self._command_queue.append((command_name, context, data))
            return CommandResult(
                success=True,
                data={"message": "Command queued for batch processing"},
                metadata={"queued": True, "queue_position": len(self._command_queue)}
            )
    
    async def process_batch(self) -> List[CommandResult]:
        """Process queued commands in batch."""
        if not self._command_queue:
            return []
        
        results = []
        batch = self._command_queue[:self._batch_size]
        self._command_queue = self._command_queue[self._batch_size:]
        
        logger.info(f"Processing batch of {len(batch)} commands")
        
        for command_name, context, data in batch:
            try:
                result = await self.factory.execute_command(command_name, context, data)
                results.append(result)
            except Exception as e:
                logger.error(f"Error in batch processing command {command_name}: {e}")
                results.append(CommandResult(
                    success=False,
                    data={},
                    error=f"Batch processing error: {str(e)}"
                ))
        
        return results
    
    def get_queue_status(self) -> Dict[str, int]:
        """Get command queue status."""
        return {
            "queue_length": len(self._command_queue),
            "batch_size": self._batch_size
        }
    
    def set_batch_size(self, size: int) -> None:
        """Set batch processing size."""
        if size > 0:
            self._batch_size = size
            logger.info(f"Batch size set to: {size}")
    
    def clear_queue(self) -> int:
        """Clear command queue and return number of cleared commands."""
        cleared_count = len(self._command_queue)
        self._command_queue.clear()
        logger.info(f"Cleared {cleared_count} commands from queue")
        return cleared_count


class CommandPipeline:
    """
    Command Pipeline for processing multiple commands in sequence.
    Implements Pipeline pattern for command chaining.
    """
    
    def __init__(self, invoker: CommandInvoker):
        self.invoker = invoker
        self._pipeline_steps: List[Dict] = []
    
    def add_step(
        self,
        command_name: str,
        data: Dict,
        condition: Optional[str] = None
    ) -> 'CommandPipeline':
        """Add a step to the pipeline."""
        self._pipeline_steps.append({
            "command_name": command_name,
            "data": data,
            "condition": condition
        })
        return self
    
    async def execute_pipeline(self, context: CommandContext) -> List[CommandResult]:
        """Execute all pipeline steps in sequence."""
        results = []
        pipeline_context = {"previous_results": []}
        
        for i, step in enumerate(self._pipeline_steps):
            try:
                # Check condition if specified
                if step["condition"] and not self._evaluate_condition(
                    step["condition"], 
                    pipeline_context
                ):
                    logger.info(f"Skipping step {i}: condition not met")
                    continue
                
                # Execute command
                result = await self.invoker.invoke_command(
                    step["command_name"],
                    context,
                    step["data"]
                )
                
                results.append(result)
                pipeline_context["previous_results"].append(result)
                
                # Stop pipeline if command failed and no error handling
                if not result.success and step.get("stop_on_error", True):
                    logger.warning(f"Pipeline stopped at step {i}: {result.error}")
                    break
                
            except Exception as e:
                logger.error(f"Error in pipeline step {i}: {e}")
                error_result = CommandResult(
                    success=False,
                    data={},
                    error=f"Pipeline step {i} error: {str(e)}"
                )
                results.append(error_result)
                break
        
        return results
    
    def _evaluate_condition(self, condition: str, context: Dict) -> bool:
        """Evaluate pipeline condition (simplified)."""
        # Simple condition evaluation
        # In a real implementation, you'd have a proper expression evaluator
        if condition == "previous_success":
            return (
                context["previous_results"] and 
                context["previous_results"][-1].success
            )
        elif condition == "previous_failure":
            return (
                context["previous_results"] and 
                not context["previous_results"][-1].success
            )
        else:
            return True
    
    def clear(self) -> 'CommandPipeline':
        """Clear pipeline steps."""
        self._pipeline_steps.clear()
        return self
    
    def get_pipeline_info(self) -> Dict:
        """Get information about the pipeline."""
        return {
            "step_count": len(self._pipeline_steps),
            "steps": [
                {
                    "index": i,
                    "command": step["command_name"],
                    "condition": step.get("condition")
                }
                for i, step in enumerate(self._pipeline_steps)
            ]
        }