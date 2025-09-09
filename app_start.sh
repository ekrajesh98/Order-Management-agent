#!/bin/bash
set -e

if [ "$APP_ENVIRONMENT" = "local" ]; then
        echo "Starting application in local environment without OpenTelemetry..."
        uvicorn src.main:app \
                --host "$APP_HOST" \
                --port "$APP_PORT" \
                --log-level "$APP_LOG_LEVEL" \
                --reload
else
        echo "Starting application with OpenTelemetry instrumentation..."
        exec opentelemetry-instrument \
                --traces_exporter=otlp \
                --logs_exporter=otlp \
                --metrics_exporter=otlp \
                uvicorn src.main:app \
                --host "$APP_HOST" \
                --port "$APP_PORT" \
                --log-level "$APP_LOG_LEVEL"
fi