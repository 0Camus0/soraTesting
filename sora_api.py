#!/usr/bin/env python3
"""
Sora 2 API Client
A Python client for calling the OpenAI Sora 2 API
"""

import os
import sys
import requests
import json


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
    
    def create(self, prompt, model="sora-2", input_reference=None, seconds=None, size=None):
        """
        Create a video using the Sora 2 API
        
        Args:
            prompt (str): Text prompt that describes the video to generate
            model (str): The video generation model to use. Defaults to "sora-2"
            input_reference (file, optional): Optional image reference that guides generation
            seconds (str, optional): Clip duration in seconds. Defaults to 4 seconds
            size (str, optional): Output resolution formatted as width x height. Defaults to 720x1280
        
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
            return result
            
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            print(f"Response: {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
            raise
    
    def remix(self, video_id, prompt):
        """
        Create a video remix based on an existing video
        
        Args:
            video_id (str): The identifier of the completed video to remix
            prompt (str): Updated text prompt that directs the remix generation
        
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
            print(f"Retrieving video '{video_id}'...")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            print("Video retrieved successfully!")
            return result
            
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            print(f"Response: {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
            raise
    
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
    """Example usage of the Sora API client"""
    
    try:
        # Initialize the client
        client = SoraAPIClient()
        
        # Test connection
        print("Testing API connection...")
        if not client.test_connection():
            print("Failed to connect to API. Please check your API key.")
            return
        
        print("\n" + "="*50)
        print("Sora 2 API Client - Examples")
        print("="*50 + "\n")
        
        # Example 1: Create a video
        print("Example 1: Creating a video")
        print("-" * 50)
        prompt = "A serene sunset over a calm ocean, with waves gently lapping at the shore"
        
        result = client.create(
            prompt=prompt,
            model="sora-2",  # Default model
            seconds="5",     # 5 second clip
            size="1920x1080" # Full HD resolution
        )
        
        print("\nCreate Response:")
        print(json.dumps(result, indent=2))
        
        # Save the video ID for later examples
        video_id = result.get('id', 'video_123')
        
        # Example 2: List videos
        print("\n\nExample 2: Listing videos")
        print("-" * 50)
        
        videos = client.list(limit=10, order="desc")
        print(f"\nFound {len(videos.get('data', []))} videos")
        
        # Example 3: Retrieve a specific video
        print("\n\nExample 3: Retrieving a video")
        print("-" * 50)
        
        video_info = client.retrieve(video_id)
        print("\nVideo Info:")
        print(json.dumps(video_info, indent=2))
        
        # Example 4: Remix a video (commented out - requires completed video)
        # print("\n\nExample 4: Remixing a video")
        # print("-" * 50)
        # 
        # remix_result = client.remix(
        #     video_id=video_id,
        #     prompt="The same ocean scene, but now at sunrise with pink and orange hues"
        # )
        # print("\nRemix Response:")
        # print(json.dumps(remix_result, indent=2))
        
        # Example 5: Download video content (commented out - requires completed video)
        # print("\n\nExample 5: Downloading video content")
        # print("-" * 50)
        # 
        # client.save_video(video_id, "my_video.mp4")
        
        # Example 6: Delete a video (commented out to prevent accidental deletion)
        # print("\n\nExample 6: Deleting a video")
        # print("-" * 50)
        # 
        # delete_result = client.delete(video_id)
        # print("\nDelete Response:")
        # print(json.dumps(delete_result, indent=2))
        
    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("\nPlease run 'setup_env.bat' to set up your API key.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
