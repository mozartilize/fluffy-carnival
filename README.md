# fluffy-carnival

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
