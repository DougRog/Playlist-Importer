# Media Checker - WOS Playlist Validator

Automated media validation tool that indexes media files and checks WOS playlist references to identify missing media.

## Overview

The Media Checker scans your media library (`/mnt/mc_media`), indexes all media files, and then validates that all media referenced in WOS (Wide Orbit Schedule) playlist files actually exists. It provides a web interface to view missing media and export reports.

## Features

- **Automatic Media Indexing**: Scans entire media library and indexes filenames (without extensions)
- **WOS File Parsing**: Extracts media references from XML-based WOS files
- **Smart Validation**: Compares WOS references against indexed media (case-insensitive)
- **Real-time Web Interface**: Modern dashboard to view missing media
- **Multiple Views**: View missing media by file name or by WOS playlist
- **Export Capabilities**: Export results as CSV or JSON
- **Refresh on Demand**: Re-run checks to verify if missing media has been added

## Components

### 1. media_checker.py
Core validation engine that performs the indexing and validation.

**Features:**
- `MediaIndexer`: Indexes all media files from `/mnt/mc_media`
- `WOSParser`: Parses WOS files to extract media references
- `MediaValidator`: Compares references against index to find missing media

### 2. media_checker_web.py
Flask web application providing the user interface.

**Features:**
- Web dashboard at `http://localhost:5001`
- REST API for running checks and retrieving results
- CSV and JSON export functionality
- Real-time status updates

## Installation

The Media Checker uses the same dependencies as the main Playlist Importer:

```bash
pip install -r requirements.txt
```

## Configuration

Edit the configuration in `media_checker.py`:

```python
# Media library root directory
MEDIA_ROOT = '/mnt/mc_media'

# WOS file search paths (station folders)
WOS_SEARCH_PATHS = [
    '/mnt/playlists/FOX 6',
    '/mnt/playlists/WENY ABC',
    '/mnt/playlists/ABC 7',
    # ... add more paths as needed
]
```

## Usage

### Command Line

Run a one-time check from the command line:

```bash
python3 media_checker.py
```

This will:
1. Index all media files in `/mnt/mc_media`
2. Scan all WOS files in configured paths
3. Display missing media in the console

### Web Interface (Recommended)

Start the web server:

```bash
python3 media_checker_web.py
```

Access the interface at: `http://localhost:5001`

**Web Interface Features:**
1. **Run Check**: Click to perform a new media validation
2. **Refresh Results**: Reload the last check results
3. **View Missing Media**: See all missing files with details
4. **Filter**: Search/filter missing media by name
5. **Toggle Views**: Switch between "By Media" and "By WOS File" views
6. **Export**: Download results as CSV or JSON

## How It Works

### 1. Media Indexing
```
/mnt/mc_media/
├── video1.mpg          → Indexed as "VIDEO1"
├── commercial.mp4      → Indexed as "COMMERCIAL"
└── show_episode.mxf    → Indexed as "SHOW_EPISODE"
```

The indexer:
- Walks through all directories under media root
- Extracts filenames without extensions
- Stores uppercase versions for case-insensitive matching
- Tracks total file count and unique names

### 2. WOS File Parsing

The parser extracts media references from WOS files using:
- **XML Parsing**: Looks for common tags like `<MediaFile>`, `<FileName>`, `<Material>`, etc.
- **Attribute Checking**: Checks XML attributes for media file references
- **Fallback Mode**: If XML parsing fails, uses regex to find media extensions

Example WOS snippet:
```xml
<Event>
    <MediaFile>commercial_spot_123</MediaFile>
    <FileName>news_open</FileName>
</Event>
```

### 3. Validation

For each media reference in WOS files:
1. Remove file extension (if present)
2. Convert to uppercase
3. Check if exists in media index
4. If not found, add to missing media list

### 4. Results

Missing media is organized:
- **By Media**: Each missing file with list of WOS files that reference it
- **By WOS File**: Each WOS file with its list of missing media
- **Statistics**: Counts and percentages

## Web Interface Guide

### Dashboard Overview

**Statistics Cards:**
- **Media Files Indexed**: Total unique media files found
- **WOS Files Checked**: Number of playlist files scanned
- **Media References**: Total references found in all WOS files
- **Missing Media**: Count of missing files (red = problem)

### View Modes

**View by Media** (Default)
- Shows each missing media file
- Displays how many WOS files reference it
- Lists all WOS files that need this media
- Sorted by reference count (most critical first)

**View by WOS File**
- Shows each WOS file that has missing media
- Displays count of missing files per playlist
- Lists all missing media for that WOS file
- Useful for fixing playlists one at a time

