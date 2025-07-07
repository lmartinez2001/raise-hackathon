import asyncio
import json
import argparse
from typing import Dict, Any, List, Optional, Tuple
import logging
import os
import sys

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.lowlevel.server import NotificationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    ListToolsResult,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
from smolagents import CodeAgent, InferenceClientModel, tool

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), ""))
from slack.slack_database_handler import SlackDatabaseHandler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
logger = logging.getLogger(__name__)

class SlackMCPTools:
    """MCP tools for Slack database operations."""
    
    def __init__(self, database_path: str, collection_name: str):
        """Initialize the Slack MCP tools."""
        self.handler = SlackDatabaseHandler(database_path, collection_name)
    
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

@tool
def search_slack_messages(
    database_path: str,
    collection_name: str,
    query_text: str,
    channel_id: Optional[str] = None,
    user_id: Optional[str] = None,
    n_results: int = 5,
) -> Tuple[List[str], List[str], List[str], List[str], List[bool]]:
    """Search for messages in the Slack database.
    
    Args:
        database_path: Path to the database
        collection_name: Name of the collection to query
        query_text: Text to search for in messages
        channel_id: Optional: Filter by specific channel ID
        user_id: Optional: Filter by specific user ID
        n_results: Number of results to return (default: 5)
        
    Returns:
        usernames: List of usernames who sent the messages
        channel_names: List of channel names where messages were sent
        message_texts: List of message texts
        timestamps: List of message timestamps
        is_thread_replies: List of boolean indicating if messages are thread replies
    """
    # Initialize the Slack tools
    tools = SlackMCPTools(database_path, collection_name)
    
    # Prepare arguments
    arguments = {
        "query_text": query_text,
        "n_results": n_results
    }
    
    if channel_id:
        arguments["channel_id"] = channel_id
    if user_id:
        arguments["user_id"] = user_id
    
    # Call the tool
    result = asyncio.run(tools.call_tool("slack_search_messages", arguments))
    
    # Parse the result
    messages_data = json.loads(result.content[0].text)
    messages = messages_data.get("results", [])
    
    # Extract data
    usernames = [msg.get("username", "Unknown") for msg in messages]
    channel_names = [msg.get("channel_name", "Unknown") for msg in messages]
    message_texts = [msg.get("text", "No text") for msg in messages]
    timestamps = [msg.get("timestamp", "Unknown") for msg in messages]
    is_thread_replies = [msg.get("is_thread_reply", False) for msg in messages]
    
    return (usernames, channel_names, message_texts, timestamps, is_thread_replies)


@tool
def get_slack_channels(
    database_path: str,
    collection_name: str,
) -> Tuple[List[str], List[str], List[int], List[bool]]:
    """Get list of channels from the Slack database.
    
    Args:
        database_path: Path to the database
        collection_name: Name of the collection to query
        
    Returns:
        channel_names: List of channel names
        channel_ids: List of channel IDs
        member_counts: List of member counts
        is_private: List of boolean indicating if channels are private
    """
    # Initialize the Slack tools
    tools = SlackMCPTools(database_path, collection_name)
    
    # Call the tool
    result = asyncio.run(tools.call_tool("slack_get_channels", {}))
    
    # Parse the result
    channels = json.loads(result.content[0].text)
    
    # Extract data
    channel_names = [channel.get("name", "Unknown") for channel in channels]
    channel_ids = [channel.get("channel_id", "Unknown") for channel in channels]
    member_counts = [channel.get("member_count", 0) for channel in channels]
    is_private = [channel.get("is_private", False) for channel in channels]
    
    return (channel_names, channel_ids, member_counts, is_private)


@tool
def get_slack_statistics(
    database_path: str,
    collection_name: str,
) -> Tuple[int, int, int, int]:
    """Get statistics about the Slack database.
    
    Args:
        database_path: Path to the database
        collection_name: Name of the collection to query
        
    Returns:
        total_messages: Total number of messages
        total_channels: Total number of channels
        unique_users: Number of unique users
        total_documents: Total number of documents
    """
    # Initialize the Slack tools
    tools = SlackMCPTools(database_path, collection_name)
    
    # Call the tool
    result = asyncio.run(tools.call_tool("slack_get_stats", {}))
    
    # Parse the result
    stats = json.loads(result.content[0].text)
    
    return (
        stats.get("total_messages", 0),
        stats.get("total_channels", 0),
        stats.get("unique_users", 0),
        stats.get("total_documents", 0)
    )


