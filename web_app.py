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
            'message': 'Video creation started, waiting for completion...'
        })
        
        # Poll for completion
        final_result = client.wait_for_completion(
            video_id,
            poll_interval=3,
            max_wait_time=600,
            show_progress=False
        )
        
        # Update status based on result
        if final_result.get('status') == 'completed':
            job_status[job_id].update({
                'status': 'downloading',
                'progress': 90,
                'message': 'Video completed, downloading...'
            })
            
            # Download all variants
            base_name = video_id
            video_file = f"videos/{base_name}.mp4"
            thumbnail_file = f"videos/{base_name}_thumbnail.webp"
            spritesheet_file = f"videos/{base_name}_spritesheet.jpg"
            
            # Ensure videos directory exists
            os.makedirs('videos', exist_ok=True)
            
            client.save_video(video_id, video_file, variant='video')
            client.save_video(video_id, thumbnail_file, variant='thumbnail')
            client.save_video(video_id, spritesheet_file, variant='spritesheet')
            
            # Save metadata
            client.save_video_info(final_result, params)
            
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

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

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
            # Get all JSON files (metadata)
            for filename in os.listdir('videos'):
                if filename.endswith('.json'):
                    json_path = os.path.join('videos', filename)
                    with open(json_path, 'r') as f:
                        metadata = json.load(f)
                        
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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/videos/<path:filename>')
def serve_video(filename):
    """Serve video files"""
    return send_from_directory('videos', filename)

@app.route('/api/delete/<video_id>', methods=['DELETE'])
def delete_video(video_id):
    """Delete a video and its associated files"""
    try:
        client = SoraAPIClient()
        
        # Delete from API
        try:
            client.delete(video_id)
        except:
            pass  # Continue even if API delete fails
        
        # Delete local files
        files_to_delete = [
            f"videos/{video_id}.mp4",
            f"videos/{video_id}_thumbnail.webp",
            f"videos/{video_id}_spritesheet.jpg",
            f"videos/{video_id}.json"
        ]
        
        for filepath in files_to_delete:
            if os.path.exists(filepath):
                os.remove(filepath)
        
        return jsonify({
            'success': True,
            'message': 'Video deleted successfully'
        })
        
    except Exception as e:
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
