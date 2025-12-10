#!/usr/bin/env python3
"""
Media Checker - Validates media file references in WOS playlist files
Indexes media files and checks if all referenced media exists
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import json

# Configuration
MEDIA_ROOT = '/mnt/mc_media'
WOS_SEARCH_PATHS = [
    '/mnt/playlists/FOX 6',
    '/mnt/playlists/WENY ABC',
    '/mnt/playlists/ABC 7',
    '/mnt/playlists/WENY CBS',
    '/mnt/playlists/SEE CBS',
    '/mnt/playlists/WCVI CBS',
    '/mnt/playlists/WZMQ CBS',
    '/mnt/playlists/WSEE CBS',
    '/mnt/playlists/WICU NBC',
    '/mnt/playlists/OCTV',
    '/mnt/playlists/ENN+',
    '/mnt/playlists/WCVI ABC',
    '/mnt/playlists/WSJP FOX',
    '/mnt/playlists/WVXF FOX',
    '/mnt/playlists/WVGN NBC',
    '/mnt/playlists/WENY CW',
    '/mnt/playlists/NY Local'
]

class MediaIndexer:
    """Indexes media files from the media root directory"""

    def __init__(self, media_root):
        self.media_root = media_root
        self.media_index = set()
        self.index_time = None
        self.file_count = 0

    def build_index(self):
        """Build index of all media files (without extensions)"""
        print(f"Indexing media files from {self.media_root}...")
        self.media_index = set()
        self.file_count = 0

        if not os.path.exists(self.media_root):
            print(f"Warning: Media root {self.media_root} does not exist")
            self.index_time = datetime.now()
            return

        for root, dirs, files in os.walk(self.media_root):
            for filename in files:
                # Store filename without extension
                name_without_ext = os.path.splitext(filename)[0]
                self.media_index.add(name_without_ext.upper())  # Store uppercase for case-insensitive matching
                self.file_count += 1

        self.index_time = datetime.now()
        print(f"Indexed {self.file_count} media files ({len(self.media_index)} unique names)")

    def has_media(self, filename_without_ext):
        """Check if media file exists in index"""
        return filename_without_ext.upper() in self.media_index

    def get_stats(self):
        """Return indexing statistics"""
        return {
            'total_files': self.file_count,
            'unique_names': len(self.media_index),
            'index_time': self.index_time.strftime('%Y-%m-%d %H:%M:%S') if self.index_time else 'Never',
            'media_root': self.media_root
        }


class WOSParser:
    """Parses WOS (Wide Orbit Schedule) files to extract media references"""

    def __init__(self):
        self.media_references = []

    def parse_file(self, wos_file_path):
        """Parse a WOS file and extract media references"""
        references = []

        try:
            # WOS files are typically XML-based
            tree = ET.parse(wos_file_path)
            root = tree.getroot()

            # Common tags that contain media file references in WOS files:
            # <MediaFile>, <FileName>, <VideoFile>, <AudioFile>, <Material>, etc.
            media_tags = [
                './/MediaFile',
                './/FileName',
                './/VideoFile',
                './/AudioFile',
                './/Material',
                './/File',
                './/media',
                './/filename'
            ]

            for tag_pattern in media_tags:
                elements = root.findall(tag_pattern)
                for element in elements:
                    if element.text:
                        # Remove any path information and extension
                        media_name = os.path.basename(element.text.strip())
                        name_without_ext = os.path.splitext(media_name)[0]
                        if name_without_ext:  # Skip empty values
                            references.append(name_without_ext)

            # Also check attributes that might contain filenames
            for element in root.iter():
                for attr_name in ['file', 'media', 'filename', 'source']:
                    if attr_name in element.attrib:
                        media_name = os.path.basename(element.attrib[attr_name].strip())
                        name_without_ext = os.path.splitext(media_name)[0]
                        if name_without_ext:
                            references.append(name_without_ext)

        except ET.ParseError as e:
            print(f"XML Parse error in {wos_file_path}: {e}")
            # If XML parsing fails, try a simple text-based approach
            references = self._parse_as_text(wos_file_path)
        except Exception as e:
            print(f"Error parsing {wos_file_path}: {e}")

        return references

    def _parse_as_text(self, wos_file_path):
        """Fallback: Parse as text file looking for common media extensions"""
        references = []
        media_extensions = ['.mpg', '.mpeg', '.mp4', '.avi', '.mov', '.mxf', '.wav', '.mp3']

        try:
            with open(wos_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

                # Look for filenames with media extensions
                for ext in media_extensions:
                    import re
                    # Find patterns like "filename.ext"
                    pattern = r'(\w+)' + re.escape(ext)
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    references.extend(matches)
        except Exception as e:
            print(f"Error reading {wos_file_path} as text: {e}")

        return references


class MediaValidator:
    """Validates media references against indexed media files"""

    def __init__(self, media_indexer):
        self.indexer = media_indexer
        self.results = {
            'wos_files_checked': 0,
            'total_references': 0,
            'missing_media': [],
            'missing_by_wos': defaultdict(list),
            'check_time': None
        }

    def check_wos_files(self, wos_paths):
        """Check all WOS files for missing media"""
        print("Checking WOS files for missing media...")

        parser = WOSParser()
        missing_media = defaultdict(list)  # media_name -> [wos_files]
        wos_file_count = 0
        total_refs = 0

        for search_path in wos_paths:
            if not os.path.exists(search_path):
                print(f"Warning: WOS path {search_path} does not exist")
                continue

            # Find all WOS files in this path
            for wos_file in Path(search_path).glob('*.WOS'):
                wos_file_count += 1
                wos_file_str = str(wos_file)

                # Parse the WOS file
                references = parser.parse_file(wos_file_str)
                total_refs += len(references)

                # Check each reference
                for media_ref in references:
                    if not self.indexer.has_media(media_ref):
                        missing_media[media_ref].append({
                            'wos_file': os.path.basename(wos_file_str),
                            'wos_folder': os.path.basename(os.path.dirname(wos_file_str)),
                            'wos_path': wos_file_str
                        })

        # Convert to list format for easier display
        missing_list = []
        missing_by_wos = defaultdict(list)

        for media_name, wos_files in missing_media.items():
            missing_list.append({
                'media_name': media_name,
                'referenced_in': wos_files,
                'reference_count': len(wos_files)
            })

            # Also organize by WOS file
            for wos_info in wos_files:
                missing_by_wos[wos_info['wos_file']].append(media_name)

        # Sort by reference count (most referenced first)
        missing_list.sort(key=lambda x: x['reference_count'], reverse=True)

        self.results = {
            'wos_files_checked': wos_file_count,
            'total_references': total_refs,
            'missing_count': len(missing_list),
            'missing_media': missing_list,
            'missing_by_wos': dict(missing_by_wos),
            'check_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        print(f"Checked {wos_file_count} WOS files")
        print(f"Found {total_refs} media references")
        print(f"Missing media files: {len(missing_list)}")

        return self.results

    def get_results(self):
        """Return validation results"""
        return self.results


# Global instances
media_indexer = MediaIndexer(MEDIA_ROOT)
media_validator = MediaValidator(media_indexer)

def perform_check():
    """Perform a full media check"""
    # Rebuild index
    media_indexer.build_index()

    # Check WOS files
    results = media_validator.check_wos_files(WOS_SEARCH_PATHS)

    return {
        'index_stats': media_indexer.get_stats(),
        'validation_results': results
    }


if __name__ == "__main__":
    print("Media Checker - Validating WOS file references")
    print("=" * 60)

    results = perform_check()

    print("\n" + "=" * 60)
    print("RESULTS:")
    print("=" * 60)
    print(f"Media Index: {results['index_stats']['unique_names']} files")
    print(f"WOS Files Checked: {results['validation_results']['wos_files_checked']}")
    print(f"Missing Media: {results['validation_results']['missing_count']}")

    if results['validation_results']['missing_count'] > 0:
        print("\nMissing Media Files:")
        for item in results['validation_results']['missing_media'][:10]:  # Show first 10
            print(f"  - {item['media_name']} (referenced in {item['reference_count']} WOS files)")

        if results['validation_results']['missing_count'] > 10:
            print(f"  ... and {results['validation_results']['missing_count'] - 10} more")
