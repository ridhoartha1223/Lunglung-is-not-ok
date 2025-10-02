FROM node:20-slim AS node_builder
RUN npm install -g lottie2tgs

FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y curl \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=node_builder /usr/local/bin/lottie2tgs /usr/local/bin/
COPY . .

CMD ["python", "main.py"]
