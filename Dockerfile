# build stage
FROM python:3.11-slim AS builder

# install PDM
RUN pip install -U pip setuptools wheel pdm -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install pdm -i https://pypi.tuna.tsinghua.edu.cn/simple

# copy files
COPY pyproject.toml pdm.lock /project/
COPY server/ /project/server
COPY client/ /project/client

# install dependencies and project into the local packages directory
WORKDIR /project
RUN mkdir __pypackages__  \
    && pdm config python.use_venv false  \
    && pdm install --prod --no-lock --no-editable  \
    && pdm config pypi.url https://pypi.tuna.tsinghua.edu.cn/simple


# run stage
FROM python:3.11-slim

# retrieve packages from build stage
ENV PYTHONPATH=/project/pkgs
COPY --from=builder /project/__pypackages__/3.11/lib /project/pkgs
COPY --from=builder /project/__pypackages__/3.11/bin /usr/local/bin
COPY --from=builder /project/server /project/server
COPY --from=builder /project/client /project/client

# expose port
EXPOSE 5000

# set command
CMD ["python", "-m", "server.app" ]
