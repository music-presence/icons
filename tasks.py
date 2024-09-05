from invoke import task, Collection
from invoke.context import Context

import os

import base


logos = [
    "logo-simple-light",
    "logo-simple-dark",
    "logo-icon-light-tray",
    "logo-icon-light",
    "logo-icon-dark-tray",
    "logo-icon-dark",
]


@task
def icos(c: Context):
    for dir, _, files in os.walk(base.OUT):
        for file in files:
            ext = os.path.splitext(file)[-1]
            if ext.lower().endswith(base.EXT.lower()):
                base.to_ico(os.path.join(dir, file), "dist/ico")


@task(pre=[base.prepare], post=[icos])
def export(c: Context):
    with base.Inkscape(c) as inkscape:
        inkscape.export_all(f"{base.SRC}/logo.svg", logos)


namespace = Collection(base.clean, icos, export)
