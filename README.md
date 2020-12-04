# fluffy-carnival

## Update 2020/12/04

This repo is using mysql and mysql's drivers and there is still no async mysql driver supported by sqlalchemy. Although the code works but it's blocking.

However, the general idea of having multiple concurrent select queries on single connection is fine.

Checkout https://github.com/sqlalchemy/sqlalchemy/issues/5743

## Setup

Create a .env file contains `SQLALCHEMY_DATABASE_URI` connection string.

Can set to `pymysql` and `mariadbconnector` driver. Ex:

```
SQLALCHEMY_DATABASE_URI=mysql+mariadbconnector://user:pwd@127.0.0.1:3306/db?charset=utf8
```

## Start servers

### Flask app

```sh
gunicorn 'todoapp.main:create_flask_app()' -w 4 --threads 12 --preload
```

### FastAPI app

- with gunicorn workers

```sh
PRELOAD=1 gunicorn 'todoapp.main:create_fastapi_app()' -w 4 -k uvicorn.workers.UvicornWorker --preload
```

- single worker

```sh
uvicorn todoapp.main:fastapiapp
```

### Benchmark

```sh
ab -n 3000 -c 1000 localhost:8000/users
```
