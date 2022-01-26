FROM python:3.9

WORKDIR /app

# set up requirements
ADD requirements-lock.txt .
RUN pip install -r requirements-lock.txt

#create and run nonroot user
RUN useradd -u 8877 nonroot
RUN chown -R 8877 .
USER nonroot

# set up source
ADD . .

# set up entrypoint
ENTRYPOINT ["./main.sh"]
