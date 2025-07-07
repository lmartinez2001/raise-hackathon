# Slack Database Handler

A Model Context Protocol (MCP) server for storing and retrieving Slack messages and channels using ChromaDB for vector search capabilities.

## Features

- **Message Storage**: Store Slack messages with metadata including user info, timestamps, reactions, and attachments
- **Channel Management**: Store and retrieve channel information
- **Vector Search**: Search messages using semantic similarity with ChromaDB
- **Thread Support**: Retrieve thread replies and conversation threads
- **MCP Integration**: Full MCP server implementation with tools for Slack operations
- **Flexible Filtering**: Search by channel, user, date range, and text content

## Installation

The Slack database handler is already integrated into your project. Make sure you have the required dependencies:

```bash
# Install dependencies (if not already installed)
uv sync
```

## Configuration

The Slack database handler is configured in `mcp_config.json`:

```json
{
  "mcpServers": {
    "slack-database": {
      "command": "python",
      "args": ["slack_database_handler.py"],
      "env": {
        "PYTHONPATH": "."
      }
    }
  }
}
```

## Usage

### Running the MCP Server

The Slack database handler runs as an MCP server that provides tools for Slack operations:

```bash
python slack_database_handler.py
```

### Available MCP Tools

1. **`slack_search_messages`**
   - Search for messages using text queries
   - Filter by channel, user, or date range
   - Returns semantically similar messages

2. **`slack_get_channel_messages`**
   - Get all messages from a specific channel
   - Supports pagination with cursors
   - Returns messages with metadata

3. **`slack_get_thread_replies`**
   - Get replies to a specific thread
   - Returns thread conversation history

4. **`slack_get_channels`**
   - Get list of all channels
   - Filter by channel types (public, private, DM, group DM)

5. **`slack_get_stats`**
   - Get database statistics
   - Shows message counts, channel counts, unique users

### Direct Python Usage

You can also use the handler directly in Python code:

```python
from slack_database_handler import SlackDatabaseHandler, SlackMessage, SlackChannel

# Initialize handler
handler = SlackDatabaseHandler("output/database/slack")

# Store a message
message = SlackMessage(
    message_id="1234567890.123456",
    channel_id="C1234567890",
    channel_name="general",
    user_id="U1234567890",
    username="john_doe",
    text="Hello everyone!",
    timestamp="1234567890.123456",
    thread_ts=None,
    is_thread_reply=False,
    attachments=[],
    reactions=[],
    permalink="https://company.slack.com/archives/C1234567890/p1234567890123456"
)

handler.store_message(message)

# Search messages
results = handler.search_messages("hello", n_results=10)
print(f"Found {results['total_found']} messages")

# Get channel messages
channel_messages = handler.get_messages_by_channel("C1234567890", limit=100)
print(f"Channel has {channel_messages['total_messages']} messages")
```

## Data Models

### SlackMessage

```python
@dataclass
class SlackMessage:
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
```

### SlackChannel

```python
@dataclass
class SlackChannel:
    channel_id: str
    name: str
    is_private: bool
    is_im: bool
    is_mpim: bool
    member_count: int
    topic: Optional[str] = None
    purpose: Optional[str] = None
```

## Example Usage

Run the example script to see the handler in action:

```bash
python slack_example.py
```

This will:
1. Store sample channels and messages
2. Demonstrate search functionality
3. Show thread retrieval
4. Display database statistics

## Integration with Slack MCP Server

This handler is designed to work with the [slack-mcp-server](https://github.com/korotovsky/slack-mcp-server) project. You can:

1. Use the Go-based slack-mcp-server to fetch data from Slack
2. Store the fetched data using this Python handler
3. Enable vector search and semantic queries on your Slack data

## Database Structure

The handler uses ChromaDB with the following structure:

- **Documents**: Message text or channel descriptions
- **Metadata**: Rich metadata including IDs, timestamps, user info, etc.
- **Embeddings**: Vector embeddings for semantic search (handled by ChromaDB)

### Document Types

- `slack_message`: Individual Slack messages
- `slack_channel`: Channel information

## Search Capabilities

The handler supports various search options:

- **Text Search**: Find messages by content
- **User Filter**: Filter by specific user
- **Channel Filter**: Filter by specific channel
- **Date Range**: Filter by timestamp range
- **Thread Search**: Find thread replies
- **Semantic Search**: Find similar messages using vector embeddings

## Error Handling

The handler includes comprehensive error handling:

- Database connection errors
- Invalid data format
- Missing required fields
- Search query errors

## Performance Considerations

- Uses ChromaDB's persistent storage for data durability
- Supports pagination for large result sets
- Efficient vector search with configurable result limits
- Metadata indexing for fast filtering

## Security

- No sensitive data is logged
- Database files are stored locally
- No external API calls (data must be provided programmatically)

## Contributing

To extend the handler:

1. Add new data models in the handler file
2. Implement new storage methods
3. Add corresponding MCP tools
4. Update the example script
5. Test with your Slack data

## License

This project is part of your hackathon project and follows the same license terms. 