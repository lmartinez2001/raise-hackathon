from smolagents import FinalAnswerTool
from typing import Any, List, Dict

class VideoFinalAnswerTool(FinalAnswerTool):
    """
    A tool that formats a final answer with an explanation, references to relevant video segments, 
    and clickable video links with timestamps.

    Args:
        answer (str): The generated explanation text.
        segments (List[Dict[str, Any]]): A list of dictionaries, each containing information about a video segment,
                                          including 'video_segment_file', 'timestamp_range', and 'text'.

    Returns:
        str: A formatted string containing the final answer with references and video links.

    Example:
        answer = "The primary purpose of the meeting was to discuss the new project timeline."
        segments = [
            {
                "video_segment_file": "data/video_short_2_segment_0062.mp4",
                "timestamp_range": "[02:33 - 02:35]",
                "text": "In order to make the connection."
            },
            {
                "video_segment_file": "data/video_short_2_segment_0067.mp4",
                "timestamp_range": "[02:46 - 02:49]",
                "text": "That we now have initialized a session."
            }
        ]
        tool = VideoFinalAnswerTool()
        formatted_answer = tool.forward(answer, segments)
        print(formatted_answer)
    """
    name = "final_answer"
    description = (
        "Formats the final answer with explanation, segment references, "
        "timestamps, and video segment links."
    )
    inputs = {
        "answer": {"type": "string", "description": "Generated explanation text"},
        "segments": {
            "type": "array",
            "description": "List of segment dicts including video_segment_file, timestamp_range, text"
        }
    }
    output_type = "string"

    def forward(self, answer: str, segments: List[Dict[str, Any]]) -> str:
        output = [f"**Answer:** {answer}", "", "**References & Evidence:**"]
        for seg in segments:
            file = seg["video_segment_file"]
            time = seg.get("timestamp_range", "")
            text = seg.get("text", "")
            note = f'- 📹 `{file}` {time}\n    • "{text}"'
            output.append(note)
        return "\n".join(output)
