FROM python:3.9

WORKDIR /app

# set up requirements
ADD requirements-lock.txt .
RUN pip install -r requirements-lock.txt

# set up source
ADD . .

# set up entrypoint
ENTRYPOINT ["./main.sh"]
