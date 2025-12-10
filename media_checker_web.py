#!/usr/bin/env python3
"""
Media Checker Web Interface
Web-based interface for monitoring missing media files in WOS playlists
"""

from flask import Flask, render_template, jsonify, request
import media_checker
from datetime import datetime
import os

app = Flask(__name__, template_folder='templates')
app.secret_key = 'media-checker-secret-key-change-in-production'

# Store the last check results
last_results = None
check_in_progress = False

@app.route('/')
def index():
    """Main media checker dashboard"""
    return render_template('media_checker.html')

@app.route('/api/check', methods=['POST'])
def run_check():
    """Run a media check"""
    global last_results, check_in_progress

    if check_in_progress:
        return jsonify({'error': 'Check already in progress'}), 429

    try:
        check_in_progress = True
        last_results = media_checker.perform_check()
        check_in_progress = False

        return jsonify({
            'success': True,
            'message': 'Check completed successfully',
            'results': last_results
        })
    except Exception as e:
        check_in_progress = False
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/results')
def get_results():
    """Get the last check results"""
    if last_results is None:
        return jsonify({
            'success': False,
            'message': 'No check has been run yet'
        })

    return jsonify({
        'success': True,
        'results': last_results,
        'check_in_progress': check_in_progress
    })

@app.route('/api/status')
def get_status():
    """Get current status"""
    return jsonify({
        'check_in_progress': check_in_progress,
        'has_results': last_results is not None,
        'last_check_time': last_results['validation_results']['check_time'] if last_results else None
    })

@app.route('/api/config')
def get_config():
    """Get current configuration"""
    return jsonify({
        'media_root': media_checker.MEDIA_ROOT,
        'wos_search_paths': media_checker.WOS_SEARCH_PATHS,
        'media_root_exists': os.path.exists(media_checker.MEDIA_ROOT),
        'wos_paths_exist': [
            {'path': path, 'exists': os.path.exists(path)}
            for path in media_checker.WOS_SEARCH_PATHS
        ]
    })

@app.route('/api/missing_detail/<media_name>')
def get_missing_detail(media_name):
    """Get detailed information about a specific missing media file"""
    if last_results is None:
        return jsonify({'error': 'No results available'}), 404

    for item in last_results['validation_results']['missing_media']:
        if item['media_name'] == media_name:
            return jsonify(item)

    return jsonify({'error': 'Media not found in results'}), 404

@app.route('/export/csv')
def export_csv():
    """Export missing media as CSV"""
    if last_results is None:
        return "No results available", 404

    from flask import Response
    import io
    import csv

    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(['Media Name', 'Reference Count', 'WOS Files'])

    # Write data
    for item in last_results['validation_results']['missing_media']:
        wos_files = ', '.join([ref['wos_file'] for ref in item['referenced_in']])
        writer.writerow([item['media_name'], item['reference_count'], wos_files])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=missing_media_{datetime.now():%Y%m%d_%H%M%S}.csv'}
    )

@app.route('/export/json')
def export_json():
    """Export missing media as JSON"""
    if last_results is None:
        return jsonify({'error': 'No results available'}), 404

    from flask import Response
    import json

    return Response(
        json.dumps(last_results, indent=2),
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment; filename=missing_media_{datetime.now():%Y%m%d_%H%M%S}.json'}
    )

if __name__ == '__main__':
    print("Media Checker Web Interface")
    print("=" * 60)
    print(f"Media Root: {media_checker.MEDIA_ROOT}")
    print(f"WOS Search Paths: {len(media_checker.WOS_SEARCH_PATHS)} configured")
    print("=" * 60)
    print("\nStarting web server on http://0.0.0.0:5001")
    print("Access the interface at: http://localhost:5001")
    print("\n")

    # Run on port 5001 (different from the main web interface)
    app.run(host='0.0.0.0', port=5001, debug=True)
