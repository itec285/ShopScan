#!/bin/bash

# This script is designed to prepare a (Ubuntu 16.04.3 at the time of this writing) system for a shop and scan server
#  see https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-uwsgi-and-nginx-on-ubuntu-16-04 for further details
# Feb 2018 IL

sudo apt-get update
sudo apt install -y python3-pip python3-dev nginx boxes
sudo pip3 install virtualenv
cd ~
mkdir shopscanserver
cd shopscanserver
virtualenv myprojectenv

#Prepare the virtual environment
source myprojectenv/bin/activate
pip install uwsgi flask
pip install flask-restful


cp ~/shopscan/ShopAndScanServer.py .
cp ~/shopscan/ShopAndScan.db .

cp ~/shopscan/addons/wsgi.py .
cp ~/shopscan/addons/shopscanserver.ini .

echo -e "\n\tFirst test, manually with python\n\t" | boxes -d stone
read -rsp $'Press any key to continue...\n' -n 1 key
python ShopAndScanServer.py 

##Now, test uwsgi##
echo
echo -e "\n\tSecond test, manually with uwsgi\n\t" | boxes -d stone
read -rsp $'Press any key to continue...\n' -n 1 key
uwsgi --socket 0.0.0.0:5000 --protocol=http -w wsgi:app

##If everything works to this point, we are done with test environment#
deactivate

#Create our service
cd ~/as-keyserver
sudo cp addons/myproject.service /etc/systemd/system/
sudo systemctl start myproject
sudo systemctl enable myproject

#Note - keyserver file contains the server address so if it changes you need to update this file
cd ~/as-keyserver
sudo cp addons/keyserver /etc/nginx/sites-available/

sudo ln -s /etc/nginx/sites-available/keyserver /etc/nginx/sites-enabled/

echo -e "Check nginx for errors " | boxes -d stone
sudo nginx -t

sudo systemctl restart nginx

#Allow NGINX and other important traffic through the firewall, then enable it
sudo ufw allow openssh
sudo ufw allow 'Nginx Full'
sudo ufw enable

#Setup Lets Encrypt - see https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-16-04
sudo add-apt-repository -y ppa:certbot/certbot
sudo apt-get update
sudo apt install -y python-certbot-nginx

#Show final message
echo -e "\n\t            YOU ARE DONE EXCEPT FOR ONE THING :-)\n\t\n\trun $ sudo certbot --nginx -d keys.auto-star.com \n\t\n\t Thanks for everything.  Regards, Ivan. ivanl@auto-star.com" | boxes -d dog
