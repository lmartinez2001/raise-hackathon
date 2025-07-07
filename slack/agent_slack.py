import asyncio
import json
from typing import Dict, Any, List
import logging
import os
import sys

from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    ListToolsResult,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

from slack.slack_database_handler import SlackDatabaseHandler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
logger = logging.getLogger(__name__)

class SlackMCPTools:
    """MCP tools for Slack database operations."""
    
    def __init__(self, database_path: str = "output/database/slack"):
        """Initialize the Slack MCP tools."""
        self.handler = SlackDatabaseHandler(database_path)
    
    def get_tools(self) -> List[Tool]:
        """Get the list of available tools."""
        return [
            Tool(
                name="slack_search_messages",
                description="Search for messages in the Slack database using text query",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query_text": {
                            "type": "string",
                            "description": "Text to search for in messages"
                        },
                        "channel_id": {
                            "type": "string",
                            "description": "Optional: Filter by specific channel ID"
                        },
                        "user_id": {
                            "type": "string",
                            "description": "Optional: Filter by specific user ID"
                        },
                        "date_from": {
                            "type": "string",
                            "description": "Optional: Start date for search (ISO format)"
                        },
                        "date_to": {
                            "type": "string",
                            "description": "Optional: End date for search (ISO format)"
                        },
                        "n_results": {
                            "type": "integer",
                            "description": "Number of results to return (default: 10)",
                            "default": 10
                        }
                    },
                    "required": ["query_text"]
                }
            ),
            Tool(
                name="slack_get_channel_messages",
                description="Get messages from a specific Slack channel",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "Channel ID to get messages from"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of messages to return (default: 100)",
                            "default": 100
                        },
                        "cursor": {
                            "type": "string",
                            "description": "Optional: Cursor for pagination"
                        }
                    },
                    "required": ["channel_id"]
                }
            ),
            Tool(
                name="slack_get_thread_replies",
                description="Get replies to a specific thread",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "Channel ID where the thread exists"
                        },
                        "thread_ts": {
                            "type": "string",
                            "description": "Thread timestamp to get replies for"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of replies to return (default: 100)",
                            "default": 100
                        }
                    },
                    "required": ["channel_id", "thread_ts"]
                }
            ),
            Tool(
                name="slack_get_channels",
                description="Get list of channels from the Slack database",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "channel_types": {
                            "type": "string",
                            "description": "Comma-separated channel types to include (default: public_channel,private_channel,im,mpim)",
                            "default": "public_channel,private_channel,im,mpim"
                        }
                    }
                }
            ),
            Tool(
                name="slack_get_stats",
                description="Get statistics about the Slack database",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            )
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> CallToolResult:
        """Call a specific tool."""
        try:
            if name == "slack_search_messages":
                result = self.handler.search_messages(
                    query_text=arguments["query_text"],
                    channel_id=arguments.get("channel_id"),
                    user_id=arguments.get("user_id"),
                    date_from=arguments.get("date_from"),
                    date_to=arguments.get("date_to"),
                    n_results=arguments.get("n_results", 10)
                )
                
            elif name == "slack_get_channel_messages":
                result = self.handler.get_messages_by_channel(
                    channel_id=arguments["channel_id"],
                    limit=arguments.get("limit", 100),
                    cursor=arguments.get("cursor")
                )
                
            elif name == "slack_get_thread_replies":
                result = self.handler.get_thread_replies(
                    channel_id=arguments["channel_id"],
                    thread_ts=arguments["thread_ts"],
                    limit=arguments.get("limit", 100)
                )
                
            elif name == "slack_get_channels":
                result = self.handler.get_channels(
                    channel_types=arguments.get("channel_types", "public_channel,private_channel,im,mpim")
                )
                
            elif name == "slack_get_stats":
                result = self.handler.get_collection_stats()
                
            else:
                raise ValueError(f"Unknown tool: {name}")
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(result, indent=2))]
            )
            
        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")]
            )

# Global instance
slack_tools = SlackMCPTools()

async def main():
    """Main function to run the Slack MCP server."""
    # Create stdio server
    server = stdio_server()
    
    @server.list_tools()
    async def handle_list_tools() -> ListToolsResult:
        """Handle list tools request."""
        return ListToolsResult(tools=slack_tools.get_tools())
    
    @server.call_tool()
    async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle tool call requests."""
        return await slack_tools.call_tool(name, arguments)
    
    # Run the server
    async with server.run_session() as session:
        await session.run()

if __name__ == "__main__":
    asyncio.run(main()) 