#!/usr/bin/env python3
"""
Flask app for cron-job.org webhook
Exposes /check endpoint that runs ticket check
"""
from flask import Flask, jsonify
from check_tickets import check_all_events
from datetime import datetime

app = Flask(__name__)


@app.route('/')
def index():
    """Health check"""
    return jsonify({
        'status': 'ok',
        'service': 'ticket-monitor',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/check')
def check():
    """Run ticket check - called by cron-job.org"""
    try:
        print(f"🔔 Check triggered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        found = check_all_events()

        return jsonify({
            'status': 'success',
            'tickets_found': found,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"⚠️ Error in /check: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/health')
def health():
    """Kubernetes-style health check"""
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    # For local testing
    app.run(host='0.0.0.0', port=5000, debug=True)
