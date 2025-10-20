#!/usr/bin/env python3
"""
Sora 2 API Web Interface
========================

A Flask-based web application providing a user-friendly interface for the OpenAI
Sora 2 video generation API. This application offers:

- **Video Creation**: Generate videos from text prompts with optional image references
- **Video Remixing**: Transform existing videos with new creative directions
- **Gallery Management**: Browse and manage locally stored videos
- **API Integration**: Direct access to OpenAI's Sora 2 video library
- **Real-time Progress**: Monitor video generation with live status updates

Architecture:
    - Frontend: Single-page application (HTML/CSS/JavaScript)
    - Backend: Flask REST API with CORS support
    - Storage: Local filesystem for video downloads and metadata
    - Processing: Asynchronous video generation with threading

Endpoints:
    GET  /                          - Serve main web interface
    POST /api/create                - Create new video from prompt/image
    POST /api/remix                 - Remix existing video
    GET  /api/status/<job_id>       - Poll job progress
    GET  /api/gallery               - List locally stored videos
    GET  /api/videos                - List videos from API
    GET  /api/download/<video_id>   - Download video from API
    DELETE /api/delete/<video_id>   - Delete video from API (preserves local)
    DELETE /api/delete-local/<id>   - Delete local video files only

Dependencies:
    - Flask: Web framework
    - flask-cors: Cross-origin resource sharing
    - sora_api: Custom Sora 2 API client

Author: OpenAI Sora Integration Team
Version: 1.0.0
License: MIT
"""

import os
import sys
import json
import threading
import shutil
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

# Add parent directory to path to import sora_api from src/api/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from api.sora_api import SoraAPIClient

app = Flask(__name__)
CORS(app)

# Global dictionary to track job progress
# Structure: {job_id: {status, progress, message, video_id, result, ...}}
job_status = {}


