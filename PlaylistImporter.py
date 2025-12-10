import os
import shutil
import time
import smtplib
import json
from email.message import EmailMessage
from datetime import datetime

# Configuration file path
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

# Global configuration variables
config = {}
import_folder = None
archive_folder = None
final_destination_root = None
log_folder = None
log_file = None
EMAIL_TO = None
EMAIL_FROM = None
EMAIL_PASSWORD = None
SMTP_SERVER = None
SMTP_PORT = None
folder_map = {}
allowed_file_types = []

def load_config():
    """Load configuration from config.json file"""
    global config, import_folder, archive_folder, final_destination_root, log_folder
    global log_file, EMAIL_TO, EMAIL_FROM, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT
    global folder_map, allowed_file_types

    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)

        # Load directories
        import_folder = config['directories']['import_folder']
        archive_folder = config['directories']['archive_folder']
        final_destination_root = config['directories']['final_destination_root']
        log_folder = config['directories']['log_folder']

        # Load email settings
        EMAIL_TO = config['email']['to']
        EMAIL_FROM = config['email']['from']
        EMAIL_PASSWORD = config['email']['password']
        SMTP_SERVER = config['email']['smtp_server']
        SMTP_PORT = config['email']['smtp_port']

        # Load folder mappings and allowed file types
        folder_map = config['folder_mappings']
        allowed_file_types = [ft.upper() for ft in config['allowed_file_types']]

        # Ensure log folder exists
        os.makedirs(log_folder, exist_ok=True)
        log_file = os.path.join(log_folder, f'PlaylistImporter-{datetime.now():%Y-%m-%d}.txt')

        return True
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return False

# Load initial configuration
load_config()

def log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_message = f"{timestamp} - {message}"
    print(full_message)
    with open(log_file, "a") as f:
        f.write(full_message + "\n")

def send_email(subject, body):
    try:
        msg = EmailMessage()
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO
        msg['Subject'] = subject
        msg.set_content(body)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_FROM, EMAIL_PASSWORD)
            smtp.send_message(msg)

        log(f"Email sent: {subject}")
    except Exception as e:
        log(f"Failed to send email: {e}")

def is_stable_file(file_path, delay=30):
    last_modified = os.path.getmtime(file_path)
    return (time.time() - last_modified) > delay

def move_files():
    while True:
        try:
            # Reload configuration on each iteration
            load_config()

            imported_files = []
            deleted_files = []

            for file_name in os.listdir(import_folder):
                file_path = os.path.join(import_folder, file_name)

                if not os.path.isfile(file_path):
                    continue

                # Handle files not matching allowed types
                file_ext = os.path.splitext(file_name)[1][1:].upper()  # Get extension without dot
                if file_ext not in allowed_file_types:
                    try:
                        os.remove(file_path)
                        msg = f"Deleted non-allowed file type: {file_path}"
                        log(msg)
                        deleted_files.append(msg)
                    except Exception as e:
                        log(f"Failed to delete non-allowed file {file_path}: {e}")
                    continue

                # Skip unstable files
                if not is_stable_file(file_path):
                    log(f"Skipping {file_name}, file not stable yet")
                    continue

                matched = False
                for prefix, target_folder in folder_map.items():
                    if file_name.startswith(prefix):
                        matched = True
                        try:
                            final_folder_path = os.path.join(final_destination_root, target_folder)
                            os.makedirs(final_folder_path, exist_ok=True)
                            final_path = os.path.join(final_folder_path, file_name)

                            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                            file_base, file_extension = os.path.splitext(file_name)
                            archive_name = f"{file_base}_{timestamp}{file_extension}"
                            archive_path = os.path.join(archive_folder, archive_name)

                            shutil.copy2(file_path, archive_path)
                            log(f"Copied to archive: {archive_path}")

                            shutil.move(file_path, final_path)
                            log(f"Moved to final destination: {final_path}")

                            imported_files.append(
                                f"{file_name}\n→ {target_folder}\n→ Archived: {archive_path}\n→ Moved to: {final_path}"
                            )
                        except Exception as e:
                            log(f"Error processing {file_name}: {e}")
                        break

                if not matched:
                    try:
                        os.remove(file_path)
                        msg = f"Deleted unmapped playlist file: {file_path}"
                        log(msg)
                        deleted_files.append(msg)
                    except Exception as e:
                        log(f"Failed to delete unmapped playlist file {file_path}: {e}")

            # Send combined email notifications
            if imported_files:
                send_email(
                    "Playlist Imports Completed",
                    "The following playlist files were imported:\n\n" + "\n\n".join(imported_files)
                )

            if deleted_files:
                send_email(
                    "Files Deleted During Playlist Import",
                    "The following files were deleted:\n\n" + "\n\n".join(deleted_files)
                )

        except Exception as main_err:
            log(f"Main loop error: {main_err}")
        time.sleep(60)

if __name__ == "__main__":
    log(f"Monitoring for playlist files: {', '.join(allowed_file_types)}")
    move_files()
