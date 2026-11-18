#!/usr/bin/env python3
"""Submit schema-backed asynchronous extraction without the Cogneris SDK."""
import os
from pathlib import Path
import sys
from urllib.parse import urlparse
from uuid import UUID, uuid4
import requests


def main():
    if len(sys.argv) != 3: raise SystemExit('Usage: python extract.py DOCUMENT.pdf TEMPLATE_ID')
    template = str(UUID(sys.argv[2]))
    key = os.environ.get('COGNERIS_API_KEY')
    base = os.environ.get('COGNERIS_API_BASE', 'https://api-eu.cogneris.ai').rstrip('/')
    parsed = urlparse(base)
    if not key: raise SystemExit('Set COGNERIS_API_KEY in the environment.')
    if parsed.scheme != 'https' and not (parsed.scheme == 'http' and parsed.hostname in {'127.0.0.1', 'localhost'}):
        raise SystemExit('Use HTTPS for the API; HTTP is allowed only for a local test server.')
    headers = {'Authorization': 'Bearer ' + key}
    document = Path(sys.argv[1])
    with document.open('rb') as stream:
        upload = requests.post(base + '/api/v1/artifacts', headers=headers, files={'file': (document.name, stream, 'application/pdf')}, timeout=120)
    upload.raise_for_status()
    envelope = upload.json()
    if envelope.get('hasErrors'): raise SystemExit('Artifact upload reported an error.')
    reference = envelope['data']['reference']
    job = requests.post(base + '/api/v1/document-jobs', headers={**headers, 'Idempotency-Key': str(uuid4())},
                        json={'operation': 'Extraction', 'inputReference': reference, 'templateId': template}, timeout=120)
    job.raise_for_status()
    if job.json().get('hasErrors'): raise SystemExit('Job submission reported an error.')
    print(job.text)


if __name__ == '__main__': main()
