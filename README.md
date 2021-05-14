# Workflow runner

## deployment

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

## testing

```bash
python -m pytest tests/ --cov app --cov-report term-missing
```