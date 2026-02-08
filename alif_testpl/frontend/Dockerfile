FROM node:18-alpine

WORKDIR /app

# Vite may attempt to open a browser URL on startup; Alpine doesn't ship xdg-open.
# Installing xdg-utils prevents the dev server from crashing.
RUN apk add --no-cache xdg-utils

# Install dependencies first (caching)
COPY package.json package-lock.json* ./
RUN npm install

# Copy source code
COPY . .

# Expose port
EXPOSE 5173

# Start development server
CMD ["npm", "run", "dev", "--", "--host"]
