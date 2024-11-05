from invoke import task, Collection
from invoke.context import Context

import base


icon = lambda v, s, m="tray-margin": base.ids("logo-icon", v, [*s, m])
app = lambda v, s, m="margin": base.ids("logo-app", v, [*s, m])

themed_tray_icons = lambda theme: {
    f"tray-{theme}": icon(theme, ["shape"]),
    f"tray-{theme}-active": icon(theme, ["shape-active", "overlay-active"]),
    f"tray-{theme}-active-paused": icon(
        theme, ["shape-active", "overlay-active-paused"]
    ),
    f"tray-{theme}-disabled": icon(theme, ["shape", "overlay-disabled"]),
}
themed_symbol = lambda theme, name: {
    f"symbol-{theme}-{name}": base.export(f"symbol-light", [name])
}

logos = {
    **themed_tray_icons("dark"),
    **themed_tray_icons("light"),
    "logo-app-mac": app("mac", ["slate", "shape-shade"]),
    "logo-app-circle": app("circle", ["slate", "shape-shade"]),
    "logo-app-full": app("square", ["slate", "shape"]),
    "logo-app-full-large": app("square", ["slate", "shape"], "margin-large"),
    "logo-discord-server": app(
        "square", ["slate-gradient", "long-shadow", "shape"], "margin"
    ),
}
symbols = {
    "symbol-status-playing": base.export("status", ["playing"]),
    "symbol-status-paused": base.export("status", ["paused"]),
}
invertable_light_symbols = {
    **themed_symbol("light", "patreon"),
    **themed_symbol("light", "donate"),
    **themed_symbol("light", "blitz"),
    **themed_symbol("light", "open"),
    **themed_symbol("light", "info"),
    **themed_symbol("light", "close"),
}
installer_graphics = {
    # https://nsis.sourceforge.io/Docs/Modern%20UI/Readme.html#toggle_inwf
    "installer-nsis-wizard": base.export(
        "installer",
        ["nsis-wizard", "nsis-wizard-box"],
        width=164,
        height=314,
    ),
    # https://nsis.sourceforge.io/Docs/Modern%20UI/Readme.html#toggle_ingen
    "installer-nsis-header": base.export(
        "installer",
        ["nsis-header", "nsis-header-box"],
        width=150,
        height=57,
    ),
    # 1200x730, 144 = 72 * 2 DPI
    "installer-dmg": base.export(
        "installer",
        ["dmg", "dmg-box"],
        width=1200,
        height=730,
        dpi=144,
    ),
}
icns_convert_matching = ["^logo-app-circle", "^logo-app-mac"]
ico_convert_matching = ["^logo-", "^tray-", "^symbol-"]
bmp_convert_matching = ["nsis-wizard", "nsis-header"]


@task
def icos(c: Context):
    for file in base.files_matching(base.OUT, ico_convert_matching):
        base.to_ico(file, f"{base.OUT}/ico")


@task
def icns(c: Context):
    for file in base.files_matching(base.OUT, icns_convert_matching):
        base.to_icns(file, f"{base.OUT}/icns")


@task
def nsis_bmps(c: Context):
    for file in base.files_matching(base.OUT, bmp_convert_matching):
        # NSIS requires BMP3: https://stackoverflow.com/a/28768495/6748004
        base.to_nsis_bmp(file, f"{base.OUT}/bmp")


@task(pre=[base.prepare], post=[icos, icns])
def export_logos(c: Context):
    with base.Inkscape(c) as inkscape:
        inkscape.export_all(base.svg("logo"), logos)


@task(pre=[base.prepare], post=[icos])
def export_symbols(c: Context):
    with base.Inkscape(c) as inkscape:
        inkscape.export_all(base.svg("symbols"), symbols)
        res = inkscape.export_all(base.svg("symbols"), invertable_light_symbols)
    for path in res.values():
        base.invert(path, ("light", "dark"))


@task(pre=[base.prepare], post=[nsis_bmps])
def export_installers(c: Context):
    with base.Inkscape(c) as inkscape:
        res = inkscape.export_all(base.svg("installer"), installer_graphics)
    # Inkscape does not apply the DPI for some reason
    key = "installer-dmg"
    base.change_dpi(res[key], installer_graphics[key].dpi)


@task(pre=[base.prepare], post=[icos, icns, nsis_bmps])
def export(c: Context):
    export_logos(c)
    export_symbols(c)
    export_installers(c)


namespace = Collection(
    base.clean, export, export_logos, export_symbols, export_installers
)
