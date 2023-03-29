FROM renciorg/renci-python-image:v0.0.1

WORKDIR /app

# make sure all is writeable for the nru USER later on
RUN chmod -R 777 .

# set up requirements
ADD requirements-lock.txt .
RUN pip install -r requirements-lock.txt

# switch to the non-root user (nru). defined in the base image
USER nru

# set up source
ADD . .
COPY .env.sample .env

# set up entrypoint
ENTRYPOINT ["./main.sh"]
