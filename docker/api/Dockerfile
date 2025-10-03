FROM python:3.13-slim

# INFO: Create non-root user
RUN groupadd -r app_user && \
    useradd -r -g app_user app_user

# INFO: Set environment variables
ENV APP_HOST=0.0.0.0
ENV APP_PORT=8000
ENV APP_LOG_LEVEL=info
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# INFO: Set the working directory
WORKDIR /app

# INFO: Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        openssl \
        curl \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# INFO: Install poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry

RUN python -m venv "/opt/venv" \
    && . "/opt/venv/bin/activate" \
    && pip install --upgrade --no-cache-dir pip setuptools

# INFO: Install dependencies
COPY pyproject.toml poetry.lock /app/
RUN poetry config virtualenvs.create false \
    && poetry install --without dev

# INFO: Clean up
RUN apt-get autoremove && \
    rm -fr /var/lib/apt/lists/{apt,dpkg,cache,log} /tmp/* /var/tmp/*

# INFO: Copy the application
COPY src/ /app/src/
COPY app_start.sh /app/

# INFO: Change ownership of the application
RUN chown -R app_user /app
USER app_user

# INFO: Run the application
EXPOSE ${APP_PORT}
RUN chmod a+x /app/app_start.sh

CMD ["/app/app_start.sh"]
