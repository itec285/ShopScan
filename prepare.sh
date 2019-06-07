sudo apt-get update
mkdir ~/shopscanserver
cd ~/shopscanserver
sudo apt-get install python3-venv
sudo apt-get install sqlite3
python3 -m venv rest-api
rest-api/bin/pip install wheel
rest-api/bin/pip install flask
rest-api/bin/pip install flask-restful
