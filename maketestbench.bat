del /S /F /q build\testbench\*.*
del /S /F /Q dist\*.*
pyinstaller --onefile  --version-file=testbenchversion.txt testbench.py
