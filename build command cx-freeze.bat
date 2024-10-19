python setup.py build

//rename the folder and the exe
cd build/
ren "exe.win32-3.6" "XFBIN Texture Tool"
cd 
ren "gui.exe" "XFBIN Texture Tool.exe"

//delete the icon file
del "icon.ico"