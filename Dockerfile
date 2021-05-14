FROM python:3.9.1-buster

# set up requirements
ADD ./requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt

# set up source
ADD ./app ./app
ADD ./main.sh ./main.sh

# set up entrypoint
ENTRYPOINT ["./main.sh"]