from invoke import task
from invoke.context import Context
from invoke.runners import Promise, Result

import shutil
import pathlib
import os

from PIL import Image, ImageOps


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


def svg(name):
    return f"{SRC}/{name}.svg"


def ids(prefix: str, variant: str, suffixes: list[str] = []):
    return export(f"{prefix}-{variant}", [*suffixes])


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
    ) -> str:
        path = out(name, ext)
        command = f"inkscape -o {path} -i {export_ids} -j -h {SIZE} {svg}"
        promise: Promise = self.context.run(command, asynchronous=True)
        self.promises.append(promise)
        return path

    def export_all(self, svg: str, name_to_ids: dict[str, str]) -> list[str]:
        return [
            self.export(svg, name, ids) for name, ids in name_to_ids.items()
        ]


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


def invert(image_path: str, replace: tuple[str, str]):
    dirname = os.path.dirname(image_path)
    basename = os.path.basename(image_path)
    if not replace[0] in basename:
        raise ValueError("replace string must be in image filename")
    image = Image.open(image_path)
    if image.mode == "RGBA":
        r1, g1, b1, alpha = image.split()
        rgb_image = Image.merge("RGB", (r1, g1, b1))
        inverted_image = ImageOps.invert(rgb_image)
        r2, g2, b2 = inverted_image.split()
        result = Image.merge("RGBA", (r2, g2, b2, alpha))
    else:
        result = ImageOps.invert(image)
    new_name = basename.replace(replace[0], replace[1])
    result.save(os.path.join(dirname, new_name))