def create_video_async(job_id: str, params: dict, input_reference_path: str = None) -> None:
    """
    Background thread function for asynchronous video creation.
    
    Creates a video using the Sora API, polls for completion, and downloads
    the result to local storage. Updates the global job_status dictionary
    with progress information throughout the process.
    
    Args:
        job_id (str): Unique identifier for tracking this job's progress.
        params (dict): Video creation parameters:
            - prompt (str): Text description of the video
            - model (str, optional): Model name (default: 'sora-2')
            - seconds (str, optional): Duration in seconds
            - size (str, optional): Resolution (e.g., '1920x1080')
        input_reference_path (str, optional): Path to temporary reference image file.
            File will be deleted after processing.
    
    Updates job_status with:
        - status: 'creating', 'downloading', 'completed', 'failed', or 'error'
        - progress: Integer 0-100 indicating completion percentage
        - message: Human-readable status message
        - video_id: API video identifier (when available)
        - video_path: Local path to downloaded video (when complete)
        - thumbnail_path: Local path to thumbnail (when complete)
        - result: Full API response (when complete)
        - error_details: Error information (on failure)
    
    Side Effects:
        - Creates directory: videos/{video_id}/
        - Downloads files: video.mp4, thumbnail.webp, spritesheet.jpg
        - Saves metadata.json with creation parameters
        - Deletes input_reference_path temporary file
    
    Note:
        This function is designed to run in a daemon thread and handles
        all exceptions internally by updating job_status.
    """
    try:
        client = SoraAPIClient()
        job_status[job_id] = {
            'status': 'creating',
            'progress': 0,
            'message': 'Initiating video creation...'
        }
        
        # Create the video
        result = client.create(
            prompt=params['prompt'],
            model=params.get('model', 'sora-2'),
            input_reference=input_reference_path,
            seconds=params.get('seconds'),
            size=params.get('size'),
            wait_for_completion=False
        )
        
        video_id = result.get('id')
        job_status[job_id].update({
            'video_id': video_id,
            'progress': 10,
            'message': 'Video creation started, waiting for completion...'
        })
        
        # Poll for completion with progress updates
        import time
        max_wait_time = 600  # 10 minutes
        poll_interval = 3
        start_time = time.time()
        elapsed = 0
        
        while elapsed < max_wait_time:
            # Check video status
            final_result = client.retrieve(video_id)
            status = final_result.get('status')
            
            # Calculate progress (10-85% during waiting phase)
            # Progress increases slowly over time
            time_progress = min(75, int((elapsed / max_wait_time) * 75))
            current_progress = 10 + time_progress
            
            # Update job status with current state
            if status == 'queued':
                job_status[job_id].update({
                    'progress': current_progress,
                    'message': 'Video queued on server...'
                })
            elif status == 'in_progress':
                job_status[job_id].update({
                    'progress': current_progress,
                    'message': 'Generating video...'
                })
            elif status == 'completed':
                break
            elif status == 'failed':
                break
            else:
                job_status[job_id].update({
                    'progress': current_progress,
                    'message': f'Status: {status}...'
                })
            
            time.sleep(poll_interval)
            elapsed = time.time() - start_time
        
        # Update status based on result
        if final_result.get('status') == 'completed':
            job_status[job_id].update({
                'status': 'downloading',
                'progress': 90,
                'message': 'Video completed, downloading...'
            })
            
            # Create video-specific directory
            video_dir = f"videos/{video_id}"
            os.makedirs(video_dir, exist_ok=True)
            
            # Download all variants to video directory
            video_file = f"{video_dir}/{video_id}.mp4"
            thumbnail_file = f"{video_dir}/thumbnail.webp"
            spritesheet_file = f"{video_dir}/spritesheet.jpg"
            
            client.save_video(video_id, video_file, variant='video')
            client.save_video(video_id, thumbnail_file, variant='thumbnail')
            client.save_video(video_id, spritesheet_file, variant='spritesheet')
            
            # Save metadata to video directory
            metadata_file = f"{video_dir}/metadata.json"
            metadata = {
                'api_response': final_result,
                'creation_args': params,
                'saved_at': datetime.now().isoformat()
            }
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            job_status[job_id].update({
                'status': 'completed',
                'progress': 100,
                'message': 'Video ready!',
                'video_id': video_id,
                'video_path': video_file,
                'thumbnail_path': thumbnail_file,
                'result': final_result
            })
        else:
            job_status[job_id].update({
                'status': 'failed',
                'message': f"Video generation failed: {final_result.get('status')}",
                'result': final_result
            })
    
    except Exception as e:
        # Try to extract API error details
        error_details = {
            'error_type': type(e).__name__,
            'error_message': str(e)
        }
        
        # Check if it's an HTTP error with response
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            try:
                import json
                error_details['api_response'] = json.loads(e.response.text)
            except:
                error_details['api_response_text'] = e.response.text
        
        job_status[job_id].update({
            'status': 'error',
            'message': f'Error: {str(e)}',
            'error_details': error_details
        })
    finally:
        # Clean up temporary file if it exists
        if input_reference_path and os.path.exists(input_reference_path):
            try:
                os.remove(input_reference_path)
            except:
                pass  # Ignore cleanup errors


