# Base image
FROM node:20-alpine

# Set work directory
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy project files
COPY . .

# Healthcheck to verify the dev server is running
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget --quiet --tries=1 --spider http://localhost:5173 || exit 1

# Build for production if necessary
# RUN npm run build

# Expose port for Vite
EXPOSE 5173

# Default command for development (hot reloading)
CMD ["npm", "run", "dev", "--", "--host"]
