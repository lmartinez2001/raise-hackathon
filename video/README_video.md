# Video Transcription with ChromaDB

This project provides tools to transcribe videos and store them in a ChromaDB database for semantic search.

## Quick Start

### 1. Transcribe and Store Video

```bash
python video/transcribe_and_store.py --video data/video.mp4 --collection my_collection --database output/my_db
```

**Required arguments:**
- `--video`: Path to video file
- `--collection`: ChromaDB collection name  
- `--database`: Database directory path

**Optional arguments:**
- `--language`: Language code (default: auto-detect)
- `--video-id`: Custom video ID (default: auto-generate)
- `--store-video`: Store video file in database

### 2. Search with SmolAgent

```bash
python video/agent_transcriber.py --database_path output/meetings_db --collection_name meetings --query "What happens when we query the database?"
```

**Required arguments:**
- `--database`: Path to ChromaDB database directory
- `--collection`: ChromaDB collection name
- `--query`: Query to ask the agent

**Optional arguments:**
- `--max-steps`: Maximum agent steps (default: 5)

The agent will query the database for transcription segments and return relevant results.

## Features

- **Video Transcription**: Uses OpenAI Whisper for accurate transcription
- **Vector Search**: ChromaDB enables semantic search through transcriptions
- **Segment Storage**: Each transcription segment stored separately for precise search
- **Agent Integration**: Hugging Face SmolAgent for natural language queries

## Output

- Transcribed segments stored in ChromaDB
- Search results with timestamps and video sources
- Agent responses with relevant transcription excerpts