@tool
def get_channel_messages(
    database_path: str,
    collection_name: str,
    channel_id: str,
    limit: int = 10,
) -> Tuple[List[str], List[str], List[str], List[str]]:
    """Get messages from a specific Slack channel.
    
    Args:
        database_path: Path to the database
        collection_name: Name of the collection to query
        channel_id: Channel ID to get messages from
        limit: Maximum number of messages to return (default: 10)
        
    Returns:
        usernames: List of usernames who sent the messages
        message_texts: List of message texts
        timestamps: List of message timestamps
        thread_ts: List of thread timestamps (if applicable)
    """
    # Initialize the Slack tools
    tools = SlackMCPTools(database_path, collection_name)
    
    # Call the tool
    result = asyncio.run(tools.call_tool("slack_get_channel_messages", {
        "channel_id": channel_id,
        "limit": limit
    }))
    
    # Parse the result
    messages_data = json.loads(result.content[0].text)
    messages = messages_data.get("messages", [])
    
    # Extract data
    usernames = [msg.get("username", "Unknown") for msg in messages]
    message_texts = [msg.get("text", "No text") for msg in messages]
    timestamps = [msg.get("timestamp", "Unknown") for msg in messages]
    thread_ts = [msg.get("thread_ts", None) for msg in messages]
    
    return (usernames, message_texts, timestamps, thread_ts)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="SmolAgent for querying Slack database using natural language.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        python slack_agent.py --database output/database/slack --collection slack_data --query "What was discussed about meetings?"
        python slack_agent.py --database output/database/slack --collection slack_data --query "Show me all channels and their member counts"
        python slack_agent.py --database output/database/slack --collection slack_data --query "Find messages from gaubil.julien about deadlines"
        """
    )
    
    parser.add_argument(
        "--database_path", "-d",
        type=str,
        required=True,
        help="Path to ChromaDB database directory"
    )
    
    parser.add_argument(
        "--collection_name", "-c",
        type=str,
        required=True,
        help="ChromaDB collection name"
    )
    
    parser.add_argument(
        "--query", "-q",
        type=str,
        required=True,
        help="Query to ask the agent"
    )
    
    parser.add_argument(
        "--max-steps", "-s",
        type=int,
        default=5,
        help="Maximum number of agent steps (default: 5)"
    )
    
    return parser.parse_args()


if __name__ == "__main__":
    import os

    # Parse command line arguments
    args = parse_arguments()
    
    # Extract arguments
    database_path = args.database_path
    collection_name = args.collection_name
    query = args.query
    max_steps = args.max_steps

    # Initialize model and agent
    model = InferenceClientModel()
    agent = CodeAgent(
        model=model,
        name="slack_agent", 
        description="An agent to query the Slack database for messages, channels, and statistics using natural language.",
        tools=[search_slack_messages, get_slack_channels, get_slack_statistics, get_channel_messages],
        max_steps=max_steps,
    )

    # Run the agent and capture the result
    agent_query = f"""Query the Slack collection '{collection_name}' in the database at '{database_path}' to answer: '{query}'. 
        Use the available tools to search for messages, get channel information, and retrieve statistics as needed. 
        In your answer, include relevant message content, usernames, channel names, and timestamps when applicable.
        
        IMPORTANT DATA FORMAT NOTES:
        - search_slack_messages() returns: (usernames, channel_names, message_texts, timestamps, is_thread_replies)
        - get_slack_channels() returns: (channel_names, channel_ids, member_counts, is_private)
        - get_slack_statistics() returns: (total_messages, total_channels, unique_users, total_documents)
        - get_channel_messages() returns: (usernames, message_texts, timestamps, thread_ts)
        
        All functions return tuples of lists, not dictionaries or lists of dictionaries.
        When processing results, use zip() to combine the lists into message objects.
        
        Example:
        usernames, channel_names, message_texts, timestamps, is_thread_replies = search_slack_messages(...)
        for username, channel_name, text, timestamp, is_thread in zip(usernames, channel_names, message_texts, timestamps, is_thread_replies):
            print(f"User: {{username}}, Channel: {{channel_name}}, Message: {{text}}, Time: {{timestamp}}")"""
    result = agent.run(agent_query)

    # Print the final result
    print("\n" + "="*60)
    print("SLACK AGENT RESULT:")
    print("="*60) 
    print(f"Query: {query}")
    print(f"Result: {result}") 