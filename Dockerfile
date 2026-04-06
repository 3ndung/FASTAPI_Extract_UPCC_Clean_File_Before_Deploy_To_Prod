# Dockerfile Klo dibutuhkan deploy with Docker

FROM python:3.9

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

COPY --chown=user ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY --chown=user . /app

# Copy the templates directory
#COPY --chown=user ./templates /app/templates

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
