from agent_core import action

@action(
    name="understand_video",
    description="Analyses a video file by sampling keyframes and generating a narrative summary using a Vision Language Model. Use when the user shares a video and wants to know what happens in it, extract visible text, or answer a specific question about video content.",
    mode="CLI",
    action_sets=["document_processing, image"],
    input_schema={
        "video_path": {
            "type": "string",
            "example": "C:\\Users\\user\\Videos\\meeting.mp4",
            "description": "Absolute path to the video file (MP4, AVI, MOV supported)."
        },
        "query": {
            "type": "string",
            "example": "What is being presented on the slides?",
            "description": "Optional: specific question to answer about the video."
        },
        "max_frames": {
            "type": "integer",
            "example": 8,
            "description": "Number of evenly-spaced keyframes to sample (default: 8, max recommended: 16)."
        }
    },
    output_schema={
        "status": {
            "type": "string",
            "example": "success",
            "description": "'success' if analysis completed, 'error' otherwise."
        },
        "summary": {
            "type": "string",
            "example": "The video shows a person presenting slides about quarterly sales...",
            "description": "First 500 characters of the video summary. Full summary saved to file."
        },
        "file_path": {
            "type": "string",
            "example": "/workspace/video_summary_20260414_153000.txt",
            "description": "Absolute path to the .txt file containing the full video summary."
        },
        "file_saved": {
            "type": "boolean",
            "example": True,
            "description": "True if the full summary was saved to disk."
        },
        "message": {
            "type": "string",
            "example": "File not found.",
            "description": "Error message if applicable."
        }
    },
    test_payload={
        "video_path": "C:\\Users\\user\\Videos\\sample.mp4",
        "query": "Summarise the video content.",
        "max_frames": 8,
        "simulated_mode": True
    }
)
def understand_video(input_data: dict) -> dict:
    import os

    video_path = str(input_data.get('video_path', '')).strip()
    query = str(input_data.get('query', '')).strip() or None
    max_frames = int(input_data.get('max_frames', 8))
    simulated_mode = input_data.get('simulated_mode', False)

    if simulated_mode:
        return {
            'status': 'success',
            'summary': 'The video shows a simulated presentation with 3 speakers.',
            'file_path': '/workspace/video_summary_simulated.txt',
            'file_saved': True,
            'message': ''
        }

    if not video_path:
        return {'status': 'error', 'summary': '', 'file_path': '', 'file_saved': False, 'message': 'video_path is required.'}

    if not os.path.isfile(video_path):
        return {'status': 'error', 'summary': '', 'file_path': '', 'file_saved': False, 'message': 'File not found.'}

    try:
        import app.internal_action_interface as iai
        result = iai.InternalActionInterface.understand_video(video_path, query=query, max_frames=max_frames)
        return {**result, 'message': ''}
    except RuntimeError as e:
        # Catches missing opencv gracefully
        return {'status': 'error', 'summary': '', 'file_path': '', 'file_saved': False, 'message': str(e)}
    except Exception as e:
        return {'status': 'error', 'summary': '', 'file_path': '', 'file_saved': False, 'message': str(e)}

execute = understand_video
