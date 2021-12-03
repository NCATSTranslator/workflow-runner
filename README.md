# Workflow runner

## deployment

### Live service
Available at: https://translator-workflow-runner.renci.org/docs

### native

```bash
./main.sh --port <PORT>
```

The default port is 3084.

### docker

```bash
docker build . -t workflow_runner
docker run --name workflow_runner --rm -p <PORT>:3084 -it workflow_runner
```

### docker-compose

```bash
PORT=<PORT> docker-compose up --build
```

The "docker-compose" option requires either a) an environment variable called `PORT`, or b) a `.env` file containing a definition for `PORT`.

### kubernetes (minikube)

```bash
eval $(minikube -p minikube docker-env)  # point session to minikube's docker daemon
docker build . -t workflow_runner  # build image
kubectl create -f k8s-deployment.yml  # references local image
kubectl port-forward service/workflow-runner <PORT>:7092  # forward to port of your choice
```

Access Swagger UI at `http://localhost:<PORT>/docs`.

## configuration

Environment variables have the following effects:

* `OPENAPI_SERVER_URL`: [A URL to the target host.](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#server-object) Important for generating a portable OpenAPI schema.

## Local Development

### Management Script

The codebase comes with a zero-dependency python management script that can be used to automate basic local development tasks. Make sure you have docker and docker-compose installed and then run:

```bash
./manage.py dev # starts server accessible at 5781
./manage.py test # run tests
./manage.py lock # update lockfile if requirements.txt has changed
```

### Without Management Script

Testing:

```bash
python -m pytest tests/ --cov app --cov-report term-missing
```
