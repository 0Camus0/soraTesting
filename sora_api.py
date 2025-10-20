#!/usr/bin/env python3
"""
Sora 2 API Client
A Python client for calling the OpenAI Sora 2 API
"""

import os
import sys
import requests
import json
import time
import argparse
from datetime import datetime


class SoraAPIClient:
    """Client for interacting with the Sora 2 API"""
    
    def __init__(self, api_key=None):
        """
        Initialize the Sora API client
        
        Args:
            api_key (str, optional): OpenAI API key. If not provided, 
                                    reads from OPENAI_API_KEY environment variable.
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "API key not found. Please set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def create(self, prompt, model="sora-2", input_reference=None, seconds=None, size=None, wait_for_completion=False):
        """
        Create a video using the Sora 2 API
        
        Args:
            prompt (str): Text prompt that describes the video to generate
            model (str): The video generation model to use. Defaults to "sora-2"
            input_reference (file, optional): Optional image reference that guides generation
            seconds (str, optional): Clip duration in seconds. Defaults to 4 seconds
            size (str, optional): Output resolution formatted as width x height. Defaults to 720x1280
            wait_for_completion (bool): If True, poll until video is complete. Defaults to False
        
        Returns:
            dict: The newly created video job
        """
        url = f"{self.base_url}/videos"
        
        payload = {
            "prompt": prompt,
            "model": model
        }
        
        if input_reference is not None:
            payload["input_reference"] = input_reference
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
    
    def remix(self, video_id, prompt, wait_for_completion=False):
        """
        Create a video remix based on an existing video
        
        Args:
            video_id (str): The identifier of the completed video to remix
            prompt (str): Updated text prompt that directs the remix generation
            wait_for_completion (bool): If True, poll until video is complete. Defaults to False
        
        Returns:
            dict: The newly created remix video job
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
    
    def list(self, after=None, limit=None, order=None):
        """
        List videos in the organization
        
        Args:
            after (str, optional): Identifier for the last item from the previous pagination request
            limit (int, optional): Number of items to retrieve
            order (str, optional): Sort order by timestamp. Use 'asc' or 'desc'
        
        Returns:
            dict: A paginated list of video jobs
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
    
    def retrieve(self, video_id):
        """
        Retrieve information about a specific video
        
        Args:
            video_id (str): The identifier of the video to retrieve
        
        Returns:
            dict: The video job matching the provided identifier
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
    
    def wait_for_completion(self, video_id, poll_interval=3, max_wait_time=600, show_progress=True):
        """
        Wait for a video job to complete by polling its status
        
        Args:
            video_id (str): The identifier of the video to monitor
            poll_interval (int): Seconds to wait between status checks. Defaults to 3
            max_wait_time (int): Maximum seconds to wait before timeout. Defaults to 600 (10 minutes)
            show_progress (bool): Display progress updates. Defaults to True
        
        Returns:
            dict: The completed video job
            
        Raises:
            TimeoutError: If video doesn't complete within max_wait_time
            Exception: If video job fails
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
    
    def _create_progress_bar(self, progress, width=30):
        """
        Create a text-based progress bar
        
        Args:
            progress (int): Progress percentage (0-100)
            width (int): Width of the progress bar in characters
        
        Returns:
            str: Progress bar string
        """
        filled = int(width * progress / 100)
        bar = '█' * filled + '░' * (width - filled)
        return f"[{bar}]"
    
    def save_video_info(self, video_data, creation_args=None, output_dir="videos"):
        """
        Save video information to a JSON file
        
        Args:
            video_data (dict): The video data returned by the API
            creation_args (dict, optional): The arguments used to create the video
            output_dir (str): Directory to save the JSON file
        
        Returns:
            str: Path to the saved JSON file
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
    
    def delete(self, video_id):
        """
        Delete a video
        
        Args:
            video_id (str): The identifier of the video to delete
        
        Returns:
            dict: Deletion confirmation response
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
    
    def get_content(self, video_id, variant=None):
        """
        Download video content
        
        Args:
            video_id (str): The identifier of the video whose media to download
            variant (str, optional): The variant of the video to download
        
        Returns:
            bytes: The video file content
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
    
    def save_video(self, video_id, filename, variant=None):
        """
        Download and save video content to a file
        
        Args:
            video_id (str): The identifier of the video to download
            filename (str): The filename to save the video as
            variant (str, optional): The variant of the video to download
        
        Returns:
            str: The path to the saved file
        """
        content = self.get_content(video_id, variant)
        
        with open(filename, 'wb') as f:
            f.write(content)
        
        print(f"Video saved to: {filename}")
        return filename
    
    def test_connection(self):
        """
        Test the API connection with a simple request
        
        Returns:
            bool: True if connection is successful
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
    """Command-line interface for the Sora API client"""
    
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
    download_parser.add_argument('--variant', type=str, help='Video variant to download')
    
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
