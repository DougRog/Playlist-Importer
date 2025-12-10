# Playlist Importer

Automated playlist file routing and management system for broadcast automation. Supports WOS, SCH, and SCD file formats with configurable routing to station-specific folders.

Includes **Media Checker** - a validation tool that indexes media files and checks WOS playlists for missing media references.

## Features

- **Automated File Processing**: Monitors import folder and routes files based on configurable prefix mappings
- **Multi-Format Support**: Handles WOS, SCH, and SCD file types (configurable)
- **Web Interface**: Flask-based GUI for easy file uploads and configuration management
- **Archive System**: Automatically archives processed files with timestamps
- **Email Notifications**: Sends alerts for imported and deleted files
- **Real-time Logging**: Daily log files with detailed processing information

## Components

### 1. PlaylistImporter.py
Background service that monitors the import folder and processes playlist files.

**Features:**
- Monitors import folder every 60 seconds
- Routes files based on filename prefix to designated station folders
- Archives all processed files with timestamps
- Sends email notifications for imports and deletions
- Reloads configuration automatically (no restart needed)

### 2. web_interface.py
Flask web application for management and configuration.

**Features:**
- File upload interface
- Configure folder mappings (prefix → station folder)
- Manage allowed file types (WOS, SCH, SCD, etc.)
- Update directory paths
- View log files

### 3. Media Checker (media_checker.py + media_checker_web.py)
Validates that all media referenced in WOS playlists actually exists in the media library.

**Features:**
- Indexes all media files from `/mnt/mc_media`
- Parses WOS files to extract media references
- Identifies missing media files
- Web interface at `http://localhost:5001`
- Export results as CSV or JSON
- Refresh capability to verify if missing media has been added

**See [MEDIA_CHECKER_README.md](MEDIA_CHECKER_README.md) for detailed documentation.**

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure the configuration file exists (created automatically with defaults):
```bash
# config.json will be created in the application directory
```

3. Update configuration as needed via web interface or manually edit config.json

## Usage

### Running the Importer Service

```bash
python PlaylistImporter.py
```

This starts the background monitoring service. Leave it running to process files automatically.

### Running the Web Interface

```bash
python web_interface.py
```

Access the web interface at: `http://localhost:5000`

For remote access: `http://your-server-ip:5000`

### Running the Media Checker

```bash
python media_checker_web.py
```

Access the media checker at: `http://localhost:5001`

**Quick Start:**
1. Open http://localhost:5001 in your browser
2. Click "Run Check" to scan WOS files and validate media
3. View missing media files and export reports
4. Click "Run Check" again after adding missing media to verify

See [MEDIA_CHECKER_README.md](MEDIA_CHECKER_README.md) for complete documentation.

## Configuration

### Via Web Interface (Recommended)

1. Navigate to `http://localhost:5000/configure`
2. Manage settings through the GUI:
   - **Allowed File Types**: Add/remove file extensions (WOS, SCH, SCD, etc.)
   - **Folder Mappings**: Map filename prefixes to destination folders
   - **Directory Paths**: Configure import, archive, destination, and log folders

### Manual Configuration

Edit `config.json`:

```json
{
    "directories": {
        "import_folder": "/mnt/playlists/Import",
        "archive_folder": "/mnt/playlists/Archive",
        "final_destination_root": "/mnt/playlists",
        "log_folder": "/home/lilly/Logs"
    },
    "email": {
        "to": "drogers@lillybroadcasting.com",
        "from": "mib@lillyhubtv.com",
        "password": "N0t1fy!@!",
        "smtp_server": "smtp-legacy.office365.com",
        "smtp_port": 587
    },
    "allowed_file_types": ["WOS", "SCH", "SCD"],
    "folder_mappings": {
        "FOX6": "FOX 6",
        "WENY": "WENY ABC",
        "ABC7": "ABC 7"
    }
}
```

## Workflow

1. **Upload**: Files uploaded via web interface or placed in import folder
2. **Detection**: Importer detects new files (waits 30 seconds for stability)
3. **Validation**: Checks if file extension is in allowed types
4. **Routing**: Matches filename prefix to folder mapping
5. **Archive**: Copies file to archive with timestamp
6. **Move**: Moves file to destination station folder
7. **Notify**: Sends email with processing summary

## File Processing Rules

- **Allowed Files**: Only files matching configured extensions are processed
- **Prefix Matching**: Filenames must start with a configured prefix
- **Unmapped Files**: Files without matching prefix are deleted
- **Non-Allowed Types**: Files with non-allowed extensions are deleted
- **Stability Check**: Files must be unchanged for 30 seconds before processing

## Directory Structure

```
/mnt/playlists/
├── Import/              # Upload files here
├── Archive/            # Timestamped copies
├── FOX 6/              # Station folders
├── WENY ABC/
├── ABC 7/
└── ...

/home/lilly/Logs/       # Daily log files
└── PlaylistImporter-YYYY-MM-DD.txt
```

## Web Interface Pages

- **Dashboard** (`/`): Overview of configuration and quick actions
- **Upload** (`/upload`): Upload playlist files
- **Configure** (`/configure`): Manage settings
- **Logs** (`/logs`): View historical log files

## Running as a Service

### Linux (systemd)

Create `/etc/systemd/system/playlist-importer.service`:

```ini
[Unit]
Description=Playlist Importer Service
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/home/user/Playlist-Importer
ExecStart=/usr/bin/python3 /home/user/Playlist-Importer/PlaylistImporter.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable playlist-importer
sudo systemctl start playlist-importer
```

### Web Interface Service

Create `/etc/systemd/system/playlist-web.service`:

```ini
[Unit]
Description=Playlist Importer Web Interface
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/home/user/Playlist-Importer
ExecStart=/usr/bin/python3 /home/user/Playlist-Importer/web_interface.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Security Considerations

- **Credentials**: Email password is stored in config.json - ensure proper file permissions
- **Web Access**: By default, web interface runs on all interfaces (0.0.0.0)
- **Upload Validation**: Only configured file types are accepted
- **File Permissions**: Ensure proper permissions on import/archive/destination folders

## Troubleshooting

### Files Not Processing
- Check if PlaylistImporter.py is running
- Verify file extension is in allowed_file_types
- Ensure filename starts with a configured prefix
- Check log files for errors

### Web Interface Not Accessible
- Verify web_interface.py is running
- Check firewall settings (port 5000)
- Ensure Flask is installed

### Email Notifications Not Sending
- Verify SMTP settings in config.json
- Check email credentials
- Review logs for email errors

## Support

For issues or questions, check the log files in the configured log folder.
