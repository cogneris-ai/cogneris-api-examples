#!/usr/bin/env python3
"""Local demonstration receiver for signed job webhooks; not a production server."""
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import time

SECRET = os.environ.get('COGNERIS_WEBHOOK_SECRET', '')
if not SECRET: raise SystemExit('Set COGNERIS_WEBHOOK_SECRET in the environment.')
PORT = int(os.environ.get('WEBHOOK_PORT', '8080'))
seen = set()  # Demonstration only: production needs a durable, atomic idempotency store.

class Receiver(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', '-1'))
            if length < 0 or length > 1024 * 1024: raise ValueError('invalid length')
            body = self.rfile.read(length)
            parts = self.headers.get('X-Xtrakt-Signature', '').split(',')
            if len(parts) != 2 or not parts[0].startswith('t=') or not parts[1].startswith('v1='): raise ValueError('invalid signature')
            timestamp = int(parts[0][2:]); supplied = parts[1][3:]
            if abs(int(time.time()) - timestamp) > 300: raise ValueError('expired signature')
            expected = hmac.new(SECRET.encode(), str(timestamp).encode() + b'.' + body, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected, supplied): raise ValueError('invalid signature')
            delivery = self.headers.get('X-Xtrakt-Delivery', '')
            if not delivery or len(delivery) > 200: raise ValueError('invalid delivery')
            if delivery not in seen:
                seen.add(delivery)
                # Process the event here after durable deduplication in a real application.
            self.send_response(200)
        except (ValueError, OverflowError): self.send_response(401)
        self.send_header('Content-Length', '0'); self.end_headers()
    def log_message(self, *args): pass

HTTPServer(('127.0.0.1', PORT), Receiver).serve_forever()
