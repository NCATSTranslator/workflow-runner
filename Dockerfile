FROM python:3.9

WORKDIR /app

#create and run nonroot user
RUN useradd -u 8877 nonroot
USER nonroot

# set up requirements
ADD requirements-lock.txt .
RUN pip install -r requirements-lock.txt

# set up source
ADD . .

# set up entrypoint
ENTRYPOINT ["./main.sh"]
