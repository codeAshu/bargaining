`docker build . -t bargain`

`docker run -p 8080:8080 bargain`


### Without Docker

Create Virtual Env
`virtualenv env_bargain`

Activate the env
`source env_bargain/bin/activate`

Install dependecies
`pip install -r requirements.txt`

Start Flask Server
`python main.py`

On browser check `http://localhost:8080`
