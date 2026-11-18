#!/usr/bin/env python3
"""Classify one PDF using requests, without the Cogneris SDK."""
import os
from pathlib import Path
import sys
from urllib.parse import urlparse
import requests


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python classify.py DOCUMENT.pdf')
    key = os.environ.get('COGNERIS_API_KEY')
    base = os.environ.get('COGNERIS_API_BASE', 'https://api-eu.cogneris.ai').rstrip('/')
    parsed = urlparse(base)
    if not key:
        raise SystemExit('Set COGNERIS_API_KEY in the environment.')
    if parsed.scheme != 'https' and not (parsed.scheme == 'http' and parsed.hostname in {'127.0.0.1', 'localhost'}):
        raise SystemExit('Use HTTPS for the API; HTTP is allowed only for a local test server.')
    document = Path(sys.argv[1])
    with document.open('rb') as stream:
        response = requests.post(base + '/Document/classifier', headers={'Authorization': 'Bearer ' + key},
                                 files={'files': (document.name, stream, 'application/pdf')}, timeout=120)
    response.raise_for_status()
    if response.json().get('hasErrors'): raise SystemExit('Classification reported an error.')
    print(response.text)


if __name__ == '__main__':
    main()
