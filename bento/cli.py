"""Command line interface: python -m bento <command>."""
import argparse
import os
import sys

from . import __version__, render, stats
from .config import ConfigError, load

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES = ("designer", "developer", "minimal", "neon", "editorial", "terminal", "pastel")
PLACEHOLDER_USER = "your-github-username"

WORKFLOW = """name: update bento

on:
  schedule:
    - cron: "17 4 * * *"   # every day at 04:17 UTC
  workflow_dispatch:         # run it by hand from the Actions tab
  push:
    branches: [main]
    paths: ["bento.yml"]

permissions:
  contents: write

jobs:
  bento:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: amehara/readme-bento@v1
        # with:
        #   token: ${{ secrets.STATS_TOKEN }}   # optional PAT: also counts private repos/contributions
"""


def _fail(msg):
    print(f"error: {msg}", file=sys.stderr)
    return 1


def cmd_build(args):
    cfg = load(args.config)
    base = os.path.dirname(os.path.abspath(args.config)) if args.out_dir is None else args.out_dir
    user = cfg["user"]
    if user == PLACEHOLDER_USER:
        user = ""  # untouched template: nothing real to fetch
    if args.demo:
        data = stats.demo(user)
    elif args.offline or not user:
        data = stats.load_cache(base) or stats.demo(user)
        if not user and not args.offline:
            print("note: no github.user set, using demo data (set github.user in the config)", file=sys.stderr)
    else:
        token = os.environ.get("STATS_TOKEN") or os.environ.get("GITHUB_TOKEN")
        data = stats.fetch(user, token, bool(os.environ.get("STATS_TOKEN")), base)
        stats.save_cache(data, base)
    for path in render.build(cfg, data, base):
        print("wrote", os.path.relpath(path))
    print("\nREADME snippet:\n" + render.readme_snippet(cfg))
    return 0


def cmd_outputs(args):
    cfg = load(args.config)
    for _, _, rel in render.outputs(cfg):
        print(rel)
    return 0


def cmd_validate(args):
    cfg = load(args.config)
    print(f"ok: {len(cfg['cards'])} cards, {len(cfg['variants'])} theme variant(s), output {cfg['output']}")
    return 0


def cmd_init(args):
    if args.template not in TEMPLATES:
        return _fail(f"template must be one of: {', '.join(TEMPLATES)}")
    src = os.path.join(ROOT, "examples", f"{args.template}.yml")
    if not os.path.exists(src):
        return _fail(f"template file missing: {src}")
    with open(src, encoding="utf-8") as f:
        text = f.read()
    user = args.user or PLACEHOLDER_USER
    text = text.replace(PLACEHOLDER_USER, user)
    dest = os.path.abspath(args.dir)
    targets = {
        os.path.join(dest, "bento.yml"): text,
        os.path.join(dest, ".github", "workflows", "bento.yml"): WORKFLOW,
    }
    for path, content in targets.items():
        if os.path.exists(path) and not args.force:
            return _fail(f"{os.path.relpath(path)} already exists (use --force to overwrite)")
    for path, content in targets.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print("wrote", os.path.relpath(path))
    print("\nNext: edit bento.yml, run `python -m bento build --demo` to preview, then commit and push.")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="bento", description="Generate a bento-grid SVG for your GitHub README.")
    p.add_argument("--version", action="version", version=f"readme-bento {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="fetch stats and write the SVG(s)")
    b.add_argument("-c", "--config", default="bento.yml")
    b.add_argument("--demo", action="store_true", help="use sample data, no network (good for previews)")
    b.add_argument("--offline", action="store_true", help="no network: use cached stats from the last run")
    b.add_argument("--out-dir", default=None, help="write files here instead of next to the config")
    b.set_defaults(fn=cmd_build)

    o = sub.add_parser("outputs", help="print the files a build writes")
    o.add_argument("-c", "--config", default="bento.yml")
    o.set_defaults(fn=cmd_outputs)

    v = sub.add_parser("validate", help="check a config file")
    v.add_argument("-c", "--config", default="bento.yml")
    v.set_defaults(fn=cmd_validate)

    i = sub.add_parser("init", help="scaffold bento.yml and the GitHub workflow")
    i.add_argument("--user", help="your GitHub username")
    i.add_argument("--template", default="designer", help=f"one of: {', '.join(TEMPLATES)}")
    i.add_argument("--dir", default=".", help="target repository folder (default: current)")
    i.add_argument("--force", action="store_true")
    i.set_defaults(fn=cmd_init)

    args = p.parse_args(argv)
    try:
        return args.fn(args)
    except ConfigError as e:
        return _fail(e)
