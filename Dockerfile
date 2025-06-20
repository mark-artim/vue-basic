FROM node:18-bullseye

# Install Python
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    apt-get clean

WORKDIR /app

# Copy and install Node dependencies
COPY auth-backend/package*.json ./auth-backend/
RUN cd auth-backend && npm install && npm install concurrently

# Copy both backends
COPY auth-backend/ ./auth-backend/
COPY backend/ ./backend/

# Install Python dependencies
COPY backend/requirements.txt ./backend/
RUN pip3 install -r backend/requirements.txt

# Expose ports
EXPOSE 3001 8000

# Run both Node and Python servers using concurrently
CMD ["npx", "concurrently", "--kill-others", "--names", "node,py", \
  "node auth-backend/server.js", \
  "python3 backend/main.py"]
