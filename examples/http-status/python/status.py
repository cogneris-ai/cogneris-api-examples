#!/usr/bin/env python3
"""Read an asynchronous job status without the Cogneris SDK."""
import os
import sys
from urllib.parse import urlparse
from uuid import UUID
import requests


def main():
    if len(sys.argv) != 2: raise SystemExit('Usage: python status.py JOB_ID')
    job_id = str(UUID(sys.argv[1]))
    key = os.environ.get('COGNERIS_API_KEY')
    base = os.environ.get('COGNERIS_API_BASE', 'https://api-eu.cogneris.ai').rstrip('/')
    parsed = urlparse(base)
    if not key: raise SystemExit('Set COGNERIS_API_KEY in the environment.')
    if parsed.scheme != 'https' and not (parsed.scheme == 'http' and parsed.hostname in {'127.0.0.1', 'localhost'}):
        raise SystemExit('Use HTTPS for the API; HTTP is allowed only for a local test server.')
    response = requests.get(base + '/api/v1/document-jobs/' + job_id, headers={'Authorization': 'Bearer ' + key}, timeout=30)
    response.raise_for_status()
    envelope = response.json()
    if envelope.get('hasErrors'): raise SystemExit('Status request reported an error.')
    print(response.text)
    job = envelope['data']
    if job.get('status') == 'Succeeded' and job.get('outputReference'):
        result = requests.get(base + '/api/v1/artifacts/content', params={'reference': job['outputReference']},
                              headers={'Authorization': 'Bearer ' + key}, timeout=30)
        result.raise_for_status()
        print(result.text)


if __name__ == '__main__': main()
