#!/usr/bin/env python3
"""
Sora 2 API Web Interface
A Flask-based web interface for the Sora 2 video generation API
"""

import os
import json
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from sora_api import SoraAPIClient

app = Flask(__name__)
CORS(app)

# Global dictionary to track job progress
job_status = {}

def create_video_async(job_id, params, input_reference_path=None):
    """Background thread to create video and track progress"""
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

def remix_video_async(job_id, video_id, prompt):
    """Background thread to remix video and track progress"""
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
    """Serve the main page"""
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    """Return empty favicon to avoid 404 errors"""
    return '', 204

@app.route('/api/create', methods=['POST'])
def create_video():
    """Endpoint to create a new video"""
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
    """Endpoint to remix an existing video"""
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
    """Get the status of a job"""
    if job_id in job_status:
        return jsonify(job_status[job_id])
    else:
        return jsonify({
            'status': 'not_found',
            'message': 'Job not found'
        }), 404

@app.route('/api/gallery')
def get_gallery():
    """Get list of all generated videos"""
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
    """Get list of all videos from the server"""
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
    """Serve video files"""
    return send_from_directory('videos', filename)

@app.route('/api/download/<video_id>', methods=['GET'])
def download_video_endpoint(video_id):
    """Download video from OpenAI if not available locally and return status"""
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
    """Delete a video and its associated files"""
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
    """Delete a video's local files only (does not touch API)"""
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
