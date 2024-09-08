from invoke import task, Collection
from invoke.context import Context

import os

import base


def tray(theme: str, suffixes: list[str] = []):
    return base.export(f"logo-icon-{theme}", [*suffixes, "tray-margin"])


themed_logos = lambda theme: {
    f"tray-{theme}": tray(theme, ["shape"]),
    f"tray-{theme}-active": tray(theme, ["shape-active", "overlay-active"]),
    f"tray-{theme}-disabled": tray(theme, ["shape", "overlay-disabled"]),
}
logos = {
    **themed_logos("dark"),
    **themed_logos("light"),
}


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
