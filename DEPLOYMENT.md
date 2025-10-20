# Sora 2 API - Production Deployment

Production-ready Python client and web interface for OpenAI's Sora 2 video generation API.

## Project Structure

```
Sora/
├── src/                        # Source code (production)
│   ├── api/                    # API client package
│   │   ├── __init__.py
│   │   └── sora_api.py         # Core API client with full documentation
│   └── app/                    # Web application package
│       ├── __init__.py
│       ├── web_app.py          # Flask backend with documented endpoints
│       └── templates/
│           └── index.html      # Frontend interface
│
├── videos/                     # Video storage (local downloads)
│   └── {video_id}/
│       ├── {video_id}.mp4      # Video file
│       ├── thumbnail.webp      # Thumbnail image
│       ├── spritesheet.jpg     # Spritesheet preview
│       └── metadata.json       # Video metadata
│
├── temp/                       # Temporary uploads (auto-cleanup)
├── requirements.txt            # Python dependencies
├── .env                        # API key configuration (not in git)
└── DEPLOYMENT.md              # This file

Legacy files (for backward compatibility):
├── sora_api.py                 # Original API client
├── web_app.py                  # Original web app
└── templates/                  # Original templates
```

## Installation

### Prerequisites

- Python 3.8 or higher
- OpenAI API key with Sora 2 access

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/0Camus0/soraTesting.git
   cd soraTesting
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API key**
   
   Create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=sk-proj-your-api-key-here
   ```
   
   Or set environment variable:
   ```bash
   # Windows PowerShell
   $env:OPENAI_API_KEY="sk-proj-your-api-key-here"
   
   # Linux/Mac
   export OPENAI_API_KEY="sk-proj-your-api-key-here"
   ```

## Usage

### Web Interface

1. **Start the server**
   ```bash
   python src/app/web_app.py
   ```

2. **Open browser**
   ```
   http://localhost:5000
   ```

3. **Features available**
   - **Create Tab**: Generate videos from text prompts or image references
   - **Remix Tab**: Transform existing videos with new prompts
   - **Gallery Tab**: Browse and manage locally downloaded videos
   - **Video List Tab**: View and download videos from API

### CLI Usage

Use the API client directly from command line:

```bash
# Create a video
python src/api/sora_api.py create --prompt "A sunset over the ocean" --wait

# Remix a video
python src/api/sora_api.py remix --video-id video_abc123 --prompt "Make it sunrise" --wait

# List all videos
python src/api/sora_api.py list --limit 20

# Download a video
python src/api/sora_api.py download --video-id video_abc123 --all

# Get help
python src/api/sora_api.py --help
python src/api/sora_api.py create --help
```

### Python API

```python
from src.api.sora_api import SoraAPIClient

# Initialize client
client = SoraAPIClient()

# Create a video
video = client.create(
    prompt="A golden retriever running through a field",
    seconds="5",
    size="1920x1080",
    wait_for_completion=True
)

# Download the video
client.download(video['id'], output_dir="my_videos")

# Create a remix
remix = client.remix(
    video_id=video['id'],
    prompt="Transform into a watercolor painting",
    wait_for_completion=True
)
```

## API Documentation

### SoraAPIClient Methods

All methods in `src/api/sora_api.py` are fully documented with:
- Detailed parameter descriptions
- Return value specifications
- Exception handling information
- Usage examples

Key methods:
- `create()` - Generate new videos
- `remix()` - Create video variations
- `list()` - Browse video library
- `retrieve()` - Get video details
- `wait_for_completion()` - Poll until complete
- `download()` - Download to local storage
- `delete()` - Remove from API

See inline documentation in `src/api/sora_api.py` for complete API reference.

### Web Endpoints

All Flask routes in `src/app/web_app.py` are fully documented with:
- Request/response formats
- Status codes
- Example usage
- Side effects

Key endpoints:
- `POST /api/create` - Create video (async)
- `POST /api/remix` - Remix video (async)
- `GET /api/status/<job_id>` - Poll job progress
- `GET /api/gallery` - List local videos
- `GET /api/videos` - List API videos
- `GET /api/download/<video_id>` - Download from API
- `DELETE /api/delete/<video_id>` - Delete from API
- `DELETE /api/delete-local/<video_id>` - Delete local files

## Deployment

### Production Considerations

1. **Security**
   - Never commit `.env` file to git
   - Use environment variables for API keys in production
   - Consider adding authentication for web interface
   - Enable HTTPS for production deployments

2. **Performance**
   - Use production WSGI server (gunicorn/waitress)
   - Configure proper logging
   - Set up monitoring for job status
   - Implement cleanup for old videos

3. **Storage**
   - Monitor disk space in `videos/` directory
   - Implement video retention policies
   - Consider cloud storage for large libraries

### Example Production Setup (Linux)

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 src.app.web_app:app

# Or with waitress (Windows compatible)
pip install waitress
waitress-serve --host=0.0.0.0 --port=8000 src.app.web_app:app
```

### Docker Deployment (Optional)

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY .env .env

EXPOSE 5000
CMD ["python", "src/app/web_app.py"]
```

Build and run:
```bash
docker build -t sora-api-app .
docker run -p 5000:5000 --env-file .env sora-api-app
```

## Testing

```bash
# Test API connection
python -c "from src.api.sora_api import SoraAPIClient; SoraAPIClient().test_connection()"

# Create a test video
python src/api/sora_api.py create --prompt "Test video" --seconds 3

# Check web server
curl http://localhost:5000/api/videos
```

## Troubleshooting

### API Key Issues
- Verify `.env` file exists and contains correct key
- Check environment variable: `echo $OPENAI_API_KEY`
- Ensure API key has Sora 2 access

### Import Errors
- Verify you're in the project root directory
- Check Python path includes project root
- Ensure all `__init__.py` files exist

### Port Already in Use
- Change port in `web_app.py` (default: 5000)
- Or kill existing process on port 5000

### Video Download Fails
- Verify video status is 'completed'
- Check network connectivity
- Ensure sufficient disk space

## Migration from Legacy Code

If upgrading from the legacy structure:

1. **Update imports**
   ```python
   # Old
   from sora_api import SoraAPIClient
   
   # New
   from src.api.sora_api import SoraAPIClient
   ```

2. **Run from project root**
   ```bash
   # Old
   python web_app.py
   
   # New
   python src/app/web_app.py
   ```

3. **Video storage remains compatible**
   - Existing videos in `videos/` directory continue to work
   - No migration needed for video files

## Contributing

This is a production deployment structure. For changes:

1. Modify files in `src/` directory
2. Update documentation in docstrings
3. Test thoroughly before deployment
4. Update version in `src/__init__.py`

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
- GitHub: https://github.com/0Camus0/soraTesting
- Documentation: See inline docstrings in source files
