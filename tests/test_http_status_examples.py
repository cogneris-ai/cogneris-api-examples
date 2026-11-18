import sys
"""Hermetic status request checks for the raw HTTP examples."""
import json
import os
from pathlib import Path
import subprocess
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
ROOT = Path(__file__).resolve().parents[1]
JOB = '22222222-2222-4222-8222-222222222222'
class Handler(BaseHTTPRequestHandler):
    requests = []
    def do_GET(self):
        self.requests.append((self.path, self.headers.get('Authorization')))
        body = json.dumps({'data': {'jobId': JOB, 'status': 'Succeeded', 'outputReference': 'artifact://synthetic/result.json'}, 'hasErrors': False} if self.path.startswith('/api/v1/document-jobs/') else {'Metadata': {'synthetic': 'ok'}}).encode()
        self.send_response(200); self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self, *args): pass
class StatusExamples(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler); cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True); cls.thread.start()
    @classmethod
    def tearDownClass(cls): cls.server.shutdown(); cls.server.server_close(); cls.thread.join()
    def setUp(self): Handler.requests.clear()
    def run_example(self, command):
        env = dict(os.environ, COGNERIS_API_KEY='synthetic-test-key', COGNERIS_API_BASE=f'http://127.0.0.1:{self.server.server_port}', DOTNET_ROLL_FORWARD='Major')
        result = subprocess.run(command + [JOB], cwd=ROOT, env=env, text=True, capture_output=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Handler.requests, [('/api/v1/document-jobs/' + JOB, 'Bearer synthetic-test-key'), ('/api/v1/artifacts/content?reference=artifact%3A%2F%2Fsynthetic%2Fresult.json', 'Bearer synthetic-test-key')])
        self.assertIn('Succeeded', result.stdout)
        self.assertIn('synthetic', result.stdout)
    def test_python(self): self.run_example([sys.executable, 'examples/http-status/python/status.py'])
    def test_dotnet(self): self.run_example(['dotnet', 'run', '--project', 'examples/http-status/dotnet', '--'])
if __name__ == '__main__': unittest.main()
