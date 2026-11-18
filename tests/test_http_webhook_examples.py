import sys
"""Test raw-body webhook verification on local-only listeners."""
import hashlib, hmac, os, socket, subprocess, time, unittest, urllib.request, urllib.error
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SECRET = 'whsec_synthetic_only'
BODY = b'{"event":"extract.processed"}'

def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0)); return sock.getsockname()[1]

def post(port, signature, delivery):
    req = urllib.request.Request(f'http://127.0.0.1:{port}/', data=BODY, method='POST', headers={'X-Xtrakt-Signature': signature, 'X-Xtrakt-Delivery': delivery, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=3) as result: return result.status
    except urllib.error.HTTPError as error: return error.code

def signature(timestamp, body=BODY):
    digest = hmac.new(SECRET.encode(), str(timestamp).encode() + b'.' + body, hashlib.sha256).hexdigest()
    return f't={timestamp},v1={digest}'

class WebhookExamples(unittest.TestCase):
    def exercise(self, command):
        port = free_port(); env = dict(os.environ, COGNERIS_WEBHOOK_SECRET=SECRET, WEBHOOK_PORT=str(port), DOTNET_ROLL_FORWARD='Major')
        process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            deadline = time.monotonic() + 30
            while True:
                if process.poll() is not None: self.fail('listener exited: ' + process.stderr.read().decode())
                try:
                    with socket.create_connection(('127.0.0.1', port), timeout=.2): break
                except OSError:
                    if time.monotonic() > deadline: self.fail('listener did not start')
                    time.sleep(.1)
            now = int(time.time())
            self.assertEqual(post(port, signature(now, b'tampered'), 'delivery-a'), 401)
            self.assertEqual(post(port, signature(now - 600), 'delivery-b'), 401)
            self.assertEqual(post(port, signature(now), 'delivery-a'), 200)
            self.assertEqual(post(port, signature(now), 'delivery-a'), 200)
        finally:
            process.terminate(); process.wait(timeout=5); process.stderr.close()
    def test_python(self): self.exercise([sys.executable, 'examples/http-webhook/python/receiver.py'])
    def test_dotnet(self): self.exercise(['dotnet', 'run', '--project', 'examples/http-webhook/dotnet'])
if __name__ == '__main__': unittest.main()
