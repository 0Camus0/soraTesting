# Sora 2 API Client

A Python client for interacting with the OpenAI Sora 2 video generation API.

## Features

- 🔐 Secure API key management using environment variables
- 🎬 Easy video generation with text prompts
- ✅ Connection testing
- 🛠️ Modular and extensible design

## Setup

### Prerequisites

- Python 3.7 or higher
- OpenAI API key with Sora 2 access

### Installation

1. Clone or navigate to the repository:
```bash
cd c:\dev\Sora
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

### API Key Configuration

**Important**: Your API key is stored in `test.txt` and should NEVER be committed to the repository.

To set up your environment with the API key:

1. Make sure `test.txt` contains your OpenAI API key
2. Run the setup batch file:
```bash
setup_env.bat
```

This will:
- Extract the API key from `test.txt`
- Set it as the `OPENAI_API_KEY` environment variable
- Open a PowerShell session with the variable configured

## Usage

### Basic Example

After running `setup_env.bat`, you can use the Sora API client:

```python
from sora_api import SoraAPIClient

# Initialize the client (automatically reads from environment variable)
client = SoraAPIClient()

# Generate a video
result = client.generate_video(
    prompt="A serene sunset over a calm ocean, with waves gently lapping at the shore"
)

print(result)
```

### Running the Example Script

In the PowerShell session opened by `setup_env.bat`, run:

```bash
python sora_api.py
```

### Using the Client in Your Own Scripts

```python
from sora_api import SoraAPIClient

# Initialize client
client = SoraAPIClient()

# Test connection
if client.test_connection():
    # Generate video with custom parameters
    result = client.generate_video(
        prompt="Your video prompt here",
        duration=5,           # Optional: video duration in seconds
        resolution="1080p",   # Optional: video resolution
        aspect_ratio="16:9"   # Optional: aspect ratio
    )
```

## Project Structure

```
c:\dev\Sora\
├── .git/               # Git repository
├── .gitignore          # Git ignore file (includes test.txt)
├── test.txt            # API key storage (NOT in git)
├── setup_env.bat       # Environment setup script
├── sora_api.py         # Main API client
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## Security Notes

⚠️ **Important Security Information**:

- `test.txt` is excluded from git via `.gitignore`
- Never commit your API key to version control
- The `setup_env.bat` file is also excluded from git (it contains key extraction logic)
- Always use environment variables for API keys in production

## API Reference

### SoraAPIClient Class

#### `__init__(api_key=None)`
Initialize the client with an optional API key. If not provided, reads from `OPENAI_API_KEY` environment variable.

#### `generate_video(prompt, model="sora-2", **kwargs)`
Generate a video using the Sora 2 API.

**Parameters:**
- `prompt` (str): Text description of the video to generate
- `model` (str): Model name (default: "sora-2")
- `**kwargs`: Additional API parameters

**Returns:**
- dict: API response with video generation information

#### `test_connection()`
Test the API connection.

**Returns:**
- bool: True if connection is successful

## Troubleshooting

### "API key not found" error
- Make sure you've run `setup_env.bat` before running Python scripts
- Verify that `test.txt` exists and contains your API key

### "API connection failed" error
- Check that your API key is valid
- Verify you have access to the Sora 2 API
- Check your internet connection

## Note About the API Endpoint

The example in `test.txt` uses `/v1/responses` endpoint with `gpt-5-nano` model, which appears to be a placeholder. The actual Sora 2 API client in this project uses the proper video generation endpoint (`/v1/video/generations`). You may need to adjust the endpoint and parameters based on the actual Sora 2 API documentation when it becomes available.

## License

This is a personal project. Use at your own discretion.
