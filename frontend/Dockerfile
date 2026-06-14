# Stage 1: Build the React application
FROM public.ecr.aws/docker/library/node:20-alpine AS builder

WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

# Install dependencies
COPY package*.json pnpm-lock.yaml* ./
RUN pnpm install

# Copy source files
COPY . .

# Pass the VITE_API_URL build argument
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# Build the application
RUN pnpm run build

# Stage 2: Serve the compiled static files using Nginx
FROM public.ecr.aws/docker/library/nginx:1.25-alpine

# Copy custom nginx configuration for frontend
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy build output from Stage 1
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 5173

CMD ["nginx", "-g", "daemon off;"]
