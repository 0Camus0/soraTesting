# Sora 2 Web Interface

A modern web-based GUI for the Sora 2 API client.

## Features

✨ **Create Tab:**
- Text area for video prompts
- Model selection (sora-2, sora-2-pro)
- Duration selection (4s, 8s, 12s)
- Resolution options (Portrait, Landscape, Square, Wide)
- Real-time progress tracking with visual progress bar
- Automatic download after video completion

📚 **Gallery Tab:**
- Grid view of all generated videos
- Thumbnail previews
- Video metadata display (model, duration)
- Click to play videos in modal
- Download individual videos
- Delete videos

## Installation

1. Install the additional dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure your `.env` file is configured with your API key:
```bash
OPENAI_API_KEY=sk-proj-your-api-key-here
```

## Running the Web Interface

Start the Flask server:
```bash
python web_app.py
```

The web interface will be available at:
**http://localhost:5000**

## Usage

### Creating a Video

1. Go to the **Create Video** tab
2. Enter your video prompt
3. Select model, duration, and resolution
4. Click **Generate Video**
5. Watch the progress bar as your video is created
6. Video automatically downloads when complete
7. View it in the **Gallery** tab

### Gallery Features

- **View:** Click any thumbnail to play the video in a modal
- **Download:** Click the Download button to save the video locally
- **Delete:** Remove videos you no longer need

## API Endpoints

The Flask backend exposes the following endpoints:

- `GET /` - Serve the main web interface
- `POST /api/create` - Create a new video (returns job_id)
- `GET /api/status/<job_id>` - Check job status and progress
- `GET /api/gallery` - Get list of all generated videos
- `GET /videos/<filename>` - Serve video files
- `DELETE /api/delete/<video_id>` - Delete a video

## Architecture

```
┌─────────────────┐
│   Frontend      │
│  (HTML/CSS/JS)  │
└────────┬────────┘
         │
    HTTP Requests
         │
┌────────▼────────┐
│  Flask Server   │
│   (web_app.py)  │
└────────┬────────┘
         │
    Python Imports
         │
┌────────▼────────┐
│  Sora API       │
│ (sora_api.py)   │
└────────┬────────┘
         │
   HTTPS Requests
         │
┌────────▼────────┐
│  OpenAI Sora    │
│      API        │
└─────────────────┘
```

## Features in Detail

### Progress Tracking
- Real-time status updates every 2 seconds
- Visual progress bar (0-100%)
- Status messages for each phase:
  - Creating video
  - Waiting for completion
  - Downloading files
  - Complete

### Automatic Download
- Video file (.mp4)
- Thumbnail (.webp)
- Spritesheet (.jpg)
- Metadata (.json)

### Gallery
- Responsive grid layout
- Thumbnail previews with fallback
- Video metadata display
- Modal video player
- Download and delete actions

## Troubleshooting

**Port 5000 already in use:**
```bash
# Edit web_app.py and change the port number:
app.run(debug=True, host='0.0.0.0', port=8080)
```

**API key not found:**
Make sure your `.env` file exists with:
```
OPENAI_API_KEY=your-key-here
```

**Videos not showing in gallery:**
Videos are stored in the `videos/` directory. Make sure:
- The directory exists
- It's not empty
- You have read permissions

## Development

To run in development mode with auto-reload:
```bash
python web_app.py
```

The Flask debug mode is enabled by default, so changes to the Python code will automatically reload the server.

## Browser Compatibility

Tested and working on:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Notes

- Videos are stored locally in the `videos/` directory
- The server runs on `0.0.0.0` (accessible from network)
- Progress updates poll every 2 seconds
- Maximum wait time for video generation: 600 seconds (10 minutes)
