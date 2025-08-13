# Docker Deployment Guide

## Quick Start

### Using Docker Compose (Recommended)

1. **Build and run the application:**
   ```bash
   docker-compose up --build
   ```

2. **Access the application:**
   - Open your browser and go to: http://localhost:8501
   - The Ritter Sport Production Planner will be available

3. **Stop the application:**
   ```bash
   docker-compose down
   ```

### Using Docker directly

1. **Build the image:**
   ```bash
   docker build -t ritter-sport-planner .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8501:8501 \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/logs:/app/logs \
     -v $(pwd)/config:/app/config \
     ritter-sport-planner
   ```

## Configuration

### Environment Variables

- `STREAMLIT_SERVER_PORT`: Port for the Streamlit app (default: 8501)
- `STREAMLIT_SERVER_ADDRESS`: Address to bind to (default: 0.0.0.0)
- `STREAMLIT_SERVER_HEADLESS`: Run in headless mode (default: true)
- `PYTHONPATH`: Python module path (default: /app)

### Volume Mounts

The following directories are mounted for data persistence:

- `./data:/app/data` - Processed data and reports
- `./logs:/app/logs` - Application logs
- `./config:/app/config` - Configuration files

## Production Deployment

### Docker Compose with Nginx (Optional)

For production deployment, uncomment the nginx service in `docker-compose.yml` and create an `nginx.conf` file:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream streamlit {
        server ritter-sport-planner:8501;
    }

    server {
        listen 80;
        server_name your-domain.com;

        location / {
            proxy_pass http://streamlit;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### Health Checks

The container includes health checks that verify:
- Streamlit application is responding
- Health endpoint is accessible at `/_stcore/health`

### Resource Requirements

**Minimum:**
- CPU: 1 core
- Memory: 512MB
- Disk: 1GB

**Recommended:**
- CPU: 2 cores
- Memory: 1GB
- Disk: 2GB

## Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   # Change the port mapping
   docker-compose up --build -d
   # Or check what's using port 8501
   lsof -i :8501
   ```

2. **Permission issues with mounted volumes:**
   ```bash
   # Ensure directories exist and have correct permissions
   mkdir -p data logs
   chmod 755 data logs
   ```

3. **Application not starting:**
   ```bash
   # Check container logs
   docker-compose logs ritter-sport-planner
   ```

4. **Module import errors:**
   ```bash
   # Rebuild the image to ensure all dependencies are installed
   docker-compose build --no-cache
   ```

### Debugging

**Run container in interactive mode:**
```bash
docker run -it --entrypoint /bin/bash ritter-sport-planner
```

**Check application logs:**
```bash
docker-compose logs -f ritter-sport-planner
```

**Access running container:**
```bash
docker-compose exec ritter-sport-planner /bin/bash
```

## Development

### Building for Development

```bash
# Build development image
docker build -t ritter-sport-planner:dev .

# Run with code mounted for development
docker run -p 8501:8501 \
  -v $(pwd)/src:/app/src \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/config:/app/config \
  ritter-sport-planner:dev
```

### Multi-stage Build (Future Enhancement)

For production optimization, consider implementing a multi-stage Dockerfile:

```dockerfile
# Build stage
FROM python:3.10-slim as builder
# ... build dependencies and create wheel files

# Runtime stage  
FROM python:3.10-slim as runtime
# ... copy only necessary files from builder
```

## Security Considerations

- The container runs as root by default (consider creating a non-root user)
- Sensitive configuration should use Docker secrets or environment variables
- Use specific version tags instead of `latest` for production
- Regular security updates for base image and dependencies

## Monitoring

### Container Metrics

Monitor the following metrics:
- CPU and memory usage
- Response time of health checks
- Application logs for errors
- Disk usage of mounted volumes

### Application Metrics

- Streamlit session count
- Processing time for forecasting/optimization
- Error rates in application logs
- Data quality metrics from ETL processes
