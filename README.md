# Viperidae API
API and main application for viperidae

Main site --> [`viperidae.app`](https://viperidae.app) : [`viperidae-site`](https://github.com/apt-helion/viperidae-site)

Developer docs/api --> [`developer.viperidae.app`](https://developer.viperidae.app) : [`viperidae-developers`](https://github.com/apt-helion/viperidae-developers)

## Setting up on a development environment 
```
# Make sure MariaDB and MongoDB are installed

# Clone it
git clone https://github.com/apt-helion/viperidae2.0
cd viperidae2.0

# Using the python virtual environment module (venv), create a python
# environment into "./env"
python3.6 -m venv env

# Setup your shell for this project
source env/bin/activate

# Install requirements for this project
pip install -r requirements.txt

# Start the server
./main.py
```

Go to `0.0.0.0:8080` and you should be able to see the message `api.viperidae.app is up`.

## Testing the api
### GET requests
If your web browser allows for viewing JSON, just put the requests into there. e.g.
```
0.0.0.0:8080/index?u=https://blog.justinduch.com
```

### POST requests
Use the script or cURL. e.g.
```
curl --headers "Authorization: Basic {token}" --data "q=test" 0.0.0.0:8080/v1/search
```
Don't acutally use this... just use the scripts in `tests/`.

