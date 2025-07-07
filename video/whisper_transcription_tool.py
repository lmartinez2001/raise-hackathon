import asyncio
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Literal

import aiofiles
import ffmpeg
import whisper
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    TextContent,
    Tool,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhisperTranscriptionTool:
    def __init__(self):
        self.model = None
        self.model_name = "base"  # Default model size
        
    async def load_model(self, model_name: str = "base"):
        """Load the Whisper model asynchronously."""
        if self.model is None or self.model_name != model_name:
            logger.info(f"Loading Whisper model: {model_name}")
            self.model_name = model_name
            # Run model loading in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(None, whisper.load_model, model_name)
            logger.info(f"Whisper model {model_name} loaded successfully")
    
    async def extract_audio_from_video(self, video_path: str) -> str:
        """Extract audio from video file using ffmpeg."""
        audio_path = video_path.rsplit('.', 1)[0] + '.wav'
        
        try:
            # Extract audio using ffmpeg
            stream = ffmpeg.input(video_path)
            stream = ffmpeg.output(stream, audio_path, acodec='pcm_s16le', ac=1, ar='16000')
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            return audio_path
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            raise
    
    async def transcribe_audio(self, audio_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Transcribe audio file using Whisper."""
        try:
            # Run transcription in a thread pool
            loop = asyncio.get_event_loop()
            
            # Create a wrapper function to handle the language parameter correctly
            def transcribe_with_language(audio_path: str, language: Optional[str] = None):
                if language:
                    return self.model.transcribe(audio_path, language=language)
                else:
                    return self.model.transcribe(audio_path)
            
            result = await loop.run_in_executor(
                None, 
                transcribe_with_language, 
                audio_path,
                language
            )
            return result
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            raise
    
    async def transcribe_video(
        self, 
        video_path: str, 
        model_name: str = "base",
        language: Optional[str] = None,
        output_format: Literal['text', 'srt', 'vtt', 'json'] = "text",
        output_file: Optional[str] = None,
        include_timestamps: bool = True,
        video_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transcribe video file using Whisper."""
        try:
            # Load model if needed
            await self.load_model(model_name)
            
            # Extract audio from video
            logger.info("Extracting audio from video...")
            audio_path = await self.extract_audio_from_video(video_path)
            
            # Transcribe audio
            logger.info("Transcribing audio...")
            transcription_result = await self.transcribe_audio(audio_path, language)
            
            # Clean up temporary audio file
            if os.path.exists(audio_path):
                os.remove(audio_path)
            
            # Process segments with timestamps if requested
            segments = transcription_result.get("segments", [])
            if segments:
                processed_segments = []
                
                # Generate video ID if not provided
                if video_id is None:
                    video_id = self._generate_video_id(video_path)
                
                for segment in segments:
                    start_time = segment.get("start", 0)
                    end_time = segment.get("end", 0)
                    text = segment.get("text", "").strip()
                    
                    segment_data = {
                        "start": start_time,
                        "end": end_time,
                        "text": text,
                        "video_id": video_id
                    }
                    
                    # Add formatted timestamps if requested
                    if include_timestamps:
                        start_formatted = self._format_timestamp(start_time)
                        end_formatted = self._format_timestamp(end_time)
                        segment_data.update({
                            "start_formatted": start_formatted,
                            "end_formatted": end_formatted,
                            "timestamp_range": f"[{start_formatted} - {end_formatted}]"
                        })
                    
                    processed_segments.append(segment_data)
                
                transcription_result["segments"] = processed_segments
                transcription_result["video_id"] = video_id
            
            # Save to file if output_file is specified
            if output_file:
                await self._save_transcription_to_file(
                    transcription_result, 
                    output_file, 
                    output_format,
                    include_timestamps
                )
            
            # Format output based on requested format
            if output_format == "text":
                return {
                    "text": transcription_result.get("text", ""),
                    "language": transcription_result.get("language", ""),
                    "segments": transcription_result.get("segments", []),
                    "output_file": output_file if output_file else None
                }
            elif output_format == "json":
                return transcription_result
            else:
                return transcription_result
        except Exception as e:
            logger.error(f"Error in video transcription: {e}")
            raise
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to MM:SS timestamp."""
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes:02d}:{remaining_seconds:02d}"
    
    async def _save_transcription_to_file(
        self, 
        transcription_result: Dict[str, Any], 
        output_file: str, 
        output_format: Literal['text', 'srt', 'vtt', 'json'],
        include_timestamps: bool
    ) -> None:
        """Save transcription result to file in various formats."""
        try:
            output_path = Path(output_file)
            if output_format == 'srt':
                output_file = str(output_path.with_suffix('.srt'))
                await self._save_as_srt(transcription_result, output_file)
            elif output_format == 'vtt':
                output_file = str(output_path.with_suffix('.vtt'))
                await self._save_as_vtt(transcription_result, output_file)
            elif output_format == 'json':
                output_file = str(output_path.with_suffix('.json'))
                await self._save_as_json(transcription_result, output_file)
            else: # default to text format
                output_file = str(output_path.with_suffix('.txt'))
                await self._save_as_text(transcription_result, output_file, include_timestamps)
                
            logger.info(f"Transcription saved to: {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving transcription to file: {e}")
            raise
    
    async def _save_as_text(self, transcription_result: Dict[str, Any], output_file: str, include_timestamps: bool) -> None:
        """Save transcription as plain text."""
        async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            await f.write(f"Transcription Results\n")
            await f.write(f"Language: {transcription_result.get('language', 'Unknown')}\n")
            await f.write(f"{'='*50}\n\n")
            
            # Write full text
            await f.write(f"Full Text:\n{transcription_result.get('text', '')}\n\n")
            
            # Write segments with timestamps if requested
            if include_timestamps and transcription_result.get('segments'):
                await f.write(f"Segments with Timestamps:\n")
                await f.write(f"{'='*50}\n")
                for segment in transcription_result['segments']:
                    if 'timestamp_range' in segment:
                        await f.write(f"{segment['timestamp_range']} {segment['text']}\n")
                    else:
                        start_time = self._format_timestamp(segment.get('start', 0))
                        end_time = self._format_timestamp(segment.get('end', 0))
                        await f.write(f"[{start_time} - {end_time}] {segment['text']}\n")
    
    async def _save_as_srt(self, transcription_result: Dict[str, Any], output_file: str) -> None:
        """Save transcription as SRT subtitle format."""
        async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
            segments = transcription_result.get('segments', [])
            for i, segment in enumerate(segments, 1):
                start_time = self._format_srt_timestamp(segment.get('start', 0))
                end_time = self._format_srt_timestamp(segment.get('end', 0))
                text = segment.get('text', '').strip()
                
                await f.write(f"{i}\n")
                await f.write(f"{start_time} --> {end_time}\n")
                await f.write(f"{text}\n\n")
    
    async def _save_as_vtt(self, transcription_result: Dict[str, Any], output_file: str) -> None:
        """Save transcription as WebVTT subtitle format."""
        async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
            await f.write("WEBVTT\n\n")
            
            segments = transcription_result.get('segments', [])
            for segment in segments:
                start_time = self._format_vtt_timestamp(segment.get('start', 0))
                end_time = self._format_vtt_timestamp(segment.get('end', 0))
                text = segment.get('text', '').strip()
                
                await f.write(f"{start_time} --> {end_time}\n")
                await f.write(f"{text}\n\n")
    
    async def _save_as_json(self, transcription_result: Dict[str, Any], output_file: str) -> None:
        """Save transcription as JSON format."""
        async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(transcription_result, indent=2, ensure_ascii=False))
    
    def _format_srt_timestamp(self, seconds: float) -> str:
        """Format seconds to SRT timestamp format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def _format_vtt_timestamp(self, seconds: float) -> str:
        """Format seconds to WebVTT timestamp format (HH:MM:SS.mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}"
    
    def _generate_video_id(self, video_path: str) -> str:
        """Generate a video ID from the video path."""
        try:
            # Use relative path if possible, otherwise use filename
            path_obj = Path(video_path)
            if path_obj.is_absolute():
                # Try to make it relative to current working directory
                try:
                    relative_path = path_obj.relative_to(Path.cwd())
                    return str(relative_path)
                except ValueError:
                    # If it can't be made relative, use the filename
                    return path_obj.name
            else:
                return str(path_obj)
        except Exception:
            # Fallback to just the filename
            return Path(video_path).name

# Initialize the transcription tool
transcription_tool = WhisperTranscriptionTool()

# MCP Server setup
server = Server("whisper-transcription")

@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """List available tools."""
    return ListToolsResult(
        tools=[
            Tool(
                name="transcribe_video",
                description="Transcribe video files using OpenAI Whisper",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "video_path": {
                            "type": "string",
                            "description": "Path to the video file to transcribe"
                        },
                        "model_name": {
                            "type": "string",
                            "description": "Whisper model to use (tiny, base, small, medium, large)",
                            "default": "base"
                        },
                        "language": {
                            "type": "string",
                            "description": "Language code for transcription (e.g., 'en', 'fr', 'es')",
                            "default": None
                        },
                        "output_format": {
                            "type": "string",
                            "description": "Output format: 'text' for plain text, 'json' for full result",
                            "default": "text"
                        },
                        "output_file": {
                            "type": "string",
                            "description": "Path to save transcription file (supports .txt, .srt, .vtt, .json)",
                            "default": None
                        },
                        "include_timestamps": {
                            "type": "boolean",
                            "description": "Include timestamps in segments and output",
                            "default": True
                        },
                        "video_id": {
                            "type": "string",
                            "description": "Custom video ID for segments (auto-generated from path if not provided)",
                            "default": None
                        }
                    },
                    "required": ["video_path"]
                }
            )
        ]
    )

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls."""
    if name == "transcribe_video":
        try:
            video_path = arguments["video_path"]
            model_name = arguments.get("model_name", "base")
            language = arguments.get("language")
            output_format = arguments.get("output_format", "text")
            output_file = arguments.get("output_file")
            include_timestamps = arguments.get("include_timestamps", True)
            video_id = arguments.get("video_id")
            
            # Validate video file exists
            if not os.path.exists(video_path):
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Error: Video file not found at {video_path}"
                        )
                    ]
                )
            
            # Perform transcription
            result = await transcription_tool.transcribe_video(
                video_path=video_path,
                model_name=model_name,
                language=language,
                output_format=output_format,
                output_file=output_file,
                include_timestamps=include_timestamps,
                video_id=video_id
            )
            
            # Format response
            if output_format == "text":
                output_file_info = f"\n\nFile saved to: {result.get('output_file', 'Not saved')}" if result.get('output_file') else ""
                response_text = f"Transcription completed successfully!\n\nText: {result['text']}\n\nLanguage detected: {result['language']}{output_file_info}"
            else:
                output_file_info = f"\n\nFile saved to: {result.get('output_file', 'Not saved')}" if result.get('output_file') else ""
                response_text = f"Transcription completed successfully!\n\nFull result: {json.dumps(result, indent=2)}{output_file_info}"
            
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=response_text
                    )
                ]
            )
            
        except Exception as e:
            logger.error(f"Error in transcribe_video tool: {e}")
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error during transcription: {str(e)}"
                    )
                ]
            )
    
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )
        ]
    )

async def main():
    """Main function to run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="whisper-transcription",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main()) 