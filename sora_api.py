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
    
    def generate_video(self, prompt, model="sora-2", **kwargs):
        """
        Generate a video using Sora 2 API
        
        Args:
            prompt (str): The text prompt describing the video to generate
            model (str): The model to use (default: "sora-2")
            **kwargs: Additional parameters to pass to the API
                     (e.g., duration, resolution, aspect_ratio, etc.)
        
        Returns:
            dict: API response containing the generated video information
        """
        url = f"{self.base_url}/video/generations"
        
        payload = {
            "model": model,
            "prompt": prompt,
            **kwargs
        }
        
        try:
            print(f"Generating video with prompt: '{prompt}'...")
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            print("Video generation successful!")
            return result
            
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            print(f"Response: {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
            raise
    
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
        print("Sora 2 API Client - Example")
        print("="*50 + "\n")
        
        # Example: Generate a video
        prompt = "A serene sunset over a calm ocean, with waves gently lapping at the shore"
        
        print(f"Prompt: {prompt}\n")
        
        # Call the API
        result = client.generate_video(
            prompt=prompt,
            # Add additional parameters as needed:
            # duration=5,  # seconds
            # resolution="1080p",
            # aspect_ratio="16:9"
        )
        
        # Display the result
        print("\nAPI Response:")
        print(json.dumps(result, indent=2))
        
    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("\nPlease run 'setup_env.bat' to set up your API key.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
