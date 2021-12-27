FROM python:alpine

ADD requirements.txt /

RUN apk add --no-cache gcc libc-dev linux-headers zlib-dev jpeg-dev \
 && pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r /requirements.txt \
 && rm /requirements.txt

ADD app /app/
WORKDIR /app

EXPOSE 3000/tcp

CMD ["uwsgi", "--ini", "uwsgi.ini"]
