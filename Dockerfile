FROM python:3.12.0

WORKDIR /usr/src/app
RUN chmod 777 /usr/src/app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python3", "main.py"]