# Sora API CLI Usage Guide

## Overview

The Sora API client now includes a comprehensive command-line interface (CLI) that allows you to interact with all API endpoints directly from the terminal.

## Prerequisites

Before using the CLI, make sure to set up your API key:

```bash
setup_env.bat
```

## Available Commands

### 1. Create a Video

#### Basic Creation
```bash
python sora_api.py create --prompt "A sunset over the ocean" --wait
```

#### With Full Parameters
```bash
python sora_api.py create \
  --prompt "A majestic eagle soaring through clouds" \
  --model "sora-2" \
  --seconds "10" \
  --size "1920x1080" \
  --wait
```

#### Using a JSON File
```bash
python sora_api.py create --file create_params.json --wait
```

The `create_params.json` template includes:
```json
{
  "prompt": "Your video description here",
  "model": "sora-2",
  "seconds": "5",
  "size": "1920x1080",
  "wait": true,
  "no_save": false
}
```

**Options:**
- `--file FILE` - Load parameters from JSON file
- `--prompt PROMPT` - Video generation prompt (required if not using --file)
- `--model MODEL` - Model to use (default: sora-2)
- `--seconds SECONDS` - Video duration in seconds
- `--size SIZE` - Video resolution (e.g., 1920x1080)
- `--wait` - Wait for video completion with progress bar
- `--no-save` - Don't save video info to JSON when complete

### 2. Remix a Video

```bash
python sora_api.py remix \
  --video-id video_abc123 \
  --prompt "Make it sunrise instead of sunset" \
  --wait
```

**Options:**
- `--video-id VIDEO_ID` - ID of the video to remix (required)
- `--prompt PROMPT` - Remix prompt (required)
- `--model MODEL` - Model to use (default: sora-2)
- `--seconds SECONDS` - Video duration in seconds
- `--size SIZE` - Video resolution
- `--wait` - Wait for completion
- `--no-save` - Don't save video info

### 3. List Videos

```bash
# List 20 most recent videos
python sora_api.py list --limit 20

# List with pagination
python sora_api.py list --limit 10 --order desc

# Pagination with cursor
python sora_api.py list --after cursor_xyz
```

**Options:**
- `--limit LIMIT` - Number of videos to return (default: 20)
- `--order ORDER` - Sort order: asc or desc (default: desc)
- `--after AFTER` - Cursor for pagination (after)
- `--before BEFORE` - Cursor for pagination (before)

### 4. Retrieve Video Information

```bash
python sora_api.py retrieve --video-id video_abc123
```

This displays:
- Video ID
- Status (queued, in_progress, completed, failed, etc.)
- Progress percentage
- Creation timestamp
- Full JSON response

### 5. Download a Video

```bash
# Auto-generated filename: <video_id>.mp4
python sora_api.py download --video-id video_abc123

# Custom filename
python sora_api.py download --video-id video_abc123 --output my_video.mp4

# Download specific variant
python sora_api.py download --video-id video_abc123 --variant hd --output video.mp4
```

**Options:**
- `--video-id VIDEO_ID` - ID of the video to download (required)
- `--output OUTPUT` - Output filename (default: <video_id>.mp4)
- `--variant VARIANT` - Video variant to download

### 6. Wait for Video Completion

```bash
# Wait with default settings (3s interval, 10min timeout)
python sora_api.py wait --video-id video_abc123

# Custom interval and timeout
python sora_api.py wait \
  --video-id video_abc123 \
  --interval 5 \
  --timeout 1800
```

**Options:**
- `--video-id VIDEO_ID` - ID of the video to wait for (required)
- `--interval INTERVAL` - Polling interval in seconds (default: 3)
- `--timeout TIMEOUT` - Maximum wait time in seconds (default: 600)
- `--no-save` - Don't save video info when complete

### 7. Delete a Video

```bash
# With confirmation prompt
python sora_api.py delete --video-id video_abc123

# Skip confirmation
python sora_api.py delete --video-id video_abc123 --yes
```

**Options:**
- `--video-id VIDEO_ID` - ID of the video to delete (required)
- `--yes` - Skip confirmation prompt

## Auto-Save Feature

### What Gets Saved?

When a video reaches "completed" status, the CLI automatically saves a JSON file containing:

1. **Timestamp** - When the info was saved
2. **Creation Arguments** - All parameters used to create/remix the video
3. **API Response** - Complete response from the API

### File Location

Files are saved to: `videos/<video_id>.json`

Example: `videos/video_abc123xyz.json`

### File Format

```json
{
  "saved_at": "2025-10-19T14:30:45.123456",
  "creation_args": {
    "prompt": "A sunset over the ocean",
    "model": "sora-2",
    "seconds": "5",
    "size": "1920x1080"
  },
  "api_response": {
    "id": "video_abc123xyz",
    "status": "completed",
    "progress": 100,
    "created_at": 1729351845,
    "prompt": "A sunset over the ocean",
    ...
  }
}
```

### Disabling Auto-Save

Use the `--no-save` flag:

```bash
python sora_api.py create --prompt "Test" --wait --no-save
```

## Progress Tracking

When using `--wait`, you'll see real-time progress updates:

```
Waiting for video 'video_abc123' to complete...
  [5s] Status: Queued, waiting to start...
  [12s] Progress: [███░░░░░░░░░░░░░░░░░░░░░░░░░░░] 10%
  [23s] Progress: [████████████░░░░░░░░░░░░░░░░░░] 40%
  [45s] Progress: [███████████████████████░░░░░░░] 75%
  [67s] Progress: [██████████████████████████████] 100%
  [67s] Status: Completed! ✓

✓ Video generation completed successfully!
  Total time: 67 seconds
```

## Example Workflows

### Complete Video Creation Workflow

```bash
# 1. Create a video and wait for completion
python sora_api.py create --prompt "A dragon flying over mountains" --wait

# 2. Check the saved JSON file
type videos\video_abc123.json

# 3. Download the video
python sora_api.py download --video-id video_abc123 --output dragon.mp4
```

### Batch Creation with JSON Files

```bash
# Create multiple videos using different JSON files
python sora_api.py create --file scene1.json --wait
python sora_api.py create --file scene2.json --wait
python sora_api.py create --file scene3.json --wait
```

### Monitor Existing Video

```bash
# Start a video without waiting
python sora_api.py create --prompt "A space station orbiting Earth"

# Later, check its status
python sora_api.py retrieve --video-id video_xyz789

# Wait for it to complete
python sora_api.py wait --video-id video_xyz789
```

## Tips

1. **Always use `--wait`** when creating/remixing if you want the video info auto-saved
2. **Check video status** before downloading to ensure it's completed
3. **Use JSON files** for complex or repeated requests
4. **Set longer timeouts** for longer videos: `--timeout 1800` (30 minutes)
5. **The videos/ folder is gitignored** - your video info JSONs won't be committed

## Error Handling

The CLI provides helpful error messages:

- **Missing API Key**: "Please run 'setup_env.bat' to set up your API key"
- **Timeout**: "Video generation timed out after X seconds"
- **Failed Generation**: "Video generation failed: [error message]"
- **Missing Parameters**: "Error: --prompt is required when not using --file"

## Getting Help

For any command, add `--help`:

```bash
python sora_api.py --help
python sora_api.py create --help
python sora_api.py remix --help
```
