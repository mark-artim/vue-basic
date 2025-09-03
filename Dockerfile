FROM node:18-bullseye

WORKDIR /app

# Copy and install Node dependencies
COPY auth-backend/package*.json ./auth-backend/
RUN cd auth-backend && npm install

# Copy Node backend
COPY auth-backend/ ./auth-backend/

# Expose port
EXPOSE 3001

# Run Node server
CMD ["node", "auth-backend/server.js"]
