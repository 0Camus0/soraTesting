#!/usr/bin/env python3
"""
Sora 2 API Client
=================

A comprehensive Python client for interacting with the OpenAI Sora 2 video generation API.

This module provides a high-level interface for:
- Creating videos from text prompts and image references
- Remixing existing videos with new prompts
- Managing video lifecycle (list, retrieve, delete)
- Downloading video content and thumbnails
- Monitoring video generation progress

Basic Usage:
    >>> from sora_api import SoraAPIClient
    >>> client = SoraAPIClient()
    >>> result = client.create(prompt="A sunset over the ocean", wait_for_completion=True)
    >>> client.save_video(result['id'], 'my_video.mp4')

API Key Configuration:
    The client looks for your OpenAI API key in the following order:
    1. api_key parameter passed to __init__()
    2. OPENAI_API_KEY environment variable
    3. OPENAI_API_KEY in .env file in the current directory

Author: OpenAI Sora Integration Team
Version: 1.0.0
License: MIT
"""

import os
import sys
import requests
import json
import time
import argparse
from datetime import datetime
from typing import Optional, Dict, Any, List


class SoraAPIClient:
    """
    Client for interacting with the OpenAI Sora 2 video generation API.
    
    This class provides methods for all Sora 2 API operations including video creation,
    remixing, listing, retrieval, deletion, and content downloading. It handles
    authentication, request formatting, error handling, and progress tracking.
    
    Attributes:
        api_key (str): The OpenAI API key used for authentication.
        base_url (str): The base URL for the Sora API endpoints.
        headers (dict): Default headers including authorization for API requests.
    
    Example:
        >>> client = SoraAPIClient(api_key="sk-...")
        >>> video = client.create(prompt="A cat playing piano", wait_for_completion=True)
        >>> client.save_video(video['id'], 'cat_piano.mp4')
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Sora API client with authentication credentials.
        
        The client will attempt to find an API key in the following order:
        1. The api_key parameter
        2. OPENAI_API_KEY environment variable
        3. OPENAI_API_KEY in a .env file
        
        Args:
            api_key (str, optional): OpenAI API key. If not provided, will attempt
                to load from environment variables or .env file.
        
        Raises:
            ValueError: If no API key can be found in any of the expected locations.
        
        Example:
            >>> # Using explicit API key
            >>> client = SoraAPIClient(api_key="sk-...")
            >>> 
            >>> # Using environment variable or .env file
            >>> client = SoraAPIClient()
        """
        # Try to load from .env file if environment variable is not set
        if not api_key and not os.getenv('OPENAI_API_KEY'):
            self._load_env_file()
        
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "API key not found. Please create a .env file with OPENAI_API_KEY, "
                "or set OPENAI_API_KEY environment variable, or pass api_key parameter."
            )
        
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def _load_env_file(self) -> None:
        """
        Load environment variables from a .env file if it exists.
        
        This internal method reads a .env file in the current directory and loads
        any KEY=VALUE pairs into the environment. Lines starting with # are treated
        as comments and ignored.
        
        Note:
            This method fails silently if the .env file doesn't exist or can't be read.
        
        Example .env file:
            # OpenAI API Configuration
            OPENAI_API_KEY=sk-proj-...
        """
        env_file = '.env'
        if os.path.exists(env_file):
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
            except Exception as e:
                pass  # Silently fail if .env can't be read
    
    def create(
        self, 
        prompt: str, 
        model: str = "sora-2", 
        input_reference: Optional[str] = None, 
        seconds: Optional[str] = None, 
        size: Optional[str] = None, 
        wait_for_completion: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new video using the Sora 2 API.
        
        This method submits a video generation request to the Sora API. Videos can be
        created from text prompts alone or guided by a reference image. The method
        can optionally wait for the video to complete before returning.
        
        Args:
            prompt (str): Text description of the video to generate. Be specific and
                descriptive for best results.
            model (str): The video generation model to use. Defaults to "sora-2".
            input_reference (str, optional): Path to a local image file (.jpg, .jpeg,
                .png, or .webp) to use as a visual reference for generation.
            seconds (str, optional): Clip duration in seconds (e.g., "5" or "10").
                Defaults to 4 seconds if not specified.
            size (str, optional): Output resolution in format "WIDTHxHEIGHT"
                (e.g., "1920x1080"). Defaults to "720x1280" if not specified.
            wait_for_completion (bool): If True, polls the API until the video is
                complete and returns the final status. If False, returns immediately
                with the initial job status. Defaults to False.
        
        Returns:
            dict: A dictionary containing the video job information with keys:
                - id (str): Unique identifier for the video
                - status (str): Current status ('queued', 'in_progress', 'completed', etc.)
                - progress (int): Generation progress percentage (0-100)
                - prompt (str): The prompt used for generation
                - created_at (str): ISO timestamp of job creation
                - Additional fields depending on status
        
        Raises:
            FileNotFoundError: If input_reference path doesn't exist.
            ValueError: If input_reference file format is unsupported.
            requests.exceptions.HTTPError: If the API returns an error response.
            requests.exceptions.RequestException: If network/connection error occurs.
        
        Example:
            >>> # Simple text-to-video
            >>> client = SoraAPIClient()
            >>> result = client.create(
            ...     prompt="A golden retriever running through a field",
            ...     seconds="5",
            ...     wait_for_completion=True
            ... )
            >>> print(f"Video ID: {result['id']}")
            >>> 
            >>> # Image-guided generation
            >>> result = client.create(
            ...     prompt="Transform this into a watercolor painting",
            ...     input_reference="photo.jpg",
            ...     size="1920x1080"
            ... )
        """
        url = f"{self.base_url}/videos"
        
        # If input_reference is provided, use multipart/form-data
        if input_reference is not None:
            # Prepare multipart form data
            files = {}
            data = {
                "prompt": prompt,
                "model": model
            }
            
            if seconds is not None:
                data["seconds"] = seconds
            if size is not None:
                data["size"] = size
            
            # Open the image file
            try:
                with open(input_reference, 'rb') as f:
                    # Determine the MIME type based on file extension
                    ext = os.path.splitext(input_reference)[1].lower()
                    mime_type = {
                        '.jpg': 'image/jpeg',
                        '.jpeg': 'image/jpeg',
                        '.png': 'image/png',
                        '.webp': 'image/webp'
                    }.get(ext, 'image/jpeg')
                    
                    files = {
                        'input_reference': (os.path.basename(input_reference), f.read(), mime_type)
                    }
                    
                    # Update headers for multipart request
                    headers = {
                        "Authorization": f"Bearer {self.api_key}"
                    }
                    # Don't set Content-Type - requests will set it automatically with boundary
                    
                    print(f"Creating video with prompt: '{prompt}' and reference image '{input_reference}'...")
                    response = requests.post(url, headers=headers, data=data, files=files)
                    response.raise_for_status()
                    
                    result = response.json()
                    print("Video creation job submitted successfully!")
                    
                    # Wait for completion if requested
                    if wait_for_completion:
                        video_id = result.get('id')
                        if video_id:
                            result = self.wait_for_completion(video_id)
                    
                    return result
                    
            except FileNotFoundError:
                raise ValueError(f"Reference image file not found: {input_reference}")
            except requests.exceptions.HTTPError as e:
                print(f"HTTP Error: {e}")
                print(f"Response: {e.response.text}")
                raise
            except requests.exceptions.RequestException as e:
                print(f"Request Error: {e}")
                raise
            except Exception as e:
                raise ValueError(f"Error reading reference image: {e}")
        else:
            # Use JSON payload when no file is provided
            payload = {
                "prompt": prompt,
                "model": model
            }
            
            if seconds is not None:
                payload["seconds"] = seconds
            if size is not None:
                payload["size"] = size
            
            try:
                print(f"Creating video with prompt: '{prompt}'...")
                response = requests.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                
                result = response.json()
                print("Video creation job submitted successfully!")
                
                # Wait for completion if requested
                if wait_for_completion:
                    video_id = result.get('id')
                    if video_id:
                        result = self.wait_for_completion(video_id)
                
                return result
                
            except requests.exceptions.HTTPError as e:
                print(f"HTTP Error: {e}")
                print(f"Response: {e.response.text}")
                raise
            except requests.exceptions.RequestException as e:
                print(f"Request Error: {e}")
                raise
    
    def remix(
        self, 
        video_id: str, 
        prompt: str, 
        wait_for_completion: bool = False
    ) -> Dict[str, Any]:
        """
        Create a remix (variation) of an existing video with a new prompt.
        
        Remixing allows you to create variations of existing videos by applying a new
        prompt. The original video serves as a base, and the new prompt guides how it
        should be modified or transformed.
        
        Args:
            video_id (str): The unique identifier of the completed video to remix.
                The original video must have status='completed'.
            prompt (str): New text prompt that describes the desired modifications
                or transformations to apply to the original video.
            wait_for_completion (bool): If True, polls until the remix is complete.
                If False, returns immediately with initial job status. Defaults to False.
        
        Returns:
            dict: A dictionary containing the remix job information with keys:
                - id (str): Unique identifier for the new remix video
                - status (str): Current status of the remix job
                - progress (int): Remix progress percentage (0-100)
                - prompt (str): The remix prompt
                - source_video_id (str): ID of the original video
                - created_at (str): ISO timestamp of remix job creation
        
        Raises:
            requests.exceptions.HTTPError: If the API returns an error (e.g., video
                not found, video not completed, invalid prompt).
            requests.exceptions.RequestException: If network/connection error occurs.
        
        Example:
            >>> client = SoraAPIClient()
            >>> # First create a video
            >>> original = client.create(
            ...     prompt="A city street in daylight",
            ...     wait_for_completion=True
            ... )
            >>> 
            >>> # Then remix it
            >>> remix = client.remix(
            ...     video_id=original['id'],
            ...     prompt="Transform to nighttime with neon lights",
            ...     wait_for_completion=True
            ... )
            >>> print(f"Remix ID: {remix['id']}")
        """
        url = f"{self.base_url}/videos/{video_id}/remix"
        
        payload = {
            "prompt": prompt
        }
        
        try:
            print(f"Creating remix of video '{video_id}' with prompt: '{prompt}'...")
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            print("Video remix job submitted successfully!")
            
            # Wait for completion if requested
            if wait_for_completion:
                remix_video_id = result.get('id')
                if remix_video_id:
                    result = self.wait_for_completion(remix_video_id)
            
            return result
            
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            print(f"Response: {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
            raise
    
    def list(
        self, 
        after: Optional[str] = None, 
        limit: Optional[int] = None, 
        order: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List videos in your organization with pagination support.
        
        Retrieves a paginated list of all videos created by your organization.
        Results can be sorted and paginated for efficient browsing of large
        video collections.
        
        Args:
            after (str, optional): Cursor identifier from a previous response.
                Use this to retrieve the next page of results. The cursor value
                comes from the 'last_id' field of a previous list() response.
            limit (int, optional): Maximum number of videos to return per request.
                Typical values range from 10-100. If not specified, API default is used.
            order (str, optional): Sort order by creation timestamp. Valid values:
                - 'asc': Oldest videos first
                - 'desc': Newest videos first (default)
        
        Returns:
            dict: A dictionary containing paginated video data:
                - data (list): List of video objects, each containing:
                    - id (str): Video identifier
                    - status (str): Current status
                    - prompt (str): Generation prompt
                    - created_at (str): Creation timestamp
                    - progress (int): Generation progress
                - has_more (bool): True if more results are available
                - last_id (str): Cursor for fetching the next page
        
        Raises:
            requests.exceptions.HTTPError: If the API returns an error response.
            requests.exceptions.RequestException: If network/connection error occurs.
        
        Example:
            >>> client = SoraAPIClient()
            >>> 
            >>> # Get first page of videos (most recent first)
            >>> page1 = client.list(limit=20, order='desc')
            >>> print(f"Found {len(page1['data'])} videos")
            >>> 
            >>> # Get next page if available
            >>> if page1.get('has_more'):
            ...     page2 = client.list(after=page1['last_id'], limit=20)
            >>> 
            >>> # Get all completed videos
            >>> all_videos = client.list(limit=100)
            >>> completed = [v for v in all_videos['data'] if v['status'] == 'completed']
        """
        url = f"{self.base_url}/videos"
        
        params = {}
        if after is not None:
            params["after"] = after
        if limit is not None:
            params["limit"] = limit
        if order is not None:
            params["order"] = order
        
        try:
            print("Retrieving list of videos...")
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            result = response.json()
            print(f"Retrieved {len(result.get('data', []))} video(s)!")
            return result
            
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            print(f"Response: {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
            raise
    
    def retrieve(self, video_id: str) -> Dict[str, Any]:
        """
        Retrieve detailed information about a specific video.
        
        Fetches the current state and metadata for a video, including its status,
        progress, prompts, dimensions, and other properties. This is useful for
        checking the status of ongoing generations or getting details about
        completed videos.
        
        Args:
            video_id (str): The unique identifier of the video to retrieve.
                This ID is returned when creating or listing videos.
        
        Returns:
            dict: Complete video information including:
                - id (str): Video identifier
                - status (str): Current status ('queued', 'in_progress', 'completed',
                    'failed', 'cancelled', 'incomplete')
                - progress (int): Generation progress (0-100)
                - prompt (str): Text prompt used for generation
                - model (str): Model used (e.g., 'sora-2')
                - created_at (str): ISO timestamp of creation
                - completed_at (str, optional): ISO timestamp of completion
                - duration (float, optional): Video duration in seconds
                - dimensions (dict, optional): Width and height
                - error (dict, optional): Error details if status is 'failed'
        
        Raises:
            requests.exceptions.HTTPError: If video not found or API error occurs.
            requests.exceptions.RequestException: If network/connection error occurs.
        
        Example:
            >>> client = SoraAPIClient()
            >>> 
            >>> # Check status of a video
            >>> video = client.retrieve("video_abc123")
            >>> print(f"Status: {video['status']}")
            >>> print(f"Progress: {video['progress']}%")
            >>> 
            >>> # Wait manually by checking status
            >>> while video['status'] == 'in_progress':
            ...     time.sleep(5)
            ...     video = client.retrieve(video['id'])
            ...     print(f"Progress: {video['progress']}%")
        """
        url = f"{self.base_url}/videos/{video_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            return result
            
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            print(f"Response: {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
            raise
    
    def wait_for_completion(
        self, 
        video_id: str, 
        poll_interval: int = 3, 
        max_wait_time: int = 60000, 
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Wait for a video generation job to complete by polling its status.
        
        This method repeatedly checks the video status at regular intervals until
        it reaches a terminal state (completed, failed, cancelled, or incomplete).
        It provides real-time progress updates and handles timeouts.
        
        Args:
            video_id (str): The identifier of the video to monitor.
            poll_interval (int): Number of seconds to wait between status checks.
                Shorter intervals provide more frequent updates but increase API usage.
                Defaults to 3 seconds.
            max_wait_time (int): Maximum number of seconds to wait before timing out.
                Defaults to 60000 seconds (16.67 hours). Set lower for faster timeout.
            show_progress (bool): If True, prints progress updates to stdout including
                status changes and progress percentages. Defaults to True.
        
        Returns:
            dict: The final video information after completion, containing all fields
                from retrieve() plus completion timestamp and final status.
        
        Raises:
            TimeoutError: If the video doesn't complete within max_wait_time seconds.
            Exception: If the video generation fails, is cancelled, or becomes incomplete.
                The exception message includes details from the API error response.
        
        Example:
            >>> client = SoraAPIClient()
            >>> 
            >>> # Create and wait with custom settings
            >>> result = client.create(prompt="A dancing robot")
            >>> final = client.wait_for_completion(
            ...     video_id=result['id'],
            ...     poll_interval=5,  # Check every 5 seconds
            ...     max_wait_time=300,  # Timeout after 5 minutes
            ...     show_progress=True
            ... )
            >>> print(f"Video completed: {final['id']}")
            >>> 
            >>> # Silent wait (no progress output)
            >>> final = client.wait_for_completion(
            ...     video_id=result['id'],
            ...     show_progress=False
            ... )
        """
        if show_progress:
            print(f"\nWaiting for video '{video_id}' to complete...")
        
        start_time = time.time()
        last_status = None
        last_progress = None
        
        while True:
            # Check if we've exceeded max wait time
            elapsed = time.time() - start_time
            if elapsed > max_wait_time:
                raise TimeoutError(
                    f"Video generation timed out after {max_wait_time} seconds. "
                    f"Video ID: {video_id}"
                )
            
            # Get current video status
            try:
                video = self.retrieve(video_id)
            except Exception as e:
                print(f"\nError retrieving video status: {e}")
                time.sleep(poll_interval)
                continue
            
            status = video.get('status', 'unknown')
            progress = video.get('progress', 0)
            
            # Display progress if it changed
            if show_progress and (status != last_status or progress != last_progress):
                elapsed_str = f"{int(elapsed)}s"
                
                if status == 'queued':
                    print(f"  [{elapsed_str}] Status: Queued, waiting to start...")
                elif status == 'in_progress':
                    progress_bar = self._create_progress_bar(progress)
                    print(f"  [{elapsed_str}] Progress: {progress_bar} {progress}%")
                elif status == 'completed':
                    print(f"  [{elapsed_str}] Status: Completed! ✓")
                elif status == 'failed':
                    error_msg = video.get('error', {}).get('message', 'Unknown error')
                    print(f"  [{elapsed_str}] Status: Failed - {error_msg}")
                elif status == 'cancelled':
                    print(f"  [{elapsed_str}] Status: Cancelled")
                elif status == 'incomplete':
                    print(f"  [{elapsed_str}] Status: Incomplete")
                
                last_status = status
                last_progress = progress
            
            # Check for terminal states
            if status == 'completed':
                if show_progress:
                    print(f"\n✓ Video generation completed successfully!")
                    print(f"  Total time: {int(elapsed)} seconds")
                return video
            
            elif status == 'failed':
                error_info = video.get('error', {})
                error_msg = error_info.get('message', 'Unknown error occurred')
                raise Exception(f"Video generation failed: {error_msg}")
            
            elif status == 'cancelled':
                raise Exception("Video generation was cancelled")
            
            elif status == 'incomplete':
                raise Exception("Video generation incomplete")
            
            # Wait before next poll
            time.sleep(poll_interval)
    
    def _create_progress_bar(self, progress: int, width: int = 30) -> str:
        """
        Create a text-based progress bar visualization.
        
        Generates a Unicode progress bar string with filled and unfilled segments
        to represent completion percentage visually in terminal output.
        
        Args:
            progress (int): Progress percentage from 0 to 100.
            width (int): Total character width of the progress bar. Defaults to 30.
        
        Returns:
            str: A formatted progress bar string like "[████████░░░░░░░░░░░░░░░░░░░░]"
        
        Example:
            >>> client = SoraAPIClient()
            >>> print(client._create_progress_bar(0))
            [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]
            >>> print(client._create_progress_bar(50))
            [███████████████░░░░░░░░░░░░░░░]
            >>> print(client._create_progress_bar(100))
            [██████████████████████████████]
        """
        filled = int(width * progress / 100)
        bar = '█' * filled + '░' * (width - filled)
        return f"[{bar}]"
    
    def save_video_info(
        self, 
        video_data: Dict[str, Any], 
        creation_args: Optional[Dict[str, Any]] = None, 
        output_dir: str = "videos"
    ) -> str:
        """
        Save video metadata to a JSON file for record-keeping.
        
        Stores complete video information and creation parameters to a JSON file,
        useful for tracking generation history, debugging, and documentation.
        
        Args:
            video_data (dict): The complete video information returned by the API.
                Should include fields like id, status, prompt, etc.
            creation_args (dict, optional): The original arguments used to create
                the video (prompt, model, size, etc.). If provided, these are
                stored alongside the API response.
            output_dir (str): Directory where the JSON file will be saved.
                Defaults to "videos". Directory is created if it doesn't exist.
        
        Returns:
            str: Absolute path to the saved JSON file.
        
        Example:
            >>> client = SoraAPIClient()
            >>> result = client.create(
            ...     prompt="A forest scene",
            ...     size="1920x1080",
            ...     wait_for_completion=True
            ... )
            >>> 
            >>> # Save with creation arguments
            >>> json_path = client.save_video_info(
            ...     video_data=result,
            ...     creation_args={"prompt": "A forest scene", "size": "1920x1080"},
            ...     output_dir="my_videos"
            ... )
            >>> print(f"Metadata saved to: {json_path}")
        """
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        video_id = video_data.get('id', 'unknown')
        filename = os.path.join(output_dir, f"{video_id}.json")
        
        # Combine API response with creation arguments
        info = {
            "saved_at": datetime.now().isoformat(),
            "creation_args": creation_args or {},
            "api_response": video_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2, ensure_ascii=False)
        
        print(f"Video info saved to: {filename}")
        return filename
    
    def delete(self, video_id: str) -> Dict[str, Any]:
        """
        Delete a video from your organization's video library.
        
        Permanently removes a video and all its associated data from the Sora API.
        This action cannot be undone. The video content, metadata, and variants
        will no longer be accessible.
        
        Args:
            video_id (str): The unique identifier of the video to delete.
        
        Returns:
            dict: Deletion confirmation response containing:
                - id (str): ID of the deleted video
                - object (str): Object type (typically "video")
                - deleted (bool): True if deletion was successful
        
        Raises:
            requests.exceptions.HTTPError: If video not found or API error occurs.
            requests.exceptions.RequestException: If network/connection error occurs.
        
        Warning:
            This operation is irreversible. Make sure you have downloaded any content
            you want to keep before deleting a video.
        
        Example:
            >>> client = SoraAPIClient()
            >>> 
            >>> # Delete a video
            >>> result = client.delete("video_abc123")
            >>> print(f"Deleted: {result['deleted']}")
            >>> 
            >>> # Delete with confirmation
            >>> video_id = "video_xyz789"
            >>> confirm = input(f"Delete {video_id}? (yes/no): ")
            >>> if confirm.lower() == 'yes':
            ...     client.delete(video_id)
        """
        url = f"{self.base_url}/videos/{video_id}"
        
        try:
            print(f"Deleting video '{video_id}'...")
            response = requests.delete(url, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            print("Video deleted successfully!")
            return result
            
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            print(f"Response: {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
            raise
    
    def get_content(
        self, 
        video_id: str, 
        variant: Optional[str] = None
    ) -> bytes:
        """
        Download video content as raw bytes.
        
        Retrieves the binary content of a video or one of its variants from the API.
        This is a low-level method; consider using save_video() or download() for
        simpler file-based operations.
        
        Args:
            video_id (str): The identifier of the video whose content to download.
            variant (str, optional): The variant of the content to download. Options:
                - None or 'video': Full video file (MP4 format)
                - 'thumbnail': Single thumbnail image (WebP format)
                - 'spritesheet': Grid of thumbnails (JPEG format)
                If not specified, downloads the full video.
        
        Returns:
            bytes: Raw binary content of the requested video or variant.
        
        Raises:
            requests.exceptions.HTTPError: If video not found, not completed, or
                API error occurs.
            requests.exceptions.RequestException: If network/connection error occurs.
        
        Example:
            >>> client = SoraAPIClient()
            >>> 
            >>> # Get full video content
            >>> video_bytes = client.get_content("video_abc123")
            >>> with open("my_video.mp4", "wb") as f:
            ...     f.write(video_bytes)
            >>> 
            >>> # Get thumbnail
            >>> thumb_bytes = client.get_content("video_abc123", variant="thumbnail")
            >>> with open("thumb.webp", "wb") as f:
            ...     f.write(thumb_bytes)
        """
        url = f"{self.base_url}/videos/{video_id}/content"
        
        params = {}
        if variant is not None:
            params["variant"] = variant
        
        try:
            print(f"Downloading content for video '{video_id}'...")
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            print("Video content downloaded successfully!")
            return response.content
            
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            print(f"Response: {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
            raise
    
    def save_video(
        self, 
        video_id: str, 
        filename: str, 
        variant: Optional[str] = None
    ) -> str:
        """
        Download and save video content directly to a file.
        
        Retrieves video content from the API and writes it to a local file in one
        operation. This is the recommended method for downloading videos.
        
        Args:
            video_id (str): The identifier of the video to download.
            filename (str): The local path where the file should be saved.
                Should include appropriate extension (.mp4 for video, .webp for
                thumbnail, .jpg for spritesheet).
            variant (str, optional): The content variant to download:
                - None or 'video': Full video (recommend .mp4 extension)
                - 'thumbnail': Thumbnail image (recommend .webp extension)
                - 'spritesheet': Spritesheet image (recommend .jpg extension)
        
        Returns:
            str: The path to the saved file (same as the filename parameter).
        
        Raises:
            requests.exceptions.HTTPError: If video not found or API error.
            requests.exceptions.RequestException: If network error occurs.
            OSError: If file cannot be written (permissions, disk space, etc.).
        
        Example:
            >>> client = SoraAPIClient()
            >>> video_id = "video_abc123"
            >>> 
            >>> # Download full video
            >>> client.save_video(video_id, "output.mp4")
            >>> 
            >>> # Download thumbnail
            >>> client.save_video(video_id, "thumbnail.webp", variant="thumbnail")
            >>> 
            >>> # Download spritesheet
            >>> client.save_video(video_id, "sprites.jpg", variant="spritesheet")
        """
        content = self.get_content(video_id, variant)
        
        with open(filename, 'wb') as f:
            f.write(content)
        
        print(f"Video saved to: {filename}")
        return filename
    
    def download(self, video_id: str, output_dir: str = ".") -> str:
        """
        Download a video to a specific directory with automatic naming.
        
        Downloads the full video file to the specified directory, automatically
        naming it with the video ID and .mp4 extension. This is a convenience
        method that combines save_video() with automatic path construction.
        
        Args:
            video_id (str): The identifier of the video to download.
            output_dir (str): Directory where the video should be saved.
                Defaults to current directory. Directory is created if it
                doesn't exist.
        
        Returns:
            str: The full path to the downloaded video file.
        
        Raises:
            requests.exceptions.HTTPError: If video not found or API error.
            requests.exceptions.RequestException: If network error occurs.
            OSError: If directory cannot be created or file cannot be written.
        
        Example:
            >>> client = SoraAPIClient()
            >>> 
            >>> # Download to current directory
            >>> path = client.download("video_abc123")
            >>> print(f"Downloaded to: {path}")  # ./video_abc123.mp4
            >>> 
            >>> # Download to specific directory
            >>> path = client.download("video_abc123", output_dir="downloads")
            >>> print(f"Downloaded to: {path}")  # downloads/video_abc123.mp4
            >>> 
            >>> # Download to organized structure
            >>> video = client.retrieve("video_abc123")
            >>> date = video['created_at'][:10]  # YYYY-MM-DD
            >>> path = client.download("video_abc123", output_dir=f"videos/{date}")
        """
        os.makedirs(output_dir, exist_ok=True)
        video_file = os.path.join(output_dir, f"{video_id}.mp4")
        return self.save_video(video_id, video_file, variant='video')
    
    def generate_thumbnail(self, video_id: str, thumbnail_file: str) -> str:
        """
        Download a thumbnail image from the API.
        
        Retrieves the thumbnail variant for a video and saves it to a file.
        Thumbnails are provided by the API as WebP images and don't require
        any video processing.
        
        Args:
            video_id (str): The identifier of the video.
            thumbnail_file (str): Local path where the thumbnail should be saved.
                Recommend using .webp extension for proper file type.
        
        Returns:
            str: The path to the saved thumbnail file.
        
        Raises:
            requests.exceptions.HTTPError: If video not found or API error.
            requests.exceptions.RequestException: If network error occurs.
            OSError: If file cannot be written.
        
        Example:
            >>> client = SoraAPIClient()
            >>> 
            >>> # Generate thumbnail
            >>> thumb_path = client.generate_thumbnail(
            ...     video_id="video_abc123",
            ...     thumbnail_file="thumbnails/video_abc123.webp"
            ... )
            >>> print(f"Thumbnail saved to: {thumb_path}")
            >>> 
            >>> # Generate thumbnails for all videos
            >>> videos = client.list()
            >>> for video in videos['data']:
            ...     if video['status'] == 'completed':
            ...         client.generate_thumbnail(
            ...             video['id'],
            ...             f"thumbs/{video['id']}.webp"
            ...         )
        """
        return self.save_video(video_id, thumbnail_file, variant='thumbnail')
    
    def test_connection(self) -> bool:
        """
        Test the API connection and authentication.
        
        Makes a simple API request to verify that the API key is valid and the
        service is accessible. Useful for debugging connection issues or validating
        configuration before starting work.
        
        Returns:
            bool: True if the connection test succeeds, False if it fails.
        
        Note:
            This method prints error messages to stdout if the connection fails.
        
        Example:
            >>> client = SoraAPIClient()
            >>> 
            >>> # Test before starting work
            >>> if not client.test_connection():
            ...     print("Please check your API key and internet connection")
            ...     exit(1)
            >>> 
            >>> # Continue with video operations
            >>> result = client.create(prompt="Test video")
        """
        try:
            # Using a minimal request to test connection
            url = f"{self.base_url}/models"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            print("API connection successful!")
            return True
        except requests.exceptions.RequestException as e:
            print(f"API connection failed: {e}")
            return False


def main():
    """
    Command-line interface for the Sora API client.
    
    Provides a full-featured CLI for interacting with the Sora 2 API including:
    - create: Generate new videos from prompts or images
    - remix: Create variations of existing videos
    - list: Browse your video library
    - retrieve: Get detailed info about specific videos
    - delete: Remove videos from your library
    - download: Save videos, thumbnails, and spritesheets
    - wait: Monitor video generation progress
    
    Run with --help for detailed usage information.
    
    Example:
        $ python sora_api.py create --prompt "A sunset over the ocean" --wait
        $ python sora_api.py list --limit 10
        $ python sora_api.py download --video-id video_abc123 --all
    """
    
    parser = argparse.ArgumentParser(
        description='Sora 2 API Client - Create, manage, and download AI-generated videos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a video from a prompt
  python sora_api.py create --prompt "A sunset over the ocean" --wait

  # Create a video from a JSON file
  python sora_api.py create --file create_params.json --wait

  # Remix an existing video
  python sora_api.py remix --video-id video_123 --prompt "Make it sunrise" --wait

  # List all videos
  python sora_api.py list --limit 20

  # Retrieve video information
  python sora_api.py retrieve --video-id video_123

  # Download a video
  python sora_api.py download --video-id video_123 --output my_video.mp4

  # Delete a video
  python sora_api.py delete --video-id video_123
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # CREATE command
    create_parser = subparsers.add_parser('create', help='Create a new video')
    create_parser.add_argument('--file', type=str, help='JSON file with creation parameters')
    create_parser.add_argument('--prompt', type=str, help='Video generation prompt')
    create_parser.add_argument('--model', type=str, default='sora-2', help='Model to use (default: sora-2)')
    create_parser.add_argument('--seconds', type=str, help='Video duration in seconds')
    create_parser.add_argument('--size', type=str, help='Video resolution (e.g., 1920x1080)')
    create_parser.add_argument('--wait', action='store_true', help='Wait for video completion')
    create_parser.add_argument('--no-save', action='store_true', help='Don\'t save video info to JSON')
    
    # REMIX command
    remix_parser = subparsers.add_parser('remix', help='Remix an existing video')
    remix_parser.add_argument('--video-id', type=str, required=True, help='ID of the video to remix')
    remix_parser.add_argument('--prompt', type=str, required=True, help='Remix prompt')
    remix_parser.add_argument('--model', type=str, default='sora-2', help='Model to use (default: sora-2)')
    remix_parser.add_argument('--seconds', type=str, help='Video duration in seconds')
    remix_parser.add_argument('--size', type=str, help='Video resolution (e.g., 1920x1080)')
    remix_parser.add_argument('--wait', action='store_true', help='Wait for video completion')
    remix_parser.add_argument('--no-save', action='store_true', help='Don\'t save video info to JSON')
    
    # LIST command
    list_parser = subparsers.add_parser('list', help='List videos')
    list_parser.add_argument('--limit', type=int, default=20, help='Number of videos to return (default: 20)')
    list_parser.add_argument('--order', type=str, choices=['asc', 'desc'], default='desc', help='Sort order (default: desc)')
    list_parser.add_argument('--after', type=str, help='Cursor for pagination (after)')
    list_parser.add_argument('--before', type=str, help='Cursor for pagination (before)')
    
    # RETRIEVE command
    retrieve_parser = subparsers.add_parser('retrieve', help='Retrieve video information')
    retrieve_parser.add_argument('--video-id', type=str, required=True, help='ID of the video to retrieve')
    
    # DELETE command
    delete_parser = subparsers.add_parser('delete', help='Delete a video')
    delete_parser.add_argument('--video-id', type=str, required=True, help='ID of the video to delete')
    delete_parser.add_argument('--yes', action='store_true', help='Skip confirmation prompt')
    
    # DOWNLOAD command
    download_parser = subparsers.add_parser('download', help='Download video content')
    download_parser.add_argument('--video-id', type=str, required=True, help='ID of the video to download')
    download_parser.add_argument('--output', type=str, help='Output filename (default: <video_id>.mp4)')
    download_parser.add_argument('--variant', type=str, help='Video variant to download (video, thumbnail, spritesheet)')
    download_parser.add_argument('--all', action='store_true', help='Download video, thumbnail, and spritesheet')
    
    # WAIT command
    wait_parser = subparsers.add_parser('wait', help='Wait for a video to complete')
    wait_parser.add_argument('--video-id', type=str, required=True, help='ID of the video to wait for')
    wait_parser.add_argument('--interval', type=int, default=3, help='Polling interval in seconds (default: 3)')
    wait_parser.add_argument('--timeout', type=int, default=600, help='Maximum wait time in seconds (default: 600)')
    wait_parser.add_argument('--no-save', action='store_true', help='Don\'t save video info to JSON when complete')
    
    args = parser.parse_args()
    
    # Show help if no command provided
    if not args.command:
        parser.print_help()
        return
    
    try:
        # Initialize the client
        client = SoraAPIClient()
        
        # Execute the requested command
        if args.command == 'create':
            # Load parameters from file if provided
            if args.file:
                with open(args.file, 'r') as f:
                    params = json.load(f)
                wait = params.pop('wait', args.wait)
                no_save = params.pop('no_save', args.no_save)
            else:
                # Build parameters from arguments
                if not args.prompt:
                    print("Error: --prompt is required when not using --file")
                    return
                
                params = {
                    'prompt': args.prompt,
                    'model': args.model
                }
                if args.seconds:
                    params['seconds'] = args.seconds
                if args.size:
                    params['size'] = args.size
                
                wait = args.wait
                no_save = args.no_save
            
            # Store original params for saving
            creation_args = params.copy()
            params['wait_for_completion'] = wait
            
            print("Creating video...")
            result = client.create(**params)
            
            print("\nVideo creation initiated!")
            print(f"Video ID: {result.get('id')}")
            print(f"Status: {result.get('status')}")
            
            if result.get('status') == 'completed' and not no_save:
                client.save_video_info(result, creation_args)
            
            print(json.dumps(result, indent=2))
        
        elif args.command == 'remix':
            params = {
                'video_id': args.video_id,
                'prompt': args.prompt,
                'model': args.model
            }
            if args.seconds:
                params['seconds'] = args.seconds
            if args.size:
                params['size'] = args.size
            
            creation_args = params.copy()
            params['wait_for_completion'] = args.wait
            
            print("Remixing video...")
            result = client.remix(**params)
            
            print("\nVideo remix initiated!")
            print(f"Video ID: {result.get('id')}")
            print(f"Status: {result.get('status')}")
            
            if result.get('status') == 'completed' and not args.no_save:
                client.save_video_info(result, creation_args)
            
            print(json.dumps(result, indent=2))
        
        elif args.command == 'list':
            params = {
                'limit': args.limit,
                'order': args.order
            }
            if args.after:
                params['after'] = args.after
            if args.before:
                params['before'] = args.before
            
            result = client.list(**params)
            
            videos = result.get('data', [])
            print(f"\nFound {len(videos)} video(s):")
            print("-" * 80)
            
            for video in videos:
                print(f"ID: {video.get('id')}")
                print(f"  Status: {video.get('status')}")
                print(f"  Created: {video.get('created_at', 'N/A')}")
                if video.get('prompt'):
                    prompt = video['prompt'][:60] + "..." if len(video.get('prompt', '')) > 60 else video.get('prompt')
                    print(f"  Prompt: {prompt}")
                print()
            
            print(json.dumps(result, indent=2))
        
        elif args.command == 'retrieve':
            result = client.retrieve(args.video_id)
            
            print(f"\nVideo Information:")
            print(f"ID: {result.get('id')}")
            print(f"Status: {result.get('status')}")
            print(f"Progress: {result.get('progress', 0)}%")
            print(f"Created: {result.get('created_at', 'N/A')}")
            
            print(json.dumps(result, indent=2))
        
        elif args.command == 'delete':
            if not args.yes:
                confirm = input(f"Are you sure you want to delete video '{args.video_id}'? (yes/no): ")
                if confirm.lower() not in ['yes', 'y']:
                    print("Deletion cancelled.")
                    return
            
            result = client.delete(args.video_id)
            print(json.dumps(result, indent=2))
        
        elif args.command == 'download':
            if args.all:
                # Download all variants: video, thumbnail, and spritesheet
                base_name = args.output.rsplit('.', 1)[0] if args.output else args.video_id
                
                print("Downloading all variants...")
                print("-" * 60)
                
                # Download video
                video_file = f"{base_name}.mp4"
                client.save_video(args.video_id, video_file, variant='video')
                print(f"✓ Video saved to: {video_file}")
                
                # Download thumbnail
                thumbnail_file = f"{base_name}_thumbnail.webp"
                client.save_video(args.video_id, thumbnail_file, variant='thumbnail')
                print(f"✓ Thumbnail saved to: {thumbnail_file}")
                
                # Download spritesheet
                spritesheet_file = f"{base_name}_spritesheet.jpg"
                client.save_video(args.video_id, spritesheet_file, variant='spritesheet')
                print(f"✓ Spritesheet saved to: {spritesheet_file}")
                
                print("-" * 60)
                print(f"\nAll files downloaded successfully!")
            else:
                # Download single variant
                output = args.output or f"{args.video_id}.mp4"
                client.save_video(args.video_id, output, args.variant)
                print(f"\nVideo saved to: {output}")
        
        elif args.command == 'wait':
            print(f"Waiting for video '{args.video_id}' to complete...")
            
            try:
                result = client.wait_for_completion(
                    args.video_id,
                    poll_interval=args.interval,
                    max_wait_time=args.timeout,
                    show_progress=True
                )
                
                if not args.no_save:
                    client.save_video_info(result)
                
                print(json.dumps(result, indent=2))
                
            except TimeoutError as e:
                print(f"\nError: {e}")
                sys.exit(1)
            except Exception as e:
                print(f"\nError: {e}")
                sys.exit(1)
    
    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("\nPlease run 'setup_env.bat' to set up your API key.")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"File Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
