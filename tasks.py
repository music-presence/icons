from invoke import task, Collection
from invoke.context import Context

import os

import base


def ids(prefix: str, variant: str, suffixes: list[str] = []):
    return base.export(f"{prefix}-{variant}", [*suffixes])


icon = lambda v, s: ids("logo-icon", v, [*s, "tray-margin"])
app = lambda v, s: ids("logo-app", v, [*s, "margin"])


themed_logos = lambda theme: {
    f"tray-{theme}": icon(theme, ["shape"]),
    f"tray-{theme}-active": icon(theme, ["shape-active", "overlay-active"]),
    f"tray-{theme}-disabled": icon(theme, ["shape", "overlay-disabled"]),
}
logos = {
    **themed_logos("dark"),
    **themed_logos("light"),
    "logo-app-mac": app("mac", ["zinc", "shape"]),
    "logo-app-circle": app("circle", ["zinc", "shape"]),
    "logo-app-full": app("square", ["zinc", "shape"]),
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
