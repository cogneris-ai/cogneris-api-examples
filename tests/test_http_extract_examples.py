import sys
"""Hermetic multipart upload and schema-backed extraction request checks."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = '11111111-1111-4111-8111-111111111111'
class Handler(BaseHTTPRequestHandler):
    requests = []
    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        self.requests.append((self.path, self.headers.get('Authorization'), self.headers.get('Content-Type'), body))
        data = {'reference': 'artifact://synthetic'} if self.path == '/api/v1/artifacts' else {'jobId': '22222222-2222-4222-8222-222222222222', 'status': 'Pending'}
        result = json.dumps({'data': data, 'hasErrors': False}).encode()
        self.send_response(201 if self.path == '/api/v1/artifacts' else 202)
        self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(result))); self.end_headers(); self.wfile.write(result)
    def log_message(self, *args): pass
class ExtractExamples(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler); cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True); cls.thread.start()
    @classmethod
    def tearDownClass(cls): cls.server.shutdown(); cls.server.server_close(); cls.thread.join()
    def setUp(self): Handler.requests.clear()
    def run_example(self, command):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / 'synthetic.pdf'; file.write_bytes(b'%PDF-1.4\nsynthetic-fixture\n%%EOF\n')
            env = dict(os.environ, COGNERIS_API_KEY='synthetic-test-key', COGNERIS_API_BASE=f'http://127.0.0.1:{self.server.server_port}', DOTNET_ROLL_FORWARD='Major')
            result = subprocess.run(command + [str(file), TEMPLATE], cwd=ROOT, env=env, text=True, capture_output=True, timeout=120)
            self.assertEqual(result.returncode, 0, result.stderr); self.assertEqual(len(Handler.requests), 2)
            upload, submit = Handler.requests
            self.assertEqual(upload[0], '/api/v1/artifacts'); self.assertEqual(upload[1], 'Bearer synthetic-test-key')
            self.assertRegex(upload[3], rb'name=(?:"file"|file)(?:;|\r)'); self.assertIn(b'application/pdf', upload[3])
            self.assertEqual(submit[0], '/api/v1/document-jobs'); self.assertEqual(submit[1], 'Bearer synthetic-test-key')
            data = json.loads(submit[3]); self.assertEqual(data['operation'], 'Extraction'); self.assertEqual(data['inputReference'], 'artifact://synthetic'); self.assertEqual(data['templateId'], TEMPLATE)
    def test_python(self): self.run_example([sys.executable, 'examples/http-extract/python/extract.py'])
    def test_dotnet(self): self.run_example(['dotnet', 'run', '--project', 'examples/http-extract/dotnet', '--'])
if __name__ == '__main__': unittest.main()
