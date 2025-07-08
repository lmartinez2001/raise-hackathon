# Slack Database Handler

A comprehensive Model Context Protocol (MCP) server for storing and retrieving Slack messages and channels using ChromaDB for vector search capabilities. Includes both direct API integration and intelligent agent-based querying.

## Features

- **Direct Slack API Integration**: Import data directly from Slack using bot tokens
- **Message Storage**: Store Slack messages with metadata including user info, timestamps, reactions, and attachments
- **Channel Management**: Store and retrieve channel information with member counts and privacy settings
- **Vector Search**: Search messages using semantic similarity with ChromaDB
- **Thread Support**: Retrieve thread replies and conversation threads
- **MCP Integration**: Full MCP server implementation with tools for Slack operations
- **Intelligent Agent**: Natural language querying using LLM agents
- **Flexible Filtering**: Search by channel, user, date range, and text content
- **Pagination Support**: Handle large datasets with cursor-based pagination

## Installation

The Slack database handler is already integrated into your project. Make sure you have the required dependencies:

```bash
# Install dependencies (if not already installed)
uv sync
```

## Configuration

### Environment Variables

The Slack database handler uses the following environment variables:

- `SLACK_BOT_TOKEN`: Your Slack bot token for API access
- `PYTHONPATH`: Set to include the project root for imports

### MCP Configuration

The Slack database handler can be configured in `mcp_config.json`:

```json
{
  "mcpServers": {
    "slack-database": {
      "command": "python",
      "args": ["slack/agent_slack.py", "--database_path", "output/database/slack", "--collection_name", "slack_data"],
      "env": {
        "PYTHONPATH": "."
      }
    }
  }
}
```

## Usage

### Data Import from Slack API

The handler can import data directly from your Slack workspace:

```bash
python slack/slack_database_handler.py --slack-token "xoxb-your-token" --database-path "output/database/slack" --collection-name "slack_data"
```

This will:
1. Fetch all channels from your Slack workspace
2. Import all messages from each channel (with pagination)
3. Store everything in ChromaDB for vector search

### Running the MCP Server

The Slack database handler runs as an MCP server that provides tools for Slack operations:

```bash
python slack/agent_slack.py --database_path output/database/slack --collection_name slack_data
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
from slack.slack_database_handler import SlackDatabaseHandler, SlackMessage, SlackChannel

# Initialize handler
handler = SlackDatabaseHandler("output/database/slack", "slack_data")

# Import data from Slack API
handler.import_from_slack_api("xoxb-your-token", include_bot_messages=False)

# Store a message manually
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

# Get statistics
stats = handler.get_collection_stats()
print(f"Total messages: {stats['total_messages']}")
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

### Command Line Import

Import your Slack data:

```bash
python slack/slack_database_handler.py --slack-token "xoxb-your-token" --database-path "output/database/slack" --collection-name "slack_data"
```

### Agent-Based Querying

Query your data using natural language:

```bash
python slack/agent_slack.py --database_path output/database/slack --collection_name slack_data --query "What was discussed about meetings?"
```

### Direct API Usage

Use the handler programmatically:

```python
from slack.slack_database_handler import SlackDatabaseHandler

# Initialize and import data
handler = SlackDatabaseHandler("output/database/slack", "slack_data")
handler.import_from_slack_api("xoxb-your-token")

# Search for messages
results = handler.search_messages("meeting", n_results=10)
for message in results['results']:
    print(f"{message['username']}: {message['text']}")
```

## Integration with Slack MCP Server

This handler provides a complete Python-based solution for Slack data management. You can:

1. **Direct API Integration**: Import data directly from Slack using bot tokens
2. **Vector Search**: Enable semantic search and similarity queries on your Slack data
3. **Agent-Based Querying**: Use natural language to query your Slack data
4. **MCP Server**: Run as a Model Context Protocol server for integration with other tools

### Alternative: External MCP Server

You can also integrate with external MCP servers like the [slack-mcp-server](https://github.com/korotovsky/slack-mcp-server) project:

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

- **Database connection errors**: Graceful fallback and retry mechanisms
- **Invalid data format**: Validation and sanitization of input data
- **Missing required fields**: Default values and error reporting
- **Search query errors**: Fallback to basic text search
- **Slack API errors**: Automatic retry and channel joining
- **Network timeouts**: Configurable timeout handling
- **Rate limiting**: Respects Slack API rate limits

## Performance Considerations

- **Persistent Storage**: Uses ChromaDB's persistent storage for data durability
- **Pagination Support**: Handles large datasets with cursor-based pagination
- **Vector Search**: Efficient semantic search with configurable result limits
- **Metadata Indexing**: Fast filtering by channel, user, and date
- **Memory Management**: Processes large datasets in chunks
- **Caching**: Caches database connections and frequently accessed data
- **Async Operations**: Uses async/await for Slack API operations

## Security

- **Local Storage**: Database files are stored locally on your machine
- **Token Security**: Slack tokens are handled securely and not logged
- **No External Calls**: All processing happens locally (except Slack API calls)
- **Data Privacy**: No sensitive message content is logged or transmitted
- **Access Control**: Database access is controlled by file system permissions
- **API Rate Limiting**: Respects Slack API rate limits to avoid account issues

## Contributing

To extend the handler:

1. **Add new data models** in `slack_database_handler.py`
2. **Implement new storage methods** in the `SlackDatabaseHandler` class
3. **Add corresponding MCP tools** in `agent_slack.py`
4. **Update the agent tools** to include new functionality
5. **Test with your Slack data** using the provided examples
6. **Update documentation** to reflect new features

### Development Setup

```bash
# Install dependencies
uv sync

