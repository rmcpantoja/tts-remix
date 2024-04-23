# create Windows build from CX_Freece
import sys
from cx_Freeze import setup, Executable 
base = None
if sys.platform == 'win32':
    base = 'Win32GUI'

build_exe_options = dict(
	build_exe="dist",
	optimize=1,
	include_msvcr=True,
	)

executables = [
    Executable('tts_remix.py', base=base)
]

setup(name="TTSRemix",
      version="0.1",
      description="Use various neural Text-To-Speech models in one",
      options = {"build_exe": build_exe_options},
      executables=executables
      )
