# Icons for Music Presence

This repository contains logos, icons and symbols for Music Presence,
to be used within the application and for media and graphics.

- `src` contains icon sources in Inkscape SVG format
- `dist` contains exported icons

## Init

```
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -r requirements.txt
invoke --list
```

## Export

```
invoke export
```

## Guide

Elements that are referenced by the build script (`tasks.py`)
get specific, unique IDs.
The ID is constructed by concatenating Inkscape layer, group and subgroup names,
up until the name of the group which is supposed to be referenced,
separated by dashes (`-`).

E.g. the "shape" for the "dark" "icon" variant of the "logo",
which is located in `src/logo.svg` under the "path" `logo/icon/dark/shape`,
i.e. layer `logo` and group path `icon/dark/shape`,
is supposed to be named `logo-icon-dark-shape`.

This name can be set in the "Object properties" tab of Inkscape
and must then be applied using the "Set" button at the bottom
(otherwise the change is not saved).

IDs can then be reference in the Inkscape CLI program with the `-i` parameter,
by naming each ID for an export image, separated by semicolons,
e.g. `logo-icon-dark-shape;logo-icon-dark-tray-margin`
to export the tray icon variant of the logo.
Note that the last ID listed here dictates which bounding box is used.
With the example the tray margin clips the output
with a bit of padding around the shape,
using the bounding box of `logo-icon-dark-tray-margin`.
If the IDs were swapped, the output would not have any padding
because the bounding box of `logo-icon-dark-shape` would be used.

Layers and groups that are referenced by the build script
must be set to visible (not hidden by clicking the eye icon),
otherwise they will not appear in an export.
This is easy to forget when disabling certain groups
while working on another.

Export file names that contain either `-dark` or `-light`
are treated as icons for the respective theme ("dark" or "light").
File names must not start with `dark-...` or `light-...`.

All icons should be exported as 512x512 PNG images
and there must be a `size` file in the root export directory (`dist`)
which contains the size of exported PNG images.
All exported images must have the same size.
