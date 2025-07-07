#!/usr/bin/env python3
"""
Slack Database Handler for MCP
Integrates with ChromaDB to store and retrieve Slack messages, channels, and conversations.
"""

import os
import sys
import logging
import asyncio
import argparse
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
import chromadb

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the current directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), ""))

from database import ChromaDB

@dataclass
class SlackMessage:
    """Represents a Slack message with metadata."""
    message_id: str
    channel_id: str
    channel_name: str
    user_id: str
    username: str
    text: str
    timestamp: str
    thread_ts: Optional[str] = None
    is_thread_reply: bool = False
    attachments: List[Dict[str, Any]] = None
    reactions: List[Dict[str, Any]] = None
    permalink: Optional[str] = None

@dataclass
class SlackChannel:
    """Represents a Slack channel."""
    channel_id: str
    name: str
    is_private: bool
    is_im: bool
    is_mpim: bool
    member_count: int
    topic: Optional[str] = None
    purpose: Optional[str] = None

class SlackDatabaseHandler(ChromaDB):
    """Handles Slack data storage and retrieval using ChromaDB."""
    
    def __init__(self, database_path: str, collection_name: str):
        """Initialize the Slack database handler."""
        self.database_path = database_path
        self.collection_name = collection_name
        
        # Ensure database directory exists
        os.makedirs(database_path, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=database_path)
        
        # Get or create collection
        if collection_name in [col.name for col in self.client.list_collections()]:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Using existing collection: {collection_name}")
        else:
            self.collection = self.client.create_collection(name=collection_name)
            logger.info(f"Created new collection: {collection_name}")

    def import_from_slack_api(self, slack_token: str, include_bot_messages: bool = False, max_messages_per_channel: Optional[int] = None):
        """
        Import data directly from Slack API.
        Requires a Slack bot token with appropriate scopes.
        
        Args:
            slack_token: Slack bot token
            include_bot_messages: Whether to include bot messages (default: False)
            max_messages_per_channel: Maximum number of messages to import per channel (None = no limit)
        """
        import aiohttp
        
        async def fetch_channels():
            """Fetch channel list from Slack API."""
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {slack_token}"}
                
                # Get channels list
                async with session.get(
                    "https://slack.com/api/conversations.list",
                    headers=headers
                ) as response:
                    data = await response.json()
                    if data["ok"]:
                        return data["channels"]
                    else:
                        raise Exception(f"Slack API error: {data['error']}")
        
        async def join_channel(channel_id: str):
            """Join a channel if not already a member."""
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {slack_token}"}
                
                async with session.post(
                    "https://slack.com/api/conversations.join",
                    headers=headers,
                    json={"channel": channel_id}
                ) as response:
                    data = await response.json()
                    return data["ok"]
        
        async def fetch_messages(channel_id: str):
            """Fetch ALL messages from a specific channel with pagination."""
            all_messages = []
            cursor = None
            
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {slack_token}"}
                
                while True:
                    params = {
                        "channel": channel_id, 
                        "limit": 1000  # Slack API maximum per request
                    }
                    if cursor:
                        params["cursor"] = cursor
                    
                    async with session.get(
                        "https://slack.com/api/conversations.history",
                        headers=headers,
                        params=params
                    ) as response:
                        data = await response.json()
                        if data["ok"]:
                            messages = data["messages"]
                            all_messages.extend(messages)
                            
                            # Check if there are more messages
                            if data.get("has_more", False) and data.get("response_metadata", {}).get("next_cursor"):
                                cursor = data["response_metadata"]["next_cursor"]
                                print(f"      Fetching more messages... (have {len(all_messages)} so far)")
                            else:
                                break
                        else:
                            if data["error"] == "not_in_channel":
                                # Try to join the channel first
                                print(f"    Trying to join channel {channel_id}...")
                                if await join_channel(channel_id):
                                    # Retry fetching messages
                                    async with session.get(
                                        "https://slack.com/api/conversations.history",
                                        headers=headers,
                                        params=params
                                    ) as retry_response:
                                        retry_data = await retry_response.json()
                                        if retry_data["ok"]:
                                            messages = retry_data["messages"]
                                            all_messages.extend(messages)
                                            
                                            # Check if there are more messages
                                            if retry_data.get("has_more", False) and retry_data.get("response_metadata", {}).get("next_cursor"):
                                                cursor = retry_data["response_metadata"]["next_cursor"]
                                                print(f"      Fetching more messages... (have {len(all_messages)} so far)")
                                            else:
                                                break
                                        else:
                                            raise Exception(f"Slack API error after joining: {retry_data['error']}")
                                else:
                                    raise Exception("Failed to join channel")
                            else:
                                raise Exception(f"Slack API error: {data['error']}")
            
            return all_messages
        
        async def fetch_users():
            """Fetch user list for username mapping."""
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {slack_token}"}
                
                async with session.get(
                    "https://slack.com/api/users.list",
                    headers=headers
                ) as response:
                    data = await response.json()
                    if data["ok"]:
                        users = data.get("members", [])  # Use 'members' instead of 'users'
                        return {user["id"]: user["name"] for user in users}
                    else:
                        print(f"Warning: Could not fetch users: {data['error']}")
                        return {}
        
        async def import_data():
            """Main import function."""
            print("Importing data from Slack API...")
            print("\nNote: The bot may need to be invited to channels to access messages.")
            print("If you see 'not_in_channel' errors, the bot will attempt to join automatically.")
            print("For private channels, you may need to manually invite the bot.")
            print()
            
            # Fetch users for username mapping
            users = await fetch_users()
            
            # Fetch channels
            channels_data = await fetch_channels()
            
            # Filter channels if specified
            print(f"Found {len(channels_data)} channels to import")
            
            # Import channels
            for channel_data in channels_data:
                channel = SlackChannel(
                    channel_id=channel_data["id"],
                    name=channel_data["name"],
                    is_private=channel_data.get("is_private", False),
                    is_im=channel_data.get("is_im", False),
                    is_mpim=channel_data.get("is_mpim", False),
                    member_count=channel_data.get("num_members", 0),
                    topic=channel_data.get("topic", {}).get("value"),
                    purpose=channel_data.get("purpose", {}).get("value")
                )
                
                self.store_channel(channel)
                print(f"  ✓ Imported channel: #{channel.name}")
                
                # Skip message import for private channels if bot can't access
                if channel_data.get("is_private", False):
                    print(f"    ⚠ Skipping private channel #{channel.name} (may need manual bot invite)")
                    continue
                
                # Fetch and import messages
                try:
                    print(f"    Fetching messages from #{channel.name}...")
                    messages_data = await fetch_messages(channel_data["id"])
                    print(f"    Found {len(messages_data)} messages in #{channel.name}")
                    
                    imported_count = 0
                    skipped_bot_count = 0
                    for msg_data in messages_data:
                        # Skip bot messages unless explicitly requested
                        if not include_bot_messages and msg_data.get("bot_id"):
                            skipped_bot_count += 1
                            continue
                        
                        # Check if we've reached the maximum messages per channel
                        if max_messages_per_channel and imported_count >= max_messages_per_channel:
                            print(f"    ⚠ Reached maximum messages limit ({max_messages_per_channel}) for #{channel.name}")
                            break
                        
                        # Get username from users mapping
                        user_id = msg_data.get("user", "unknown")
                        username = users.get(user_id, user_id)
                        
                        message = SlackMessage(
                            message_id=msg_data["ts"],
                            channel_id=channel_data["id"],
                            channel_name=channel_data["name"],
                            user_id=user_id,
                            username=username,
                            text=msg_data.get("text", ""),
                            timestamp=msg_data["ts"],
                            thread_ts=msg_data.get("thread_ts"),
                            is_thread_reply=bool(msg_data.get("thread_ts")),
                            attachments=msg_data.get("attachments", []),
                            reactions=msg_data.get("reactions", []),
                            permalink=msg_data.get("permalink")
                        )
                        
                        self.store_message(message)
                        imported_count += 1
                    
                    print(f"    ✓ Imported {imported_count} messages from #{channel.name}")
                    if skipped_bot_count > 0:
                        print(f"    ⚠ Skipped {skipped_bot_count} bot messages from #{channel.name}")
                    
                except Exception as e:
                    print(f"    ⚠ Error importing messages from #{channel.name}: {e}")
                    if "not_in_channel" in str(e):
                        print(f"      Tip: Invite the bot to #{channel.name} or make it public")
        
        # Run the import
        asyncio.run(import_data())
    
    def store_message(self, message: SlackMessage) -> str:
        """Store a Slack message in the database."""
        document_id = f"msg_{message.channel_id}_{message.message_id}"
        
        # Create metadata
        metadata = {
            "data_type": "slack_message",
            "message_id": message.message_id,
            "channel_id": message.channel_id,
            "channel_name": message.channel_name,
            "user_id": message.user_id,
            "username": message.username,
            "timestamp": message.timestamp,
            "thread_ts": message.thread_ts,
            "is_thread_reply": message.is_thread_reply,
            "stored_timestamp": datetime.now().isoformat(),
            "permalink": message.permalink
        }
        
        # Store attachments and reactions as JSON strings
        if message.attachments:
            metadata["attachments"] = json.dumps(message.attachments)
        if message.reactions:
            metadata["reactions"] = json.dumps(message.reactions)
        # Remove None values from metadata
        metadata = {k: v for k, v in metadata.items() if v is not None}
        
        # Add to collection
        self.collection.add(
            documents=[message.text],
            metadatas=[metadata],
            ids=[document_id]
        )
        
        logger.info(f"Stored message: {document_id}")
        return document_id
    
    def store_channel(self, channel: SlackChannel) -> str:
        """Store a Slack channel in the database."""
        document_id = f"channel_{channel.channel_id}"
        
        # Create metadata
        metadata = {
            "data_type": "slack_channel",
            "channel_id": channel.channel_id,
            "name": channel.name,
            "is_private": channel.is_private,
            "is_im": channel.is_im,
            "is_mpim": channel.is_mpim,
            "member_count": channel.member_count,
            "topic": channel.topic,
            "purpose": channel.purpose,
            "stored_timestamp": datetime.now().isoformat()
        }
        # Remove None values from metadata
        metadata = {k: v for k, v in metadata.items() if v is not None}
        
        # Use channel name as document text for searchability
        document_text = f"Channel: {channel.name}"
        if channel.topic:
            document_text += f" - {channel.topic}"
        if channel.purpose:
            document_text += f" - {channel.purpose}"
        
        # Add to collection
        self.collection.add(
            documents=[document_text],
            metadatas=[metadata],
            ids=[document_id]
        )
        
        logger.info(f"Stored channel: {document_id}")
        return document_id
    
    def search_messages(
        self,
        query_text: str,
        channel_id: Optional[str] = None,
        user_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        n_results: int = 10
    ) -> Dict[str, Any]:
        """Search for messages in the database."""
        
        # Build where filter
        where_filter = {"data_type": "slack_message"}
        
        if channel_id:
            where_filter["channel_id"] = channel_id
        if user_id:
            where_filter["user_id"] = user_id
        
        # Add date range filter if provided
        if date_from or date_to:
            date_filter = {}
            if date_from:
                date_filter["$gte"] = date_from
            if date_to:
                date_filter["$lte"] = date_to
            where_filter["timestamp"] = date_filter
        
        # If more than one filter, use $and
        if len(where_filter) > 1:
            and_filters = [{k: v} for k, v in where_filter.items()]
            where_filter = {"$and": and_filters}
        
        # Query the collection
        results = self.collection.query(
            query_texts=[query_text],
            where=where_filter,
            n_results=n_results
        )
        
        # Format results
        messages = []
        # ChromaDB returns lists of lists for query results
        metadatas = results["metadatas"][0] if results["metadatas"] else []
        documents = results["documents"][0] if results["documents"] else []
        distances = results["distances"][0] if results.get("distances") else []
        for i in range(len(results["ids"][0])):
            metadata = metadatas[i]
            message = {
                "message_id": metadata.get("message_id"),
                "channel_id": metadata.get("channel_id"),
                "channel_name": metadata.get("channel_name"),
                "user_id": metadata.get("user_id"),
                "username": metadata.get("username"),
                "text": documents[i],
                "timestamp": metadata.get("timestamp"),
                "thread_ts": metadata.get("thread_ts"),
                "is_thread_reply": metadata.get("is_thread_reply", False),
                "permalink": metadata.get("permalink"),
                "distance": distances[i] if distances else None
            }
            # Parse attachments and reactions
            if metadata.get("attachments"):
                try:
                    message["attachments"] = json.loads(metadata["attachments"])
                except:
                    message["attachments"] = []
            if metadata.get("reactions"):
                try:
                    message["reactions"] = json.loads(metadata["reactions"])
                except:
                    message["reactions"] = []
            messages.append(message)
        
        return {
            "query": query_text,
            "results": messages,
            "total_found": len(messages)
        }
    
    def get_messages_by_channel(
        self,
        channel_id: str,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get messages from a specific channel."""
        
        where_filter = {
            "$and": [
                {"data_type": "slack_message"},
                {"channel_id": channel_id}
            ]
        }
        
        # Get messages
        results = self.collection.get(
            where=where_filter,
            limit=limit
        )
        
        messages = []
        for i in range(len(results["ids"])):
            metadata = results["metadatas"][i]
            message = {
                "message_id": metadata.get("message_id"),
                "channel_id": metadata.get("channel_id"),
                "channel_name": metadata.get("channel_name"),
                "user_id": metadata.get("user_id"),
                "username": metadata.get("username"),
                "text": results["documents"][i],
                "timestamp": metadata.get("timestamp"),
                "thread_ts": metadata.get("thread_ts"),
                "is_thread_reply": metadata.get("is_thread_reply", False),
                "permalink": metadata.get("permalink")
            }
            
            # Parse attachments and reactions
            if metadata.get("attachments"):
                try:
                    message["attachments"] = json.loads(metadata["attachments"])
                except:
                    message["attachments"] = []
            
            if metadata.get("reactions"):
                try:
                    message["reactions"] = json.loads(metadata["reactions"])
                except:
                    message["reactions"] = []
            
            messages.append(message)
        
        return {
            "channel_id": channel_id,
            "messages": messages,
            "total_messages": len(messages)
        }
    
    def get_thread_replies(
        self,
        channel_id: str,
        thread_ts: str,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get replies to a specific thread."""
        
        where_filter = {
            "$and": [
                {"data_type": "slack_message"},
                {"channel_id": channel_id},
                {"thread_ts": thread_ts},
                {"is_thread_reply": True}
            ]
        }
        
        results = self.collection.get(
            where=where_filter,
            limit=limit
        )
        
        replies = []
        for i in range(len(results["ids"])):
            metadata = results["metadatas"][i]
            reply = {
                "message_id": metadata.get("message_id"),
                "user_id": metadata.get("user_id"),
                "username": metadata.get("username"),
                "text": results["documents"][i],
                "timestamp": metadata.get("timestamp"),
                "permalink": metadata.get("permalink")
            }
            
            # Parse attachments and reactions
            if metadata.get("attachments"):
                try:
                    reply["attachments"] = json.loads(metadata["attachments"])
                except:
                    reply["attachments"] = []
            
            if metadata.get("reactions"):
                try:
                    reply["reactions"] = json.loads(metadata["reactions"])
                except:
                    reply["reactions"] = []
            
            replies.append(reply)
        
        return {
            "channel_id": channel_id,
            "thread_ts": thread_ts,
            "replies": replies,
            "total_replies": len(replies)
        }
    
    def get_channels(self, channel_types: str = "public_channel,private_channel,im,mpim") -> List[Dict[str, Any]]:
        """Get list of channels from the database."""
        
        where_filter = {
            "$and": [
                {"data_type": "slack_channel"}
            ]
        }
        # If only one filter, use plain dict
        if len(where_filter["$and"]) == 1:
            where_filter = where_filter["$and"][0]
        
        results = self.collection.get(where=where_filter)
        
        channels = []
        for i in range(len(results["ids"])):
            metadata = results["metadatas"][i]
            channel = {
                "channel_id": metadata.get("channel_id"),
                "name": metadata.get("name"),
                "is_private": metadata.get("is_private", False),
                "is_im": metadata.get("is_im", False),
                "is_mpim": metadata.get("is_mpim", False),
                "member_count": metadata.get("member_count", 0),
                "topic": metadata.get("topic"),
                "purpose": metadata.get("purpose")
            }
            channels.append(channel)
        
        return channels
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the Slack data collection."""
        
        # Get all documents
        all_results = self.collection.get(
            where={
                "$or": [
                    {"data_type": "slack_message"},
                    {"data_type": "slack_channel"}
                ]
            }
        )
        
        # Count by type
        message_count = 0
        channel_count = 0
        channels = set()
        users = set()
        
        for metadata in all_results["metadatas"]:
            if metadata:
                if metadata.get("data_type") == "slack_message":
                    message_count += 1
                    if "channel_id" in metadata:
                        channels.add(metadata["channel_id"])
                    if "user_id" in metadata:
                        users.add(metadata["user_id"])
                elif metadata.get("data_type") == "slack_channel":
                    channel_count += 1
        
        return {
            "total_messages": message_count,
            "total_channels": channel_count,
            "unique_channels": len(channels),
            "unique_users": len(users),
            "total_documents": len(all_results["ids"])
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Slack database handler for importing and managing Slack data in ChromaDB.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        python slack/slack_database_handler.py --database output/database/slack --collection slack_data
        python slack/slack_database_handler.py --database output/database/slack --import-slack --token xoxb-your-token
        """
    )

    parser.add_argument(
        "--database", "-d",
        type=str,
        required=True,
        help="Path to ChromaDB database directory"
    )

    parser.add_argument(
        "--collection", "-c", 
        type=str,
        default="slack_data",
        help="ChromaDB collection name"
    )

    parser.add_argument(
        "--import-slack",
        action="store_true",
        help="Import data from Slack API"
    )

    parser.add_argument(
        "--token",
        type=str,
        help="Slack API token for importing data"
    )

    parser.add_argument(
        "--include-bot-messages",
        action="store_true",
        help="Include bot messages in the import (default: False)"
    )

    parser.add_argument(
        "--max-messages-per-channel",
        type=int,
        help="Maximum number of messages to import per channel (default: no limit)"
    )

    args = parser.parse_args()

    # Initialize handler
    handler = SlackDatabaseHandler(
        database_path=args.database,
        collection_name=args.collection
    )

    # Import from Slack if requested
    if args.import_slack:
        if not args.token:
            parser.error("--token is required when using --import-slack")
        handler.import_from_slack_api(
            slack_token=args.token,
            include_bot_messages=args.include_bot_messages,
            max_messages_per_channel=args.max_messages_per_channel
        )

    # Show stats if requested  
    stats = handler.get_collection_stats()
    print("\nCollection Statistics:")
    print(f"Total Messages: {stats['total_messages']}")
    print(f"Total Channels: {stats['total_channels']}")
    print(f"Unique Channels: {stats['unique_channels']}")
    print(f"Unique Users: {stats['unique_users']}")
    print(f"Total Documents: {stats['total_documents']}")