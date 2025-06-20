FROM node:18-bullseye

RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    apt-get clean

WORKDIR /app

COPY auth-backend/package*.json ./auth-backend/
RUN cd auth-backend && npm install

COPY auth-backend/ ./auth-backend/
COPY backend/ ./backend/

COPY backend/requirements.txt ./backend/
RUN pip3 install -r backend/requirements.txt

EXPOSE 3001
CMD ["node", "auth-backend/server.js"]
