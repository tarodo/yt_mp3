FROM python:alpine

RUN apk add --no-cache \
  ffmpeg \
  tzdata \
  build-base \
  linux-headers

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN apk --update-cache add --virtual build-dependencies gcc libc-dev make \
  && pip install --no-cache-dir -r requirements.txt \
  && apk del build-dependencies

COPY .. /usr/src/app

VOLUME ["/youtube-dl"]

CMD ["python", "main.py"]
