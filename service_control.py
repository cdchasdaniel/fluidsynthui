#!/usr/bin/env python3
"""
Lightweight service control daemon for FluidSynthUI
Runs independently and can start/stop the main Django service via systemctl
Listens on port 8081 for HTTP requests
"""

import subprocess
import json
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_systemctl_command(action):
    """Run systemctl command in background thread"""
    try:
        subprocess.run(
            ['systemctl', '--user', action, 'fluidsynthui.service'],
            timeout=30,
            check=False,
            capture_output=True
        )
        logger.info(f"Service {action} command completed")
    except subprocess.TimeoutExpired:
        logger.error(f"{action} command timed out")
    except Exception as e:
        logger.error(f"Error executing {action}: {e}")


class ServiceControlHandler(BaseHTTPRequestHandler):
    """HTTP request handler for service control"""

    def do_GET(self):
        """Handle GET requests"""
        path = urlparse(self.path).path
        
        # Normalize path - handle both with and without trailing slash
        if path.endswith('/'):
            path_normalized = path
        else:
            path_normalized = path + '/'

        if path_normalized == '/service/status/':
            self.handle_status()
        elif path_normalized == '/service/start/':
            self.handle_start()
        elif path_normalized == '/service/stop/':
            self.handle_stop()
        else:
            self.send_error(404, 'Not Found')

    def handle_status(self):
        """Check if fluidsynthui service is running"""
        try:
            result = subprocess.run(
                ['systemctl', '--user', 'is-active', 'fluidsynthui.service'],
                capture_output=True,
                text=True,
                timeout=5,
                check=False
            )
            is_running = result.returncode == 0
            self.send_json_response({
                'success': True,
                'running': is_running,
                'status': 'running' if is_running else 'stopped'
            })
        except subprocess.TimeoutExpired:
            logger.error("Status check timed out")
            self.send_json_response({
                'success': False,
                'error': 'Status check timed out',
                'running': False
            }, 500)
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            self.send_json_response({
                'success': False,
                'error': str(e),
                'running': False
            }, 500)

    def handle_start(self):
        """Start the fluidsynthui service (non-blocking)"""
        try:
            # Run in background thread so HTTP response returns immediately
            thread = threading.Thread(target=run_systemctl_command, args=('start',))
            thread.daemon = True
            thread.start()
            
            logger.info("Service start command queued")
            self.send_json_response({
                'success': True,
                'message': 'Service starting...'
            })
        except Exception as e:
            logger.error(f"Start failed: {e}")
            self.send_json_response({
                'success': False,
                'error': str(e)
            }, 500)

    def handle_stop(self):
        """Stop the fluidsynthui service (non-blocking)"""
        try:
            # Run in background thread so HTTP response returns immediately
            thread = threading.Thread(target=run_systemctl_command, args=('stop',))
            thread.daemon = True
            thread.start()
            
            logger.info("Service stop command queued")
            self.send_json_response({
                'success': True,
                'message': 'Service stopping...'
            })
        except Exception as e:
            logger.error(f"Stop failed: {e}")
            self.send_json_response({
                'success': False,
                'error': str(e)
            }, 500)

    def send_json_response(self, data, status_code=200):
        """Send a JSON response"""
        response = json.dumps(data).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response)
        self.wfile.flush()

    def log_message(self, format, *args):
        """Suppress default logging"""
        logger.info(format % args)


def run_server(port=8081):
    """Run the service control server"""
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, ServiceControlHandler)
    logger.info(f"Service control daemon listening on port {port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        httpd.shutdown()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8081
    run_server(port)
