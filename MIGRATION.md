# Migration Guide: Legacy → Production Structure

## Overview

This guide helps you transition from the legacy structure to the new production-ready structure. **Migration is optional** - legacy files continue to work.

## What Changed

### Directory Structure

**Before (Legacy)**
```
Sora/
├── sora_api.py              # API client
├── web_app.py               # Flask app
└── templates/
    └── index.html
```

**After (Production)**
```
Sora/
├── src/                     # NEW: Production code
│   ├── api/
│   │   └── sora_api.py     # Documented API client
│   └── app/
│       ├── web_app.py      # Documented Flask app
│       └── templates/
│           └── index.html
├── sora_api.py              # Legacy (still works)
├── web_app.py               # Legacy (still works)
└── templates/               # Legacy (still works)
```

## Migration Steps

### Option 1: No Migration (Keep Using Legacy)

**Nothing to do!** Your current setup continues to work:

```bash
# Still works
python web_app.py

# Still works
python sora_api.py create --prompt "Test"
```

### Option 2: Gradual Migration (Recommended)

#### Step 1: Update Python Scripts

**Before**
```python
from sora_api import SoraAPIClient

client = SoraAPIClient()
```

**After**
```python
from src.api.sora_api import SoraAPIClient

client = SoraAPIClient()
```

#### Step 2: Update Run Commands

**Before**
```bash
python web_app.py
```

**After**
```bash
python src/app/web_app.py
```

#### Step 3: Update CLI Commands

**Before**
```bash
python sora_api.py create --prompt "Test"
```

**After**
```bash
python src/api/sora_api.py create --prompt "Test"
```

### Option 3: Full Migration (Optional)

If you want to remove legacy files entirely:

1. **Verify new structure works**
   ```bash
   python src/app/web_app.py
   ```

2. **Update any custom scripts** to use new imports

3. **Backup legacy files** (optional)
   ```bash
   mkdir backup
   copy sora_api.py backup/
   copy web_app.py backup/
   ```

4. **Remove legacy files** (optional, not recommended yet)
   ```bash
   # Only do this if you're confident!
   # Remove legacy files:
   # - sora_api.py
   # - web_app.py
   # - templates/index.html
   ```

## Benefits of New Structure

### 1. Better Documentation

**Before**
```python
def create(self, prompt, model="sora-2", ...):
    """Create a video"""
    # What parameters? What does it return?
```

**After**
```python
def create(self, prompt: str, model: str = "sora-2", ...) -> Dict[str, Any]:
    """
    Create a new video using the Sora 2 API.
    
    Args:
        prompt (str): Text description of the video to generate
        model (str): Model to use (default: "sora-2")
        ...
    
    Returns:
        dict: Video job information including:
            - id (str): Video identifier
            - status (str): Current status
            - progress (int): Completion percentage
    
    Example:
        >>> client = SoraAPIClient()
        >>> video = client.create(prompt="A sunset", wait_for_completion=True)
        >>> print(video['id'])
    """
```

### 2. Better IDE Support

- **Type hints**: Your IDE can autocomplete better
- **Documentation**: Hover over functions to see details
- **Error checking**: Catch type errors before running

### 3. Professional Structure

- **Organized**: Separate API and app logic
- **Scalable**: Easy to add new modules
- **Standard**: Follows Python packaging best practices

## Compatibility Matrix

| Feature | Legacy | Production | Notes |
|---------|--------|------------|-------|
| Web Interface | ✅ Works | ✅ Works | Identical functionality |
| CLI Commands | ✅ Works | ✅ Works | Same commands, different path |
| Python Import | ✅ Works | ✅ Works | Need to update import statement |
| Video Files | ✅ Compatible | ✅ Compatible | No migration needed |
| API Calls | ✅ Same | ✅ Same | Identical API behavior |
| Documentation | ⚠️ Basic | ✅ Comprehensive | Major improvement |

## Common Migration Scenarios

### Scenario 1: I have custom scripts

**Before** (`my_script.py`)
```python
from sora_api import SoraAPIClient

def generate_videos():
    client = SoraAPIClient()
    # ... your code
```

**After** (`my_script.py`)
```python
from src.api.sora_api import SoraAPIClient

def generate_videos():
    client = SoraAPIClient()
    # ... rest of your code stays the same!
```

### Scenario 2: I run the web app daily

**Before**
```bash
python web_app.py
```

**After** (choose one)
```bash
# Option A: Use new structure
python src/app/web_app.py

# Option B: Keep using legacy (still works)
python web_app.py
```

### Scenario 3: I use the CLI frequently

**Before**
```bash
python sora_api.py create --prompt "Video" --wait
```

**After** (choose one)
```bash
# Option A: Use new structure
python src/api/sora_api.py create --prompt "Video" --wait

# Option B: Keep using legacy (still works)
python sora_api.py create --prompt "Video" --wait
```

## Troubleshooting

### Import Error: No module named 'src'

**Problem**: Python can't find the src module

**Solution**: Make sure you're in the project root directory
```bash
cd C:\dev\Sora
python src/app/web_app.py
```

### Import Error: No module named 'api.sora_api'

**Problem**: Import statement is incorrect

**Fix**:
```python
# Wrong
from api.sora_api import SoraAPIClient

# Correct
from src.api.sora_api import SoraAPIClient
```

### My videos disappeared!

**Don't worry!** Videos are stored in `videos/` directory regardless of which version you use. They work with both legacy and production code.

### Which version should I use?

**Short answer**: Either! Use whichever you're comfortable with.

**Recommendation**: Start using production structure for new work, migrate existing scripts when convenient.

## Testing Your Migration

After migrating, verify everything works:

```bash
# Test API client import
python -c "from src.api.sora_api import SoraAPIClient; print('✓ API import works')"

# Test web app starts
python src/app/web_app.py
# (Should show: "Starting server at http://localhost:5000")

# Test CLI
python src/api/sora_api.py --help
# (Should show help text)
```

## Rollback

If you encounter issues, you can always use the legacy files:

```bash
# Use legacy web app
python web_app.py

# Use legacy CLI
python sora_api.py create --prompt "Test"
```

Everything in the legacy files still works exactly as before.

## Questions?

- **I don't want to migrate**: That's fine! Legacy files work perfectly.
- **Can I use both?**: Yes! You can mix legacy and production code.
- **Will legacy be removed?**: No immediate plans. It's there for backward compatibility.
- **Is migration required?**: No, it's completely optional.

## Summary

✅ **Migration is optional**  
✅ **Both versions work**  
✅ **No breaking changes**  
✅ **Migrate at your own pace**  
✅ **Video files work with both versions**

Choose what works best for you!
