from invoke import task
from invoke.context import Context
from invoke.runners import Promise, Result

import shutil
import pathlib
import os
import re
from typing import Callable
from contextlib import contextmanager

from PIL import Image, ImageFile, ImageOps


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


class ExportInfo:
    ids: str
    width: int | None
    height: int | None
    dpi: int | None

    def __init__(
        self,
        ids: str,
        *,
        width: int = None,
        height: int = None,
        dpi: int = None,
    ):
        self.ids = ids
        self.width = width
        self.height = height
        self.dpi = dpi


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
        self, svg: str, name: str, info: ExportInfo, ext: str = "png"
    ) -> str:
        path = out(name, ext)
        params = []
        if info.width is not None:
            params.append(f"-w {info.width}")
        if info.height is not None:
            params.append(f"-h {info.height}")
        if info.width is None and info.height is None:
            params = [f"-h {SIZE}"]
        if info.dpi is not None:
            params.append(f"-d {info.dpi}")
        params = " ".join(params)
        command = f"inkscape -o {path} -i {info.ids} -j {params} {svg}"
        promise: Promise = self.context.run(command, asynchronous=True)
        self.promises.append(promise)
        return path

    def export_all(
        self, svg: str, name_to_ids: dict[str, str]
    ) -> dict[str, str]:
        return {
            name: self.export(svg, name, ids)
            for name, ids in name_to_ids.items()
        }


@contextmanager
def convert(
    image_path,
    target_directory,
    ext,
):
    path = pathlib.Path(image_path)
    dest = os.path.join(target_directory, f"{path.stem}.{ext}")
    pathlib.Path(target_directory).mkdir(parents=True, exist_ok=True)

    class Data:
        def __init__(self, image: ImageFile.ImageFile):
            self.image = image

    print(f"converting: {image_path} -> {dest}")
    image = Image.open(image_path)
    info = Data(image)
    yield info
    info.image.save(dest)


def to_ico(image_path, target_directory):
    with convert(image_path, target_directory, "ico"):
        pass


def to_nsis_bmp(image_path, target_directory):
    with convert(image_path, target_directory, "bmp") as out:
        out.image = out.image.convert("RGB")


def export(
    base_id, suffixes, *, width: int = None, height: int = None, dpi: int = None
):
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
    return ExportInfo(";".join(ids), width=width, height=height, dpi=dpi)


def ids(
    prefix: str,
    variant: str,
    suffixes: list[str] = [],
    *,
    width: int = None,
    height: int = None,
    dpi: int = None,
):
    return export(
        f"{prefix}-{variant}", [*suffixes], width=width, height=height, dpi=dpi
    )


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


def change_dpi(image_path: str, dpi: int):
    image = Image.open(image_path)
    image.save(image_path, dpi=(dpi, dpi))


def files_matching(dir: str, patterns: list[str], ext: str = EXT):
    for file in os.listdir(dir):
        name, ext = os.path.splitext(file)
        if not ext.lower().endswith(ext.lower()):
            continue
        for pattern in patterns:
            if re.search(pattern, name):
                yield os.path.join(dir, file)
