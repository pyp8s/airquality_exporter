FROM python:3.10-alpine

ARG APP_VERSION=0.0.0

LABEL org.opencontainers.image.title="airquality-exporter"
LABEL org.opencontainers.image.description="Air Quality Exporter"
LABEL org.opencontainers.image.authors="Pavel Kim <hello@pavelkim.com>"
LABEL org.opencontainers.image.version="${APP_VERSION}"

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBUG 0

WORKDIR /app

COPY ./entrypoint.sh .
COPY ./.version .

COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY ./airquality .

ENTRYPOINT [ "/app/entrypoint.sh" ]
