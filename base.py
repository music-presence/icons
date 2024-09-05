from invoke import task
from invoke.context import Context
from invoke.runners import Promise, Result

import shutil
import pathlib
import os

from PIL import Image


# Inkscape CLI documentation: https://inkscape.org/doc/inkscape-man.html

SRC = "src"
OUT = "dist"
BUILD = "build"
EXT = "png"

PREFIX = "musicpresence"
SIZE = 512


@task
def clean(c: Context):
    shutil.rmtree(OUT, True)
    shutil.rmtree(BUILD, True)


@task(pre=[clean])
def prepare(c: Context):
    pathlib.Path(OUT).mkdir(parents=True, exist_ok=False)
    pathlib.Path(BUILD).mkdir(parents=True, exist_ok=False)


def out(id, ext):
    return f"{OUT}/{PREFIX}-{id}.{ext}"


class Inkscape:
    def __init__(self, context: Context):
        self.context = context
        self.promises: list[Promise] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print(f"waiting for {len(self.promises)} inkscape commands to exit")
        for p in self.promises:
            r: Result = p.join()
            if "was not found in the document" in r.stderr:
                raise Exception(r.stderr)

    def export(self, svg: str, id: str, ext: str = "png") -> Promise:
        command = f"inkscape -o {out(id, ext)} -i {id} -j -h {SIZE} {svg}"
        promise: Promise = self.context.run(command, asynchronous=True)
        self.promises.append(promise)
        return promise

    def export_all(self, svg: str, ids: list[str]) -> None:
        for id in ids:
            self.export(svg, id)


def to_ico(src, dir=None):
    path = pathlib.Path(src)
    if dir is None:
        dir = path.parent
    dest = os.path.join(dir, path.stem + ".ico")
    print(f"converting: {src} -> {dest}")
    image = Image.open(src)
    pathlib.Path(dir).mkdir(parents=True, exist_ok=True)
    image.save(dest)
