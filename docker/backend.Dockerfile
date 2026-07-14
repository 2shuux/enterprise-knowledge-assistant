# ---- build stage: install deps into a clean prefix ----
FROM python:3.12-slim AS build
WORKDIR /app
COPY apps/backend/requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# ---- runtime stage: slim image, non-root user ----
FROM python:3.12-slim
RUN useradd --create-home appuser
WORKDIR /app
COPY --from=build /install /usr/local
COPY apps/backend/src/ ./src/
ENV PYTHONPATH=/app/src PYTHONUNBUFFERED=1
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
