# -*-coding:Utf-8 -*
import sys
import os
import harfang as hg
import inspect
from cx_Freeze import setup, Executable

"""
"scene_menu",
	"scene_00",
	"scene_01",
	"scene_02",
	"scene_03",
	"scene_04_demo",
	"scene_menu",
	"shaders",
	"Sons",
	"sprites",
	"textures",
	"lua_includes",
	"elements_decors",
	"cinematiques",
	"fonts",
"""


# Gather extra runtime dependencies.
def gather_extra_redist():
	path = os.path.dirname(inspect.getfile(hg))
	files = os.listdir(path)

	out = []
	for file in files:
		name, ext = os.path.splitext(file)
		if ext in ['.dll', '.so'] and "Debug" not in name:
			out.append(os.path.join(path, file))

	return out


extra_redist = gather_extra_redist()

path = sys.path + ["D:\\Movida\\make_executables\\dogfight"]

packages = ["hg"]
includes = ["utils"]
includefiles = ["openal32.dll", "assets"] + extra_redist

build_exe_options = {
	"path": path,
	"packages": packages,
	"includes": includes,
	"include_files": includefiles,
	"excludes": ["tkinter"]
}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
	base = "Win32GUI"

setup(name="Dogfight", version="0.1", description="Dogfight executable", options={"build_exe": build_exe_options}, executables=[Executable("main.py", targetName="dogfight.exe")])
