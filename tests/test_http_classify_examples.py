import sys
"""Hermetic contract checks for the raw HTTP classification examples."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]

class Handler(BaseHTTPRequestHandler):
    requests = []
    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        self.requests.append((self.path, self.headers.get('Authorization'), self.headers.get('Content-Type'), body))
        result = json.dumps({'data': {'documents': []}, 'hasErrors': False}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(result)))
        self.end_headers()
        self.wfile.write(result)
    def log_message(self, *args): pass

class ClassifyExamples(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join()
    def setUp(self): Handler.requests.clear()
    def run_example(self, command):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / 'synthetic.pdf'
            file.write_bytes(b'%PDF-1.4\nsynthetic-fixture\n%%EOF\n')
            env = dict(os.environ, COGNERIS_API_KEY='synthetic-test-key', COGNERIS_API_BASE=f'http://127.0.0.1:{self.server.server_port}', DOTNET_ROLL_FORWARD='Major')
            result = subprocess.run(command + [str(file)], cwd=ROOT, env=env, text=True, capture_output=True, timeout=120)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(Handler.requests), 1)
            route, auth, content_type, body = Handler.requests[0]
            self.assertEqual(route, '/Document/classifier')
            self.assertEqual(auth, 'Bearer synthetic-test-key')
            self.assertTrue(content_type.startswith('multipart/form-data; boundary='))
            self.assertRegex(body, rb'name=(?:"files"|files)(?:;|\r)')
            self.assertIn(b'application/pdf', body)
            self.assertIn(b'synthetic-fixture', body)
    def test_python(self): self.run_example([sys.executable, 'examples/http-classify/python/classify.py'])
    def test_dotnet(self): self.run_example(['dotnet', 'run', '--project', 'examples/http-classify/dotnet', '--'])

if __name__ == '__main__': unittest.main()
