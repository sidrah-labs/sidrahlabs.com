#!/usr/bin/env python3
"""
Sidrah Labs Mini CMS Static Site Generator.
Renders content/site.yaml through templates/*.jinja into production-ready static assets.
"""

import sys
import time
from pathlib import Path
import jinja2
import yaml

BASE_DIR = Path(__file__).resolve().parent
CONTENT_PATH = BASE_DIR / "content" / "site.yaml"
TEMPLATES_DIR = BASE_DIR / "templates"
INDEX_OUTPUT = BASE_DIR / "index.html"
LLMS_OUTPUT = BASE_DIR / "llms.txt"


def load_content() -> dict:
    if not CONTENT_PATH.exists():
        raise FileNotFoundError(f"Content file missing: {CONTENT_PATH}")
    with open(CONTENT_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build() -> None:
    start_time = time.time()
    content = load_content()

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=jinja2.select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # 1. Render index.html
    index_template = env.get_template("index.html.jinja")
    rendered_html = index_template.render(**content)
    with open(INDEX_OUTPUT, "w", encoding="utf-8") as f:
        f.write(rendered_html)

    # 2. Render llms.txt (plain text, no HTML autoescape)
    txt_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    llms_template = txt_env.get_template("llms.txt.jinja")
    rendered_llms = llms_template.render(**content)
    with open(LLMS_OUTPUT, "w", encoding="utf-8") as f:
        f.write(rendered_llms)

    elapsed_ms = (time.time() - start_time) * 1000
    html_size = INDEX_OUTPUT.stat().st_size
    llms_size = LLMS_OUTPUT.stat().st_size

    print(f"✓ Built index.html ({html_size:,} bytes) and llms.txt ({llms_size:,} bytes) in {elapsed_ms:.1f}ms")


def watch() -> None:
    print(f"Watching {CONTENT_PATH} and {TEMPLATES_DIR} for changes... (Ctrl+C to stop)")
    build()
    last_mtimes = {}

    def get_watch_files():
        files = [CONTENT_PATH]
        if TEMPLATES_DIR.exists():
            files.extend(TEMPLATES_DIR.glob("*.jinja"))
        return files

    while True:
        try:
            changed = False
            for path in get_watch_files():
                if not path.exists():
                    continue
                mtime = path.stat().st_mtime
                if path in last_mtimes and mtime > last_mtimes[path]:
                    changed = True
                last_mtimes[path] = mtime

            if changed:
                print(f"[{time.strftime('%H:%M:%S')}] Detected modification, rebuilding...")
                build()

            time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nStopped watcher.")
            break


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--watch":
        watch()
    else:
        build()
