import os
import shutil
import time
import smtplib
from email.message import EmailMessage
from datetime import datetime

# Directories
import_folder = '/mnt/playlists/Import'
archive_folder = '/mnt/playlists/Archive'
final_destination_root = '/mnt/playlists'
log_folder = '/home/lilly/Logs'

# Email settings
EMAIL_TO = 'drogers@lillybroadcasting.com'
EMAIL_FROM = 'mib@lillyhubtv.com'
EMAIL_PASSWORD = 'N0t1fy!@!'
SMTP_SERVER = 'smtp-legacy.office365.com'
SMTP_PORT = 587

# Ensure log folder exists
os.makedirs(log_folder, exist_ok=True)
log_file = os.path.join(log_folder, f'PlaylistImporter-{datetime.now():%Y-%m-%d}.txt')

# Mapping filename prefixes to folders
folder_map = {
    "FOX6": "FOX 6",
    "WENY": "WENY ABC",
    "ABC7": "ABC 7",
    "EENY": "WENY CBS",
    "SEE": "SEE CBS",
    "WCVI": "WCVI CBS",
    "EZMQ": "WZMQ CBS",
    "WSEE": "WSEE CBS",
    "WICU": "WICU NBC",
    "OCTV": "OCTV",
    "ENNPLUS": "ENN+",
    "ECVI": "WCVI ABC",
    "WSJP": "WSJP FOX",
    "WVXF": "WVXF FOX",
    "WVGN": "WVGN NBC",
    "GENY": "WENY CW",
    "NYLOCAL": "NY Local"
}

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
            imported_files = []
            deleted_files = []

            for file_name in os.listdir(import_folder):
                file_path = os.path.join(import_folder, file_name)

                if not os.path.isfile(file_path):
                    continue

                # Handle non-WOS files
                if not file_name.lower().endswith('.wos'):
                    try:
                        os.remove(file_path)
                        msg = f"Deleted non-WOS file: {file_path}"
                        log(msg)
                        deleted_files.append(msg)
                    except Exception as e:
                        log(f"Failed to delete non-WOS file {file_path}: {e}")
                    continue

                # Skip unstable WOS files
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
                            archive_name = f"{os.path.splitext(file_name)[0]}_{timestamp}.WOS"
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
                        msg = f"Deleted unmapped WOS file: {file_path}"
                        log(msg)
                        deleted_files.append(msg)
                    except Exception as e:
                        log(f"Failed to delete unmapped WOS file {file_path}: {e}")

            # Send combined email notifications
            if imported_files:
                send_email(
                    "Playlist Imports Completed",
                    "The following WOS files were imported:\n\n" + "\n\n".join(imported_files)
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
    log("Monitoring for .WOS files")
    move_files()
