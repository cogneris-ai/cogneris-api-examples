from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Mapping, Sequence


def is_java_17(java: Path) -> bool:
    try:
        result = subprocess.run(
            [str(java), "-version"], text=True, capture_output=True, check=False
        )
    except OSError:
        return False
    return result.returncode == 0 and bool(
        re.search(r'(?:openjdk|java) version "17\.', result.stdout + result.stderr)
    )


def configured_java_home(environment: Mapping[str, str]) -> Path | None:
    configured_home = environment.get("JAVA_HOME")
    if configured_home:
        home = Path(configured_home)
        if is_java_17(home / "bin" / "java"):
            return home

    java = shutil.which("java", path=environment.get("PATH"))
    if java and is_java_17(Path(java)):
        return Path(java).resolve().parent.parent
    return None


def java_environment(environment: Mapping[str, str]) -> dict[str, str]:
    """Return an environment whose java executable reports major version 17."""
    java_home = configured_java_home(environment)
    if java_home is None:
        from jdk4py import JAVA_HOME

        java_home = Path(JAVA_HOME)
        if not is_java_17(java_home / "bin" / "java"):
            raise RuntimeError(f"jdk4py did not provide Java 17 at {java_home}")

    result = dict(environment)
    result["JAVA_HOME"] = str(java_home)
    result["PATH"] = os.pathsep.join(
        entry for entry in (str(java_home / "bin"), result.get("PATH")) if entry
    )
    return result


def main(arguments: Sequence[str]) -> int:
    """Run arguments after `--` under Java 17 and return the child status."""
    if not arguments or arguments[0] != "--" or len(arguments) == 1:
        print("usage: run-java.py -- <command> [args...]", file=sys.stderr)
        return 2
    return subprocess.run(arguments[1:], env=java_environment(os.environ)).returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
