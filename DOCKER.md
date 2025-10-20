# Docker Deployment Guide

## 🐳 Running CVExtract Pro with Docker

### Prerequisites
- Docker Desktop installed and running ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (included with Docker Desktop)
- At least 2GB RAM and 1GB disk space available

---

## 🚀 Quick Start

### Option 1: Using Management Scripts (Recommended)

**Windows:**
```cmd
# Development mode (with hot reloading)
docker-scripts.bat dev

# Production mode
docker-scripts.bat prod

# View logs
docker-scripts.bat logs

# Stop application
docker-scripts.bat stop
```

**Linux/Mac:**
```bash
# Development mode (with hot reloading)
./docker-scripts.sh dev

# Production mode
./docker-scripts.sh prod

# View logs
./docker-scripts.sh logs

# Stop application
./docker-scripts.sh stop
```

### Option 2: Using Docker Compose Directly

**Development Mode:**
```bash
# Start with development settings
docker-compose up --build

# Run in background
docker-compose up -d --build
```

**Production Mode:**
```bash
# Start with production settings
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

The app will be available at: **http://localhost:5000**

### Option 3: Using Docker Commands

```bash
# Build the image
docker build -t cvextract-pro .

# Run the container (development)
docker run -d \
  -p 5000:5000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/results:/app/results \
  --name cvextract-pro \
  cvextract-pro

# View logs
docker logs -f cvextract-pro

# Stop the container
docker stop cvextract-pro
docker rm cvextract-pro
```

---

## 📁 Volume Mounts

The Docker setup mounts two directories for data persistence:

- **`./uploads`** - Stores uploaded PDF files
- **`./results`** - Stores extraction results (JSON, Markdown)

This ensures your data persists even if the container is removed.

---

## 🔧 Configuration

### Environment Variables

You can customize the application by setting environment variables:

```yaml
# docker-compose.yml
environment:
  - FLASK_ENV=production
  - MAX_CONTENT_LENGTH=16777216  # 16MB max file size
  - UPLOAD_FOLDER=/app/uploads
  - RESULTS_FOLDER=/app/results
```

### Port Configuration

To use a different port, modify `docker-compose.yml`:

```yaml
ports:
  - "8080:5000"  # Access on port 8080
```

---

## 🚀 Production Deployment

### Using Gunicorn (Production Server)

Update `Dockerfile` CMD:

```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "web_app:app"]
```

And add gunicorn to `requirements.txt`:

```txt
gunicorn==21.2.0
```

### Health Checks

The container includes health checks to ensure the app is running:

```bash
# Check container health
docker ps
```

Look for "(healthy)" in the STATUS column.

---

## 🛠️ Useful Commands

```bash
# Rebuild after code changes
docker-compose up -d --build

# View container logs
docker-compose logs -f cvextract

# Access container shell
docker-compose exec cvextract /bin/bash

# Stop and remove containers
docker-compose down

# Remove volumes (clears uploads/results)
docker-compose down -v

# View resource usage
docker stats cvextract-pro
```

---

## 🔍 Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs

# Rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Port already in use
```bash
# Use a different port in docker-compose.yml
ports:
  - "5001:5000"
```

### Permission issues with volumes
```bash
# Fix permissions (Linux/Mac)
sudo chown -R $(whoami):$(whoami) uploads results
```

---

## 📊 Resource Requirements

**Minimum:**
- CPU: 1 core
- RAM: 512MB
- Disk: 1GB

**Recommended:**
- CPU: 2 cores
- RAM: 1GB
- Disk: 5GB

---

## 🌐 Deployment Platforms

### Deploy to Docker Hub

```bash
# Tag the image
docker tag cvextract-pro yourusername/cvextract-pro:latest

# Push to Docker Hub
docker push yourusername/cvextract-pro:latest
```

### Deploy to Cloud Platforms

- **AWS ECS**: Use the Dockerfile with ECS task definitions
- **Google Cloud Run**: Supports containerized apps
- **Azure Container Instances**: Deploy directly from Docker Hub
- **DigitalOcean App Platform**: Connect to your GitHub repo

---

## 🔒 Security Notes

For production deployments:

1. **Use HTTPS** - Set up a reverse proxy (Nginx/Traefik)
2. **Set resource limits** - Add to docker-compose.yml:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 1G
   ```
3. **Run as non-root user** - Add to Dockerfile:
   ```dockerfile
   RUN useradd -m -u 1000 appuser
   USER appuser
   ```
4. **Scan for vulnerabilities**:
   ```bash
   docker scan cvextract-pro
   ```

---

## 🔧 Docker Configuration Files

### Core Files
- **`Dockerfile`** - Multi-stage production build with security optimizations
- **`docker-compose.yml`** - Base configuration with resource limits and health checks
- **`docker-compose.override.yml`** - Development overrides (auto-loaded)
- **`docker-compose.prod.yml`** - Production-specific settings
- **`.dockerignore`** - Excludes unnecessary files from build context

### Management Scripts
- **`docker-scripts.sh`** - Linux/Mac management script
- **`docker-scripts.bat`** - Windows management script

### Key Improvements
✅ **Multi-stage build** - Smaller production image  
✅ **Security hardening** - Non-root user, no new privileges  
✅ **Production server** - Gunicorn with optimized settings  
✅ **Resource limits** - CPU and memory constraints  
✅ **Health checks** - Automatic container health monitoring  
✅ **Logging** - Structured logging with rotation  
✅ **Development mode** - Hot reloading for faster development  

## 📝 Docker Image Details

**Base Image:** `python:3.11-slim`  
**Size:** ~150MB (optimized with multi-stage build)  
**Exposed Port:** 5000  
**Health Check:** HTTP GET to `/`  
**Security:** Non-root user, read-only filesystem where possible  
**Server:** Gunicorn with 4 workers  

## 🛡️ Security Features

- **Non-root user**: Application runs as `appuser`
- **No new privileges**: Prevents privilege escalation
- **Resource limits**: CPU and memory constraints
- **Health monitoring**: Automatic health checks
- **Log rotation**: Prevents disk space issues
- **Minimal attack surface**: Only necessary dependencies

---

**Happy Dockerizing! 🐳**

