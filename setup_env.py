#!/usr/bin/env python3
"""
Setup Environment Script
Extracts API key from test.txt and sets it as an environment variable
"""

import os
import re
import sys


def extract_api_key(file_path='test.txt'):
    """
    Extract OpenAI API key from test.txt file
    
    Args:
        file_path (str): Path to the file containing the API key
        
    Returns:
        str: The extracted API key, or None if not found
    """
    if not os.path.exists(file_path):
        print(f"ERROR: {file_path} not found!")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for Bearer token pattern (sk-proj-... or sk-...)
        # Match the full API key after "Bearer "
        match = re.search(r'Bearer\s+(sk-[a-zA-Z0-9_-]+)', content)
        
        if match:
            api_key = match.group(1)
            print(f"✓ API key found: {api_key[:15]}...{api_key[-4:]}")
            return api_key
        else:
            print("ERROR: Could not find API key in the expected format (Bearer sk-...)")
            return None
            
    except Exception as e:
        print(f"ERROR reading file: {e}")
        return None


def main():
    """Main function to extract and set the API key"""
    print("=" * 60)
    print("OpenAI API Key Setup")
    print("=" * 60)
    
    # Extract the API key
    api_key = extract_api_key()
    
    if not api_key:
        print("\n❌ Failed to extract API key")
        sys.exit(1)
    
    # Set the environment variable for the current process
    os.environ['OPENAI_API_KEY'] = api_key
    
    print(f"\n✓ Environment variable OPENAI_API_KEY set successfully!")
    print("\nYou can now run your Sora API commands:")
    print("  python sora_api.py create --prompt \"Your prompt here\" --wait")
    print("\nNote: This sets the variable for child processes only.")
    print("      To persist across sessions, add to your system environment variables.")
    
    # Try to create/update .env file
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(f"OPENAI_API_KEY={api_key}\n")
        print(f"\n✓ Created .env file with API key")
        print("  (This file is in .gitignore and won't be committed)")
    except Exception as e:
        print(f"\n⚠ Could not create .env file: {e}")
    
    print("\n" + "=" * 60)
    
    return api_key


if __name__ == '__main__':
    main()
