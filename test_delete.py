from sora_api import SoraAPIClient

client = SoraAPIClient()

# List all videos
print("Fetching video list...")
videos = client.list()['data']
print(f"Found {len(videos)} total videos\n")

# Find completed videos
completed = [v for v in videos if v.get('status') == 'completed']
print(f"Completed videos: {len(completed)}")
for v in completed[:5]:
    print(f"  - {v['id']}: status={v.get('status')}, prompt={v.get('prompt', 'N/A')[:50]}")

print()

# Find in-progress videos
in_progress = [v for v in videos if v.get('status') in ['in_progress', 'queued']]
print(f"In-progress/queued videos: {len(in_progress)}")
for v in in_progress[:5]:
    print(f"  - {v['id']}: status={v.get('status')}, prompt={v.get('prompt', 'N/A')[:50]}")

# Try to delete the first completed video if any
if completed:
    print(f"\n\nAttempting to delete completed video: {completed[0]['id']}")
    try:
        result = client.delete(completed[0]['id'])
        print(f"✓ SUCCESS! Deleted: {result}")
    except Exception as e:
        print(f"✗ FAILED: {e}")
else:
    print("\n\nNo completed videos to delete. Wait for a video to complete first.")
