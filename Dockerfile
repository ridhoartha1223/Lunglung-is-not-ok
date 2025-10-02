FROM node:20-slim

# Install Python + pip
RUN apt-get update && apt-get install -y python3 python3-pip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install lottie2tgs global
RUN npm install -g lottie2tgs

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "main.py"]