def remix_video_async(job_id: str, video_id: str, prompt: str) -> None:
    """
    Background thread function for asynchronous video remixing.
    
    Creates a remix of an existing video using the Sora API, polls for completion,
    and downloads the result to local storage. Updates the global job_status
    dictionary with progress information.
    
    Args:
        job_id (str): Unique identifier for tracking this remix job's progress.
        video_id (str): The ID of the source video to remix. Must be a completed video.
        prompt (str): New text prompt describing the desired remix transformation.
    
    Updates job_status with:
        - status: 'remixing', 'downloading', 'completed', 'failed', or 'error'
        - progress: Integer 0-100 indicating completion percentage
        - message: Human-readable status message
        - video_id: New remix video identifier (when available)
        - video_path: Local path to downloaded remix (when complete)
        - thumbnail_path: Local path to thumbnail (when complete)
        - result: Full API response (when complete)
        - error_details: Error information (on failure)
    
    Side Effects:
        - Creates directory: videos/{remix_video_id}/
        - Downloads files: {remix_video_id}.mp4, thumbnail.webp
        - Saves metadata.json including original_video_id
    
    Error Handling:
        - Retries polling up to 5 times on transient errors
        - Logs detailed error information to stdout
        - Updates job_status with error details on failure
    
    Note:
        This function is designed to run in a daemon thread and handles
        all exceptions internally by updating job_status.
    """
    try:
        client = SoraAPIClient()
        job_status[job_id] = {
            'status': 'remixing',
            'progress': 0,
            'message': 'Initiating video remix...'
        }
        
        print(f"[REMIX] Starting remix for video {video_id}")
        print(f"[REMIX] Prompt: {prompt}")
        
        # Start the remix
        result = client.remix(
            video_id=video_id,
            prompt=prompt,
            wait_for_completion=False
        )
        
        remix_video_id = result.get('id')
        print(f"[REMIX] Remix job created successfully! New video ID: {remix_video_id}")
        
        job_status[job_id].update({
            'video_id': remix_video_id,
            'progress': 10,
            'message': 'Video remix started, waiting for completion...'
        })
        
        # Poll for completion with progress updates
        import time
        max_wait_time = 600  # 10 minutes
        poll_interval = 3
        start_time = time.time()
        elapsed = 0
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while elapsed < max_wait_time:
            try:
                # Check video status
                final_result = client.retrieve(remix_video_id)
                status = final_result.get('status')
                
                # Reset error counter on successful poll
                consecutive_errors = 0
                
                print(f"[REMIX] Status: {status}, Elapsed: {int(elapsed)}s")
                
                # Calculate progress (10-85% during waiting phase)
                time_progress = min(75, int((elapsed / max_wait_time) * 75))
                current_progress = 10 + time_progress
                
                # Update job status with current state
                if status == 'queued':
                    job_status[job_id].update({
                        'progress': current_progress,
                        'message': 'Remix queued on server...'
                    })
                elif status == 'in_progress':
                    job_status[job_id].update({
                        'progress': current_progress,
                        'message': 'Generating remixed video...'
                    })
                elif status == 'completed':
                    print(f"[REMIX] Video completed!")
                    break
                elif status == 'failed':
                    print(f"[REMIX] Video failed!")
                    break
                else:
                    job_status[job_id].update({
                        'progress': current_progress,
                        'message': f'Status: {status}...'
                    })
                
            except Exception as poll_error:
                consecutive_errors += 1
                print(f"[REMIX] Polling error (attempt {consecutive_errors}/{max_consecutive_errors}): {poll_error}")
                
                if consecutive_errors >= max_consecutive_errors:
                    print(f"[REMIX] Too many consecutive errors, aborting")
                    raise Exception(f"Failed to poll status after {max_consecutive_errors} attempts")
                
                # Continue polling despite the error
                job_status[job_id].update({
                    'progress': job_status[job_id].get('progress', 10),
                    'message': f'Polling video status... (retry {consecutive_errors})'
                })
            
            time.sleep(poll_interval)
            elapsed = time.time() - start_time
        
        # Update status based on result
        if final_result.get('status') == 'completed':
            print(f"[REMIX] Video completed, starting download...")
            job_status[job_id].update({
                'status': 'downloading',
                'progress': 90,
                'message': 'Remix completed, downloading...'
            })
            
            # Create video-specific directory
            video_dir = f"videos/{remix_video_id}"
            os.makedirs(video_dir, exist_ok=True)
            
            # Download the video
            print(f"[REMIX] Downloading to {video_dir}...")
            video_file = client.download(remix_video_id, output_dir=video_dir)
            print(f"[REMIX] Downloaded: {video_file}")
            
            # Download thumbnail
            thumbnail_file = os.path.join(video_dir, 'thumbnail.webp')
            print(f"[REMIX] Downloading thumbnail...")
            client.generate_thumbnail(remix_video_id, thumbnail_file)
            
            # Save metadata
            metadata = {
                'video_id': remix_video_id,
                'original_video_id': video_id,
                'prompt': prompt,
                'model': final_result.get('model'),
                'seconds': final_result.get('duration'),
                'size': final_result.get('resolution'),
                'created_at': final_result.get('created_at'),
                'status': final_result.get('status'),
                'type': 'remix'
            }
            
            metadata_file = os.path.join(video_dir, 'metadata.json')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"[REMIX] Remix complete! Video saved to {video_file}")
            
            job_status[job_id].update({
                'status': 'completed',
                'progress': 100,
                'message': 'Remixed video ready!',
                'video_id': remix_video_id,
                'video_path': video_file,
                'thumbnail_path': thumbnail_file,
                'result': final_result
            })
        else:
            print(f"[REMIX] Video remix failed with status: {final_result.get('status')}")
            job_status[job_id].update({
                'status': 'failed',
                'message': f"Video remix failed: {final_result.get('status')}",
                'result': final_result
            })
    
    except Exception as e:
        print(f"[REMIX] ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Try to extract API error details
        error_details = {
            'error_type': type(e).__name__,
            'error_message': str(e)
        }
        
        # Check if it's an HTTP error with response
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            try:
                error_details['api_response'] = json.loads(e.response.text)
            except:
                error_details['api_response_text'] = e.response.text
        
        job_status[job_id].update({
            'status': 'error',
            'message': f'Error: {str(e)}',
            'error_details': error_details
        })


@app.route('/')
def index():
    """
    Serve the main web interface.
    
    Returns:
        HTML page: The single-page application interface for Sora 2 video generation.
    """
    return render_template('index.html')


@app.route('/favicon.ico')
def favicon():
    """
    Handle favicon requests to prevent 404 errors in browser console.
    
    Returns:
        Empty response with 204 No Content status.
    """
    return '', 204


@app.route('/api/create', methods=['POST'])
def create_video():
    """
    Create a new video from a text prompt and optional reference image.
    
    Accepts either JSON (text-only) or multipart/form-data (with image upload).
    Initiates an asynchronous video generation job and returns a job ID for
    status polling.
    
    JSON Request Body:
        {
            "prompt": "Text description of video",
            "model": "sora-2" (optional, default: "sora-2"),
            "seconds": "5" (optional, video duration),
            "size": "1920x1080" (optional, resolution)
        }
    
    Form Data Fields (multipart/form-data):
        - prompt: Text description (required)
        - model: Model name (optional)
        - seconds: Duration (optional)
        - size: Resolution (optional)
        - input_reference: Image file (optional, .jpg/.jpeg/.png/.webp)
    
    Returns:
        JSON response:
        {
            "success": true,
            "job_id": "job_20240115_143022_123456",
            "message": "Video creation started"
        }
    
    Status Codes:
        200: Job started successfully
        500: Server error during job initialization
    
    Example:
        # Text-only request
        POST /api/create
        Content-Type: application/json
        {"prompt": "A sunset over the ocean", "seconds": "5"}
        
        # With reference image
        POST /api/create
        Content-Type: multipart/form-data
        prompt="Transform this photo"
        input_reference=<image file>
    """
    try:
        # Check if this is a multipart request (with file) or JSON
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Handle file upload
            data = {
                'prompt': request.form.get('prompt'),
                'model': request.form.get('model', 'sora-2'),
                'seconds': request.form.get('seconds'),
                'size': request.form.get('size')
            }
            
            # Handle optional file upload
            input_reference_path = None
            if 'input_reference' in request.files:
                file = request.files['input_reference']
                if file and file.filename:
                    # Save file temporarily
                    os.makedirs('temp', exist_ok=True)
                    temp_filename = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{file.filename}"
                    input_reference_path = os.path.join('temp', temp_filename)
                    file.save(input_reference_path)
        else:
            # JSON request (backward compatible)
            data = request.json
            input_reference_path = None
        
        # Generate unique job ID
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Start background thread
        thread = threading.Thread(
            target=create_video_async,
            args=(job_id, data, input_reference_path)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Video creation started'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/remix', methods=['POST'])
def remix_video():
    """
    Create a remix of an existing video with a new prompt.
    
    Initiates an asynchronous remix job that transforms an existing completed
    video based on a new text prompt. Returns a job ID for status polling.
    
    Request Body:
        {
            "video_id": "video_abc123" (required, source video ID),
            "prompt": "New transformation prompt" (required)
        }
    
    Returns:
        JSON response:
        {
            "success": true,
            "job_id": "job_20240115_143022_123456",
            "message": "Video remix started"
        }
    
    Status Codes:
        200: Remix job started successfully
        400: Missing required parameters (video_id or prompt)
        500: Server error during job initialization
    
    Example:
        POST /api/remix
        Content-Type: application/json
        {
            "video_id": "video_abc123",
            "prompt": "Make it look like a watercolor painting"
        }
    """
    try:
        data = request.json
        video_id = data.get('video_id')
        prompt = data.get('prompt')
        
        print(f"[API] Remix request received - Video ID: {video_id}, Prompt: {prompt}")
        
        if not video_id:
            print(f"[API] ERROR: video_id is required")
            return jsonify({
                'success': False,
                'error': 'video_id is required'
            }), 400
            
        if not prompt:
            print(f"[API] ERROR: prompt is required")
            return jsonify({
                'success': False,
                'error': 'prompt is required'
            }), 400
        
        # Generate unique job ID
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        print(f"[API] Created job ID: {job_id}")
        
        # Start background thread
        thread = threading.Thread(
            target=remix_video_async,
            args=(job_id, video_id, prompt)
        )
        thread.daemon = True
        thread.start()
        
        print(f"[API] Background thread started for job: {job_id}")
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Video remix started'
        })
        
    except Exception as e:
        print(f"[API] Remix endpoint error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/status/<job_id>')
def get_status(job_id):
    """
    Get the current status of an asynchronous job.
    
    Polls the progress of a video creation or remix job. The frontend should
    call this endpoint repeatedly (e.g., every 2-3 seconds) until the job
    reaches a terminal state (completed, failed, or error).
    
    Args:
        job_id (str): The unique job identifier returned from /api/create or /api/remix.
    
    Returns:
        JSON response with job status:
        {
            "status": "in_progress" | "completed" | "failed" | "error",
            "progress": 0-100,
            "message": "Human-readable status",
            "video_id": "video_abc123" (when available),
            "video_path": "/videos/video_abc123/video_abc123.mp4" (when complete),
            "thumbnail_path": "/videos/video_abc123/thumbnail.webp" (when complete),
            "result": {...} (full API response when complete),
            "error_details": {...} (on error)
        }
    
    Status Codes:
        200: Job found, returns current status
        404: Job not found
    
    Example:
        GET /api/status/job_20240115_143022_123456
        Response: {"status": "in_progress", "progress": 45, "message": "Generating video..."}
    """
    if job_id in job_status:
        return jsonify(job_status[job_id])
    else:
        return jsonify({
            'status': 'not_found',
            'message': 'Job not found'
        }), 404


@app.route('/api/gallery')
def get_gallery():
    """
    Get a list of all locally stored videos.
    
    Scans the videos/ directory for downloaded videos and their metadata.
    Returns information about each video including paths to video files,
    thumbnails, and creation parameters.
    
    Returns:
        JSON response:
        {
            "success": true,
            "videos": [
                {
                    "id": "video_abc123",
                    "video_path": "/videos/video_abc123/video_abc123.mp4",
                    "thumbnail_path": "/videos/video_abc123/thumbnail.webp",
                    "metadata": {...},
                    "created_at": "2024-01-15T14:30:22"
                },
                ...
            ]
        }
    
    Status Codes:
        200: Success (may return empty list if no videos exist)
        500: Server error during directory scan
    
    Note:
        Videos are sorted by creation time (newest first). Supports both
        the new directory structure (videos/{id}/) and legacy flat structure
        for backward compatibility.
    
    Example:
        GET /api/gallery
        Response: {"success": true, "videos": [...]}
    """
    try:
        videos = []
        if os.path.exists('videos'):
            # Scan for video directories (new structure)
            for item in os.listdir('videos'):
                item_path = os.path.join('videos', item)
                if os.path.isdir(item_path):
                    video_id = item
                    metadata_path = os.path.join(item_path, 'metadata.json')
                    video_file = os.path.join(item_path, f'{video_id}.mp4')
                    thumbnail_file = os.path.join(item_path, 'thumbnail.webp')
                    
                    if os.path.exists(video_file):
                        # Load metadata if it exists and is valid
                        metadata = {}
                        if os.path.exists(metadata_path):
                            try:
                                with open(metadata_path, 'r') as f:
                                    content = f.read().strip()
                                    if content:  # Only parse if file has content
                                        metadata = json.loads(content)
                            except (json.JSONDecodeError, Exception) as e:
                                print(f"Warning: Could not load metadata for {video_id}: {e}")
                                # Use empty metadata as fallback
                                metadata = {}
                        
                        # Get file modification time as fallback for created_at
                        file_mtime = os.path.getmtime(video_file)
                        created_at = metadata.get('saved_at', datetime.fromtimestamp(file_mtime).isoformat())
                        
                        videos.append({
                            'id': video_id,
                            'video_path': f'/videos/{video_id}/{video_id}.mp4',
                            'thumbnail_path': f'/videos/{video_id}/thumbnail.webp' if os.path.exists(thumbnail_file) else None,
                            'metadata': metadata,
                            'created_at': created_at
                        })
            
            # Also support old flat structure for backward compatibility
            for filename in os.listdir('videos'):
                if filename.endswith('.json') and not os.path.isdir(os.path.join('videos', filename)):
                    json_path = os.path.join('videos', filename)
                    try:
                        with open(json_path, 'r') as f:
                            content = f.read().strip()
                            if content:
                                metadata = json.loads(content)
                            else:
                                metadata = {}
                    except (json.JSONDecodeError, Exception):
                        metadata = {}
                        
                    video_id = filename.replace('.json', '')
                    video_file = f"{video_id}.mp4"
                    thumbnail_file = f"{video_id}_thumbnail.webp"
                    
                    if os.path.exists(os.path.join('videos', video_file)):
                        videos.append({
                            'id': video_id,
                            'video_path': f'/videos/{video_file}',
                            'thumbnail_path': f'/videos/{thumbnail_file}',
                            'metadata': metadata,
                            'created_at': metadata.get('saved_at', '')
                        })
        
        # Sort by creation time (newest first)
        videos.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jsonify({
            'success': True,
            'videos': videos
        })
        
    except Exception as e:
        print(f"Gallery error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/videos')
def list_videos():
    """
    Get a list of all videos from the Sora API.
    
    Fetches the complete video library from OpenAI's Sora 2 API, including
    videos in all states (queued, in_progress, completed, failed). This
    provides access to videos that may not be downloaded locally yet.
    
    Returns:
        JSON response:
        {
            "success": true,
            "videos": [
                {
                    "id": "video_abc123",
                    "status": "completed",
                    "prompt": "Video description",
                    "model": "sora-2",
                    "created_at": 1705328422,
                    "completed_at": 1705328490,
                    "size": "1920x1080",
                    "seconds": 5
                },
                ...
            ],
            "has_more": false
        }
    
    Status Codes:
        200: Success
        500: API error or connection failure
    
    Note:
        Currently retrieves up to 100 videos. Pagination can be implemented
        if needed for larger video libraries.
    
    Example:
        GET /api/videos
        Response: {"success": true, "videos": [...], "has_more": false}
    """
    try:
        client = SoraAPIClient()
        result = client.list(limit=100)  # Get up to 100 videos
        
        videos_list = []
        if 'data' in result:
            for video in result['data']:
                videos_list.append({
                    'id': video.get('id'),
                    'status': video.get('status'),
                    'prompt': video.get('prompt', ''),
                    'model': video.get('model', ''),
                    'created_at': video.get('created_at', 0),
                    'completed_at': video.get('completed_at'),
                    'size': video.get('size', ''),
                    'seconds': video.get('seconds', 0)
                })
        
        return jsonify({
            'success': True,
            'videos': videos_list,
            'has_more': result.get('has_more', False)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/videos/<path:filename>')
def serve_video(filename):
    """
    Serve video files and related assets from the videos directory.
    
    Args:
        filename (str): Relative path to the file (e.g., "video_abc123/video_abc123.mp4").
    
    Returns:
        File response with appropriate MIME type.
    
    Example:
        GET /videos/video_abc123/video_abc123.mp4
        GET /videos/video_abc123/thumbnail.webp
    """
    return send_from_directory('videos', filename)


@app.route('/api/download/<video_id>', methods=['GET'])
def download_video_endpoint(video_id):
    """
    Download a video from the Sora API to local storage.
    
    Checks if the video exists locally first. If not, downloads it from the
    OpenAI API along with its thumbnail and metadata. This endpoint is used
    to sync videos from the API to local storage.
    
    Args:
        video_id (str): The unique identifier of the video to download.
    
    Returns:
        JSON response:
        {
            "success": true,
            "message": "Video downloaded successfully",
            "video_path": "/videos/video_abc123/video_abc123.mp4"
        }
    
    Status Codes:
        200: Video available (already existed or downloaded successfully)
        400: Video not ready for download (not completed yet)
        404: Video not found on server
        500: Download or file system error
    
    Side Effects:
        - Creates videos/{video_id}/ directory
        - Downloads {video_id}.mp4, thumbnail.webp
        - Saves metadata.json
    
    Example:
        GET /api/download/video_abc123
        Response: {"success": true, "video_path": "/videos/video_abc123/video_abc123.mp4"}
    """
    try:
        print(f"[DOWNLOAD] Request for video: {video_id}")
        
        # Check if video file exists locally
        video_dir = f"videos/{video_id}"
        video_file = os.path.join(video_dir, f"{video_id}.mp4")
        
        if os.path.exists(video_file):
            print(f"[DOWNLOAD] Video already exists locally: {video_file}")
            return jsonify({
                'success': True,
                'message': 'Video already exists locally',
                'video_path': f'/videos/{video_id}/{video_id}.mp4'
            })
        
        print(f"[DOWNLOAD] Video not found locally, downloading from OpenAI...")
        
        # Create directory if it doesn't exist
        os.makedirs(video_dir, exist_ok=True)
        
        # Initialize client and download
        client = SoraAPIClient()
        
        # First check if video exists on server
        try:
            video_info = client.retrieve(video_id)
            print(f"[DOWNLOAD] Video info: status={video_info.get('status')}")
            
            if video_info.get('status') != 'completed':
                return jsonify({
                    'success': False,
                    'error': f'Video is not ready for download. Status: {video_info.get("status")}'
                }), 400
        except Exception as e:
            print(f"[DOWNLOAD] Error retrieving video info: {e}")
            return jsonify({
                'success': False,
                'error': f'Video not found on server: {str(e)}'
            }), 404
        
        # Download the video
        print(f"[DOWNLOAD] Downloading to {video_dir}...")
        downloaded_file = client.download(video_id, output_dir=video_dir)
        print(f"[DOWNLOAD] Downloaded: {downloaded_file}")
        
        # Download thumbnail if it doesn't exist
        thumbnail_file = os.path.join(video_dir, 'thumbnail.webp')
        if not os.path.exists(thumbnail_file):
            print(f"[DOWNLOAD] Downloading thumbnail...")
            try:
                client.generate_thumbnail(video_id, thumbnail_file)
            except Exception as thumb_error:
                print(f"[DOWNLOAD] Thumbnail download failed: {thumb_error}")
                # Continue even if thumbnail fails
        
        # Save metadata if it doesn't exist
        metadata_file = os.path.join(video_dir, 'metadata.json')
        if not os.path.exists(metadata_file):
            print(f"[DOWNLOAD] Saving metadata...")
            metadata = {
                'video_id': video_id,
                'prompt': video_info.get('prompt'),
                'model': video_info.get('model'),
                'seconds': video_info.get('duration'),
                'size': video_info.get('resolution'),
                'created_at': video_info.get('created_at'),
                'status': video_info.get('status'),
                'saved_at': datetime.now().isoformat()
            }
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
        
        print(f"[DOWNLOAD] Download complete, file saved to: {downloaded_file}")
        
        return jsonify({
            'success': True,
            'message': 'Video downloaded successfully',
            'video_path': f'/videos/{video_id}/{video_id}.mp4'
        })
        
    except Exception as e:
        print(f"[DOWNLOAD] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/delete/<video_id>', methods=['DELETE'])
def delete_video(video_id):
    """
    Delete a video from the Sora API (preserves local files).
    
    Removes the video from OpenAI's servers while keeping local downloaded
    files intact. This is useful for cleaning up the API library while
    maintaining a local archive.
    
    Args:
        video_id (str): The unique identifier of the video to delete from the API.
    
    Returns:
        JSON response:
        {
            "success": true,
            "message": "Video deleted from API (local files preserved)",
            "api_deleted": true,
            "local_deleted": false,
            "api_error": null
        }
    
    Status Codes:
        200: Deletion completed (see api_deleted field for actual result)
        400: Video cannot be deleted (still processing)
        500: Server error
    
    Note:
        Videos in 'queued' or 'in_progress' states cannot be deleted and
        will return a 400 error. Local files are never deleted by this endpoint.
    
    Example:
        DELETE /api/delete/video_abc123
        Response: {"success": true, "api_deleted": true, "local_deleted": false}
    """
    try:
        import shutil
        client = SoraAPIClient()
        
        print(f"\n=== DELETE REQUEST ===")
        print(f"Video ID received: {video_id}")
        print(f"Video ID length: {len(video_id)}")
        print(f"Video ID repr: {repr(video_id)}")
        
        # First check video status
        video_status = None
        try:
            video_info = client.retrieve(video_id)
            video_status = video_info.get('status')
            print(f"Video status: {video_status}")
            
            if video_status in ['queued', 'in_progress']:
                return jsonify({
                    'success': False,
                    'error': f'Cannot delete video while it is {video_status}. Please wait until the video is completed or has failed.',
                    'status': video_status
                }), 400
        except Exception as e:
            print(f"Warning: Could not check video status: {e}")
            # Continue anyway - maybe it's a local-only video
        
        # Delete from API ONLY (don't touch local files)
        api_delete_success = False
        api_delete_error = None
        try:
            print(f"Calling client.delete({video_id})...")
            result = client.delete(video_id)
            api_delete_success = True
            print(f"✓ API delete successful: {result}")
        except Exception as api_error:
            api_delete_error = str(api_error)
            print(f"✗ API delete failed: {api_error}")
            import traceback
            traceback.print_exc()
        
        # NOTE: We do NOT delete local files - only delete via REST API
        print(f"Local files preserved (not deleted)")
        
        print(f"\n=== DELETE RESULT ===")
        print(f"API deleted: {api_delete_success}")
        print(f"API error: {api_delete_error}")
        
        if api_delete_success:
            return jsonify({
                'success': True,
                'message': 'Video deleted from API (local files preserved)',
                'api_deleted': True,
                'local_deleted': False,
                'api_error': None
            })
        else:
            return jsonify({
                'success': False,
                'message': 'API delete failed',
                'api_deleted': False,
                'local_deleted': False,
                'api_error': api_delete_error
            })
        
    except Exception as e:
        print(f"Delete error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/delete-local/<video_id>', methods=['DELETE'])
def delete_local_video(video_id):
    """
    Delete a video's local files only (does not affect API).
    
    Removes the local directory and all downloaded files for a video
    (video file, thumbnail, spritesheet, metadata) without touching
    the video on OpenAI's servers. This is useful for freeing local
    disk space while keeping videos available in the cloud.
    
    Args:
        video_id (str): The unique identifier of the video whose local files to delete.
    
    Returns:
        JSON response:
        {
            "success": true,
            "message": "Local files deleted for video video_abc123",
            "local_deleted": true
        }
    
    Status Codes:
        200: Local files deleted successfully
        404: Local files not found
        500: File system error
    
    Side Effects:
        - Recursively deletes videos/{video_id}/ directory and all contents
    
    Example:
        DELETE /api/delete-local/video_abc123
        Response: {"success": true, "local_deleted": true}
    """
    try:
        import shutil
        
        print(f"\n=== DELETE LOCAL REQUEST ===")
        print(f"Video ID: {video_id}")
        
        # Delete local files
        video_dir = f"videos/{video_id}"
        
        if os.path.exists(video_dir):
            print(f"Deleting local directory: {video_dir}")
            shutil.rmtree(video_dir)
            print(f"✓ Local files deleted successfully")
            
            return jsonify({
                'success': True,
                'message': f'Local files deleted for video {video_id}',
                'local_deleted': True
            })
        else:
            print(f"✗ Local directory not found: {video_dir}")
            return jsonify({
                'success': False,
                'error': f'Local files not found for video {video_id}'
            }), 404
        
    except Exception as e:
        print(f"Delete local error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    # Ensure videos directory exists
    os.makedirs('videos', exist_ok=True)
    
    print("=" * 60)
    print("Sora 2 API Web Interface")
    print("=" * 60)
    print("\nStarting server at http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
