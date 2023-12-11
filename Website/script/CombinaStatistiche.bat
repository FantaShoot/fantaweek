SET mypath=%~dp0
echo %mypath:~0,-1%

pip install openpyxl

python.exe script.py