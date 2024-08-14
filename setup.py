import sys, os
from cx_Freeze import setup, Executable

files = ["icon.ico"]

target = Executable(
    script="gui.pyw",
    base = "Win32GUI",
    icon = "icon.ico"
)


setup(
    name = "XFBIN Texture Tool",
    version = "1.0",
    description = "A GUI tool to add,removed and replace textures in XFBIN files",
    author = "Al-Hydra",
    options = {"build_exe" : {"include_files" : files}},
    executables = [target]
)