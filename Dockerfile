FROM python:3.9-slim AS builder

WORKDIR /tmp/

RUN --mount=type=cache,target=/var/cache/apt \
    apt update && \
    apt install git -y && \
    git clone https://github.com/AppDaemon/appdaemon --depth 1

FROM python:3.9-slim AS app

ADD https://files.pythonhosted.org/packages/60/05/1903d433ea96f9a49408e070275cd7c75d95c7920e1a0d3b3d5d60fed124/appdaemon-4.4.2-py3-none-any.whl /tmp/
COPY dist/*.whl /tmp/

RUN --mount=type=cache,target=/root/.cache/pip python -m pip install --verbose /tmp/*.whl

WORKDIR /usr/src/app

COPY --from=builder /tmp/appdaemon/conf ./conf
COPY --from=builder /tmp/appdaemon/dockerStart.sh .

EXPOSE 5050

VOLUME /conf
VOLUME /certs

ENTRYPOINT ["./dockerStart.sh"]
