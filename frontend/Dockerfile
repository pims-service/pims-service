# Base image
FROM node:20-alpine

# Set work directory
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy project
COPY . .

# Build for production if necessary
# RUN npm run build

# Expose port for Vite
EXPOSE 5173

# Default command for development (hot reloading)
CMD ["npm", "run", "dev", "--", "--host"]
