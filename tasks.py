from invoke import task, Collection
from invoke.context import Context

import os

import base


icon = lambda v, s, m="tray-margin": base.ids("logo-icon", v, [*s, m])
app = lambda v, s, m="margin": base.ids("logo-app", v, [*s, m])

themed_logos = lambda theme: {
    f"tray-{theme}": icon(theme, ["shape"]),
    f"tray-{theme}-active": icon(theme, ["shape-active", "overlay-active"]),
    f"tray-{theme}-disabled": icon(theme, ["shape", "overlay-disabled"]),
}
themed_symbol = lambda theme, name: {
    f"symbol-{theme}-{name}": base.export(f"symbol-light", [name])
}

logos = {
    **themed_logos("dark"),
    **themed_logos("light"),
    "logo-app-mac": app("mac", ["zinc", "shape-shade"]),
    "logo-app-circle": app("circle", ["zinc", "shape-shade"]),
    "logo-app-full": app("square", ["zinc", "shape"]),
    "logo-app-full-large": app("square", ["zinc", "shape"], "margin-large"),
}
invertable_light_symbols = {
    **themed_symbol("light", "patreon"),
    **themed_symbol("light", "blitz"),
    **themed_symbol("light", "open"),
    **themed_symbol("light", "info"),
    **themed_symbol("light", "close"),
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
        inkscape.export_all(base.svg("logo"), logos)
        to_invert = inkscape.export_all(
            base.svg("symbols"), invertable_light_symbols
        )
    for path in to_invert:
        base.invert(path, ("light", "dark"))


namespace = Collection(base.clean, icos, export)
