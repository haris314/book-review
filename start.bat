cd .Batches
start /min sass.bat
start /min start_flask.bat


cd..
call code application.py

cd templates
call code home.html

cd..
cd static/styles
call code mainStyle.scss

cd..
cd.. 

cmd /k