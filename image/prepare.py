"""Build and push the combined Happy Web/Server image for LazyCat delivery."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parent


def required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"{name} is required")
    return value


def main() -> None:
    source_dir = Path(required("LAZYCAT_SOURCE_DIR")).resolve()
    output_image = required("LAZYCAT_OUTPUT_IMAGE")
    target_platform = os.environ.get("LAZYCAT_TARGET_PLATFORM", "linux/amd64").strip()
    if not source_dir.is_dir():
        raise SystemExit(f"source directory does not exist: {source_dir}")
    if not output_image.startswith("ttl.sh/"):
        raise SystemExit("Happy Coder prepared images must use ttl.sh staging")
    if not target_platform:
        raise SystemExit("LAZYCAT_TARGET_PLATFORM is required")

    command = [
        "docker",
        "buildx",
        "build",
        "--platform",
        target_platform,
        "--file",
        str(ROOT / "Dockerfile"),
        "--tag",
        output_image,
        "--build-arg",
        "SOURCE_REF=" + os.environ.get("LAZYCAT_SOURCE_REF", ""),
        "--build-arg",
        "SOURCE_REVISION=" + os.environ.get("LAZYCAT_SOURCE_REVISION", ""),
        "--build-arg",
        "SOURCE_VERSION=" + os.environ.get("LAZYCAT_SOURCE_VERSION", ""),
        "--build-arg",
        "APPLICATION_VERSION=" + os.environ.get("LAZYCAT_APPLICATION_VERSION", ""),
        "--push",
        str(source_dir),
    ]
    print(f"Building Happy Coder source into {output_image}")
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
