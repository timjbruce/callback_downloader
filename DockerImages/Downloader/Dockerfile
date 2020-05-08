FROM amazonlinux:latest

RUN yum update -y
RUN yum install python3 git -y
RUN pip3 install --upgrade setuptools
RUN pip3 install --upgrade awscli boto3

WORKDIR /var/task
COPY lambda_function.py /var/task
COPY requirements.txt /var/task

RUN pip3 install -r requirements.txt

ENV WORKDIR /var/task

ENTRYPOINT ["python3", "lambda_function.py", "Ref::URI"]
#CMD /bin/bash
