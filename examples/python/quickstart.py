"""Safe first-result examples using the installed Cogneris Python SDK."""

import json
import os
import sys
from pathlib import Path
from typing import Callable, Mapping, Optional, Sequence, TextIO

from cogneris_document_ai_sdk import CognerisClient, CognerisError


USAGE = """Usage:
  python quickstart.py extract <file>
  python quickstart.py async <operation> <input-reference>"""
OPERATIONS = {"Extraction", "Classification", "ZeroShot", "Crop", "Split"}


class UsageError(Exception):
    """The local example configuration or invocation is invalid."""


def _required(value: Optional[str]) -> bool:
    return isinstance(value, str) and bool(value.strip()) and not value.startswith("-")


def _configuration(environment: Mapping[str, str]) -> dict[str, str]:
    api_key = environment.get("COGNERIS_API_KEY")
    if not _required(api_key):
        raise UsageError("Set COGNERIS_API_KEY before running this example.")
    region = environment.get("COGNERIS_REGION", "us")
    if region not in {"us", "eu"}:
        raise UsageError("COGNERIS_REGION must be either us or eu.")
    return {"api_key": api_key, "region": region}


def _command(arguments: Sequence[str]):
    if len(arguments) == 2 and arguments[0] == "extract" and _required(arguments[1]):
        return "extract", arguments[1], None
    if (
        len(arguments) == 3
        and arguments[0] == "async"
        and arguments[1] in OPERATIONS
        and _required(arguments[2])
    ):
        return "async", arguments[1], arguments[2]
    raise UsageError("Choose a supported example command.")


def _write_json(output: TextIO, value: object) -> None:
    output.write(json.dumps(value, separators=(",", ":")) + "\n")


def _run_example_for_testing(
    *,
    arguments: Sequence[str],
    environment: Mapping[str, str],
    stdout: TextIO,
    stderr: TextIO,
    _create_client_for_testing: Optional[Callable[..., CognerisClient]] = None,
) -> int:
    client = None
    try:
        kind, first, second = _command(arguments)
        options = _configuration(environment)
        create_client = _create_client_for_testing or CognerisClient
        client = create_client(**options)

        if kind == "extract":
            try:
                contents = Path(first).read_bytes()
            except OSError:
                raise UsageError("Unable to read the input file.") from None
            result = client.extract(contents, file_name=Path(first).name)
            has_errors = result.has_errors if isinstance(result.has_errors, bool) else None
            http_status_code = getattr(result.meta, "http_status_code", None)
            if not isinstance(http_status_code, int):
                http_status_code = None
            _write_json(
                stdout,
                {
                    "operation": "extraction",
                    "hasErrors": has_errors,
                    "httpStatusCode": http_status_code,
                },
            )
            return 0

        submission = client.submit_job(first, second)
        job_id = getattr(submission, "job_id", None)
        if not job_id:
            raise CognerisError("Cogneris API response did not include a job ID.")
        job = client.wait_for_job(job_id)
        _write_json(
            stdout,
            {
                "operation": first,
                "jobId": str(job_id),
                "status": str(job.status),
            },
        )
        return 0
    except UsageError as error:
        stderr.write(f"{error}\n{USAGE}\n")
        return 2
    except CognerisError as error:
        stderr.write(f"{error}\n")
        return 1
    except Exception:
        stderr.write("Cogneris example failed.\n")
        return 1
    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    raise SystemExit(
        _run_example_for_testing(
            arguments=sys.argv[1:],
            environment=os.environ,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
    )
