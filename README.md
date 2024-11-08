# Britannica Dictionary API 

[britannica.com/dictionary](https://www.britannica.com/dictionary)

```
pacman -S memcached
systemctl enable memcached@11211 
systemctl start memcached@11211 
```

###---
```
sudo pacman -S python python-pip nginx
```

```
sudo useradd -r -s /bin/false dictionary_user
```

```
sudo mkdir -p /opt/dictionary-api
sudo chown dictionary_user:dictionary_user /opt/dictionary-api
```

```
sudo cp app.py /opt/dictionary-api/
sudo cp wsgi.py /opt/dictionary-api/ 
sudo cp requirements.txt /opt/dictionary-api/ 
```

```
cd /opt/dictionary-api
sudo -u dictionary_user python -m venv venv
sudo -u dictionary_user venv/bin/pip install -r requirements.txt
```

```
sudo cp dictionary-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable dictionary-api
sudo systemctl start dictionary-api
```

```
sudo mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled
sudo cp dictionary-api /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/dictionary-api /etc/nginx/sites-enabled/
sudo nginx -t  # Check config
sudo systemctl enable nginx
sudo systemctl restart nginx
```
