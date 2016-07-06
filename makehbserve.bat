del /S /F /q build\testbench\*.*
del /S /F /Q dist\*.*
pyinstaller --onefile  --version-file=hbserveversion.txt hbserve.py