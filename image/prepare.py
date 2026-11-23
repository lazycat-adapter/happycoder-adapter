"""Build and push the combined Happy Web/Server image for LazyCat delivery."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parent
UPSTREAM_WEB_HOOK = Path("packages/happy-app/sources/hooks/useSessionQuickActions.ts")


def required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"{name} is required")
    return value


def patch_upstream_web_source(source_dir: Path) -> None:
    """Apply the narrow v1.1.6 Web build compatibility fix.

    The v1.1.6 tag contains two `showActionAlert` declarations in this hook,
    which makes Expo's Web compiler reject the otherwise usable release. Keep
    the newer actionItems-based declaration and remove only the earlier block.
    Later upstream tags are left untouched unless they contain the same exact
    duplicate shape.
    """
    source_file = source_dir / UPSTREAM_WEB_HOOK
    if not source_file.is_file():
        raise SystemExit(f"Happy Web hook is missing: {source_file}")
    text = source_file.read_text(encoding="utf-8")
    marker = "    const showActionAlert = React.useCallback(() => {"
    if text.count(marker) != 2:
        return
    first = text.index(marker)
    second = text.index(marker, first + len(marker))
    action_items = text.index("\n\n    const actionItems", first, second)
    source_file.write_text(text[:first] + text[action_items + 2 :], encoding="utf-8")
    print("Applied the Happy v1.1.6 duplicate showActionAlert compatibility fix")


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
    if os.environ.get("LAZYCAT_SOURCE_VERSION", "").strip() == "1.1.6":
        patch_upstream_web_source(source_dir)

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