### Filtering

Use the filter box to search:
- Media file names
- WOS file names
- Any text in the results

### Export Options

**CSV Export:**
- Columns: Media Name, Reference Count, WOS Files
- Good for spreadsheets and reporting
- Filename: `missing_media_YYYYMMDD_HHMMSS.csv`

**JSON Export:**
- Full structured data
- Includes all metadata
- Good for programmatic processing
- Filename: `missing_media_YYYYMMDD_HHMMSS.json`

## Workflow Example

1. **Initial Check**
   ```bash
   python3 media_checker_web.py
   ```
   Access http://localhost:5001 and click "Run Check"

2. **Review Results**
   - See 50 missing media files
   - Filter to find specific problems
   - Export CSV for team review

3. **Add Missing Media**
   - Copy missing files to `/mnt/mc_media`
   - Or update WOS files to reference correct media

4. **Re-check**
   - Click "Run Check" again
   - Verify missing count decreases
   - Continue until all media found

## Common WOS File Tags

The parser looks for these XML tags:
- `<MediaFile>` - Primary media reference
- `<FileName>` - File name field
- `<VideoFile>` - Video content
- `<AudioFile>` - Audio content
- `<Material>` - Material/clip reference
- `<File>` - Generic file reference
- `<media>` - Lowercase variant
- `<filename>` - Lowercase variant

And these XML attributes:
- `file="..."`
- `media="..."`
- `filename="..."`
- `source="..."`

## Performance Considerations

**Indexing Time:**
- 10,000 files: ~2-5 seconds
- 100,000 files: ~20-60 seconds
- 1,000,000 files: ~3-10 minutes

**WOS Parsing:**
- Depends on number and size of WOS files
- Typically 10-100 WOS files: ~1-5 seconds

**Optimization Tips:**
1. Run checks during off-hours if media library is very large
2. Use the web interface to avoid re-indexing unnecessarily
3. Results are cached - "Refresh Results" just reloads without re-checking

## Troubleshooting

### No Media Files Found
- Check that `/mnt/mc_media` path is correct
- Verify directory exists and is readable
- Check permissions

### No WOS Files Found
- Verify WOS_SEARCH_PATHS are correct
- Check that paths exist
- Ensure WOS files have `.WOS` extension (case-sensitive)

### WOS Files Not Parsing
- Check if files are valid XML
- View console output for parsing errors
- Files will fall back to text-based parsing if XML fails

### False Positives (Media Exists but Marked Missing)
- Check filename exactly matches (case doesn't matter)
- Verify file extension is removed correctly
- Check for special characters or spaces in filenames

## API Endpoints

### POST /api/check
Run a new media check
```bash
curl -X POST http://localhost:5001/api/check
```

### GET /api/results
Get last check results
```bash
curl http://localhost:5001/api/results
```

### GET /api/status
Get current status
```bash
curl http://localhost:5001/api/status
```

### GET /api/config
Get configuration
```bash
curl http://localhost:5001/api/config
```

### GET /export/csv
Download CSV export
```bash
curl http://localhost:5001/export/csv > missing_media.csv
```

### GET /export/json
Download JSON export
```bash
curl http://localhost:5001/export/json > missing_media.json
```

## Running as a Service

### Linux (systemd)

Create `/etc/systemd/system/media-checker.service`:

```ini
[Unit]
Description=Media Checker Web Interface
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/home/user/Playlist-Importer
ExecStart=/usr/bin/python3 /home/user/Playlist-Importer/media_checker_web.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable media-checker
sudo systemctl start media-checker
```

## Integration with Playlist Importer

The Media Checker is designed to work alongside the Playlist Importer:

- **Playlist Importer** (port 5000): Manages file uploads and routing
- **Media Checker** (port 5001): Validates media references

Both can run simultaneously and independently.

## Best Practices

1. **Regular Checks**: Run media checks before going to air
2. **Pre-validation**: Check new WOS files before deployment
3. **Archive Cleanup**: Identify and remove unreferenced media
4. **Documentation**: Keep CSV exports as audit trail
5. **Workflow Integration**: Add to production checklist

## Future Enhancements

Potential improvements:
- Scheduled automatic checks
- Email alerts for missing media
- Media usage statistics
- Duplicate media detection
- Size and duration information
- Integration with automation systems

## Support

For issues or questions:
- Check the console output for detailed error messages
- Review WOS file format if parsing fails
- Verify paths and permissions
- Check web interface at http://localhost:5001
