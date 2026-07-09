FROM python:3.11-slim

# Install system dependencies for OpenCV and PaddleOCR
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# RUN pip install dlib==19.9.0
LABEL version="For FastApi Server"

EXPOSE 8001

WORKDIR /usr/app

COPY requirements.txt ./
RUN pip install --upgrade pip

# Install dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code
COPY . .

CMD [ "python3", "start_server.py" ]
