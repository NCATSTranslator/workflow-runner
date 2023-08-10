FROM ghcr.io/translatorsri/renci-python-image:0.2.0

# Add image info
LABEL org.opencontainers.image.source https://github.com/NCATSTranslator/workflow-runner

ENV PYTHONHASHSEED=0

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

# set up entrypoint
ENTRYPOINT ["./main.sh"]