# Run tests
python -m pytest tests/

# Import test data
python slack/slack_database_handler.py --slack-token "xoxb-test-token" --database-path "test_db" --collection-name "test_data"

# Test agent
python slack/agent_slack.py --database_path test_db --collection_name test_data --query "test query"
```

## Agentic Capabilities

The Slack database handler includes powerful agentic capabilities that allow you to query your Slack data using natural language through LLM agents.

### Agent-Based Querying

The `agent_slack.py` provides an intelligent agent that can understand natural language queries and automatically use the appropriate tools to find relevant information.

#### Running the Agent

```bash
python slack/agent_slack.py --database_path output/database/slack --collection_name slack_data --query "What was discussed about meetings?"
```

#### Example Queries

The agent can handle various types of natural language queries:

- **Topic-based queries**: "What was discussed about meetings?"
- **User-focused queries**: "What did Julien say about deadlines?"
- **Channel-specific queries**: "Show me messages from the general channel about project updates"
- **Time-based queries**: "What was discussed last week about the hackathon?"
- **Action-oriented queries**: "Find all decisions made in Slack conversations"

#### Agent Features

- **Natural Language Understanding**: Converts human queries into structured database searches
- **Multi-tool Coordination**: Automatically selects and combines the right tools for each query
- **Context-Aware Results**: Provides formatted, readable summaries of search results
- **Error Handling**: Gracefully handles missing data or search failures
- **Flexible Output**: Returns structured data that can be further processed

#### Agent Tools

The agent has access to all the MCP tools plus additional capabilities:

1. **`search_slack_messages`** - Semantic search across all messages
2. **`get_slack_channels`** - List all channels with metadata
3. **`get_slack_statistics`** - Get database overview and metrics
4. **`get_channel_messages`** - Retrieve messages from specific channels

#### Example Agent Output

```bash
$ python slack/agent_slack.py --database_path output/database/slack --collection_name slack_data --query "What was discussed about meetings?"

User: gaubil.julien, Channel: all-contexta-raise, Message: when are we meeting?, Time: 1751815187.172399
User: louis.martinez7569, Channel: all-contexta-raise, Message: Daily Meeting Samedi, 5 juillet · De 4:00 à 5:00pm, Time: 1751712232.752759
User: oliverjpbolton, Channel: all-contexta-raise, Message: When do you guys want to meet today?, Time: 1751814017.344269
```

#### Advanced Agent Usage

**Complex Queries**: The agent can handle multi-part queries that require combining multiple tools:

```bash
# Find messages about meetings and then get user details
python slack/agent_slack.py --database_path output/database/slack --collection_name slack_data --query "Show me all messages about meetings and who sent them"

# Cross-reference information
python slack/agent_slack.py --database_path output/database/slack --collection_name slack_data --query "What decisions were made in the general channel and who was involved?"
```

**Statistical Analysis**: The agent can provide insights about your Slack data:

```bash
# Get overview of activity
python slack/agent_slack.py --database_path output/database/slack --collection_name slack_data --query "How active is our Slack workspace and what are the most discussed topics?"

# Find patterns
python slack/agent_slack.py --database_path output/database/slack --collection_name slack_data --query "When do people usually post messages and what channels are most active?"
```

#### Agent Configuration

The agent uses the `smolagents` framework with the following configuration:

- **Model**: meta-llama/Llama-3.3-70B-Instruct (via InferenceClientModel)
- **Max Steps**: 5 (configurable via `--max-steps`)
- **Tools**: All Slack database tools with proper data format handling
- **Error Handling**: Graceful fallbacks for missing data or tool failures

#### Integration with Other Systems

The agent can be easily integrated into larger workflows:

```python
# Use the agent programmatically
from slack.agent_slack import CodeAgent, InferenceClientModel
from slack.agent_slack import search_slack_messages, get_slack_channels, get_slack_statistics

# Initialize agent
model = InferenceClientModel()
agent = CodeAgent(
    model=model,
    name="slack_agent",
    tools=[search_slack_messages, get_slack_channels, get_slack_statistics],
    max_steps=5,
)

# Run query
result = agent.run("What was discussed about meetings?")
print(result)
```

#### Performance Considerations

- **Caching**: The agent caches database connections for efficiency
- **Pagination**: Handles large result sets automatically
- **Memory Management**: Processes results in chunks to avoid memory issues
- **Timeout Handling**: Graceful handling of long-running queries

#### Troubleshooting

**Common Issues**:

1. **No results found**: Try broader search terms or check if the database has data
2. **Tool errors**: Verify database path and collection name
3. **Format errors**: The agent now handles data format issues automatically

**Debug Mode**: Add verbose logging to see what the agent is doing:

```bash
python slack/agent_slack.py --database_path output/database/slack --collection_name slack_data --query "test query" --max-steps 10
```

## License

This project is part of your hackathon project and follows the same license terms. 