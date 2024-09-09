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

SIZE = 512


@task
def clean(c: Context):
    shutil.rmtree(OUT, True)
    shutil.rmtree(BUILD, True)


@task(pre=[clean])
def prepare(c: Context):
    pathlib.Path(OUT).mkdir(parents=True, exist_ok=False)
    pathlib.Path(BUILD).mkdir(parents=True, exist_ok=False)
    with open(os.path.join(OUT, "size"), "w") as f:
        f.write(str(SIZE))


def out(name, ext):
    return f"{OUT}/{name}.{ext}"


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

    def export(
        self, svg: str, name: str, export_ids: str, ext: str = "png"
    ) -> Promise:
        path = out(name, ext)
        command = f"inkscape -o {path} -i {export_ids} -j -h {SIZE} {svg}"
        promise: Promise = self.context.run(command, asynchronous=True)
        self.promises.append(promise)
        return promise

    def export_all(self, svg: str, name_to_ids: dict[str, str]) -> None:
        for name, ids in name_to_ids.items():
            self.export(svg, name, ids)


def to_ico(src, dir=None):
    path = pathlib.Path(src)
    if dir is None:
        dir = path.parent
    dest = os.path.join(dir, path.stem + ".ico")
    print(f"converting: {src} -> {dest}")
    image = Image.open(src)
    pathlib.Path(dir).mkdir(parents=True, exist_ok=True)
    image.save(dest)


def export(base_id, suffixes):
    """Constructs a list of IDs meant to be passed to Inkscape's CLI program
    after the -i or --export-id command line flag.
    The last ID will dictate the bounding box of the output.
    """
    if len(base_id) == 0:
        raise ValueError("the base ID cannot be empty")
    if len(suffixes) == 0:
        raise ValueError("there must be at least one suffix")
    for s in suffixes:
        if len(s) == 0:
            raise ValueError("suffixes cannot be empty")
    ids = [base_id + "-" + s for s in suffixes]
    return ";".join(ids)
