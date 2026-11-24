#!/usr/bin/env python3
"""Builds the static web configurator into _site/ (what GitHub Pages serves).

    python tools/build_site.py          # then: python -m http.server -d _site 8766

The engine itself is copied as-is: the page runs the very same Python code as the Action, through Pyodide.
"""
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "_site")


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(os.path.join(ROOT, "site"), OUT, ignore=shutil.ignore_patterns("webapi.py"))

    manifest = []
    py = os.path.join(OUT, "py")
    for base, dirs, files in os.walk(os.path.join(ROOT, "bento")):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in files:
            if name.endswith(".pyc"):
                continue
            src = os.path.join(base, name)
            rel = os.path.relpath(src, ROOT).replace(os.sep, "/")
            dst = os.path.join(py, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
            manifest.append(rel)
    shutil.copyfile(os.path.join(ROOT, "site", "webapi.py"), os.path.join(py, "webapi.py"))
    manifest.append("webapi.py")
    with open(os.path.join(py, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(sorted(manifest), f)

    presets = os.path.join(OUT, "presets")
    os.makedirs(presets)
    names = []
    for name in sorted(os.listdir(os.path.join(ROOT, "examples"))):
        if name.endswith(".yml"):
            shutil.copyfile(os.path.join(ROOT, "examples", name), os.path.join(presets, name))
            names.append(name[:-4])
    shutil.copyfile(os.path.join(ROOT, "bento", "data", "default.yml"), os.path.join(presets, "profile.yml"))
    names.insert(0, "profile")
    with open(os.path.join(presets, "index.json"), "w", encoding="utf-8") as f:
        json.dump(names, f)
    print("built", os.path.relpath(OUT, ROOT), "-", len(manifest), "python files,", len(names), "presets")


if __name__ == "__main__":
    sys.exit(main())
