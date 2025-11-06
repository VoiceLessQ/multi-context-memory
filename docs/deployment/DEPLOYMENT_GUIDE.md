# Deployment Guide - MCP Multi-Context Memory System

**Copyright (c) 2024 VoiceLessQ**
**Licensed under MIT License**

This comprehensive guide covers deploying the MCP Multi-Context Memory System in various environments.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Cloud Deployments](#cloud-deployments)
- [Kubernetes](#kubernetes)
- [Monitoring & Logging](#monitoring--logging)
- [Backup & Recovery](#backup--recovery)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 4GB
- Disk: 10GB free space
- OS: Linux, macOS, or Windows with WSL2

**Recommended:**
- CPU: 4+ cores
- RAM: 8GB+
- Disk: 50GB+ SSD
- OS: Linux (Ubuntu 20.04+ or similar)

### Software Requirements

- **Python**: 3.8+ (Python 3.11+ recommended)
- **Docker**: 20.10+ (for containerized deployment)
- **Docker Compose**: 2.0+ (for multi-service deployment)
- **Git**: For cloning the repository
- **Redis**: 7.0+ (for caching layer)

---

## Local Development

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/VoiceLessQ/multi-context-memory.git
cd multi-context-memory

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env

# Edit .env with your configuration
nano .env

# 5. Initialize database
python -c "from src.database.models import init_db; init_db()"

# 6. Start Redis (in separate terminal)
docker run -d -p 6379:6379 --name mcm-redis redis:7-alpine

# 7. Run the MCP server
python src/mcp_stdio_server.py

# OR run the API server
uvicorn src.api.main:app --host 0.0.0.0 --port 8002 --reload
```

### Environment Configuration

**Minimal `.env` for development:**

```bash
# Database
DATABASE_URL=sqlite:///./data/sqlite/memory.db

# API
API_HOST=0.0.0.0
API_PORT=8002

# Security (CHANGE THESE!)
JWT_SECRET_KEY=development-secret-key-change-in-production
API_SECRET_KEY=development-api-key-change-in-production

# Features
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379
CHROMA_ENABLED=true
VECTOR_SEARCH_ENABLED=true

# Embeddings
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

---

## Docker Deployment

### Using Docker Compose (Recommended)

**1. Prepare environment:**

```bash
# Clone repository
git clone https://github.com/VoiceLessQ/multi-context-memory.git
cd multi-context-memory

# Copy and configure environment
cp .env.example .env

# Generate secure secrets
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env
python -c "import secrets; print('API_SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env
```

**2. Start services:**

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

**3. Verify deployment:**

```bash
# Health check
curl http://localhost:8002/health

# API documentation
open http://localhost:8002/docs
```

### Docker Compose Configuration

**Default `docker-compose.yml`:**

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: mcm-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    networks:
      - mcm-network

  api-server:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: mcm-api
    restart: unless-stopped
    ports:
      - "8002:8002"
    environment:
      - DATABASE_URL=sqlite:///./data/sqlite/memory.db
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_ENABLED=true
      - CHROMA_ENABLED=true
      - VECTOR_SEARCH_ENABLED=true
    env_file:
      - .env
    volumes:
      - ./data:/app/data
    depends_on:
      - redis
    networks:
      - mcm-network

  memory-server:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: mcm-mcp
    restart: unless-stopped
    command: python src/mcp_stdio_server.py
    environment:
      - DATABASE_URL=sqlite:///./data/sqlite/memory.db
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    env_file:
      - .env
    volumes:
      - ./data:/app/data
    depends_on:
      - redis
    networks:
      - mcm-network

volumes:
  redis-data:

networks:
  mcm-network:
    driver: bridge
```

---

## Production Deployment

### Security Checklist

Before deploying to production, **MUST complete:**

- [ ] **Generate secure secrets** (32+ characters)
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```

- [ ] **Configure JWT_SECRET_KEY** in `.env`
- [ ] **Configure API_SECRET_KEY** in `.env`
- [ ] **Enable HTTPS** (use reverse proxy)
- [ ] **Set up rate limiting** (slowapi or nginx)
- [ ] **Configure firewall rules**
- [ ] **Enable database backups**
- [ ] **Set up monitoring and alerting**
- [ ] **Review CORS settings**
- [ ] **Disable debug mode** (`DEBUG=false`)
- [ ] **Use PostgreSQL** instead of SQLite for production

### Production Docker Compose

**`docker-compose.prod.yml`:**

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: mcm-postgres
    restart: always
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - mcm-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: mcm-redis
    restart: always
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    volumes:
      - redis-data:/data
    networks:
      - mcm-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  api-server:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        - BUILD_ENV=production
    container_name: mcm-api
    restart: always
    environment:
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - DEBUG=false
      - LOG_LEVEL=INFO
    env_file:
      - .env.production
    volumes:
      - ./data:/app/data
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - mcm-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    container_name: mcm-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - nginx-logs:/var/log/nginx
    depends_on:
      - api-server
    networks:
      - mcm-network

volumes:
  postgres-data:
  redis-data:
  nginx-logs:

networks:
  mcm-network:
    driver: bridge
```

### Nginx Configuration

**`nginx/nginx.conf`:**

```nginx
events {
    worker_connections 1024;
}

http {
    upstream api_backend {
        server api-server:8002;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    server {
        listen 80;
        server_name your-domain.com;

        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Strict-Transport-Security "max-age=31536000" always;

        # API endpoints
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;

            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # API docs
        location /docs {
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
        }

        # Health check
        location /health {
            proxy_pass http://api_backend;
            access_log off;
        }
    }
}
```

### Deploy to Production

```bash
# 1. Prepare environment
cp .env.example .env.production

# Edit with production values
nano .env.production

# 2. Generate SSL certificates (Let's Encrypt)
certbot certonly --standalone -d your-domain.com

# Copy certificates
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem

# 3. Deploy
docker-compose -f docker-compose.prod.yml up -d

# 4. Verify
curl https://your-domain.com/health
```

---

## Cloud Deployments

### AWS (Amazon Web Services)

**Using EC2 + Docker:**

```bash
# 1. Launch EC2 instance (Ubuntu 22.04, t3.medium or larger)

# 2. Connect to instance
ssh -i your-key.pem ubuntu@ec2-instance-ip

# 3. Install Docker
sudo apt update
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker ubuntu

# 4. Clone and deploy
git clone https://github.com/VoiceLessQ/multi-context-memory.git
cd multi-context-memory
cp .env.example .env
nano .env  # Configure
docker-compose up -d

# 5. Configure security group
# Allow inbound: 22 (SSH), 80 (HTTP), 443 (HTTPS)
```

**Using ECS (Elastic Container Service):**

See `docs/deployment/AWS_ECS.md` (coming soon)

### Google Cloud Platform

**Using Compute Engine + Docker:**

```bash
# 1. Create VM instance (e2-medium or larger)
gcloud compute instances create mcm-server \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --machine-type=e2-medium \
  --boot-disk-size=50GB

# 2. SSH to instance
gcloud compute ssh mcm-server

# 3. Follow same Docker deployment steps as AWS
```

### Azure

**Using Azure Container Instances:**

See `docs/deployment/AZURE.md` (coming soon)

### DigitalOcean

**Using Droplet + Docker:**

```bash
# 1. Create Droplet (Ubuntu 22.04, Basic - 2GB RAM minimum)

# 2. SSH to droplet
ssh root@droplet-ip

# 3. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 4. Clone and deploy
git clone https://github.com/VoiceLessQ/multi-context-memory.git
cd multi-context-memory
cp .env.example .env
nano .env  # Configure
docker-compose up -d
```

---

## Kubernetes

### Prerequisites

- Kubernetes cluster (1.20+)
- kubectl configured
- Helm 3.0+ (optional)

### Basic Kubernetes Deployment

**1. Create namespace:**

```bash
kubectl create namespace mcm
```

**2. Create secrets:**

```bash
# Generate secrets
JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
API_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Create Kubernetes secret
kubectl create secret generic mcm-secrets \
  --from-literal=jwt-secret-key=$JWT_SECRET \
  --from-literal=api-secret-key=$API_SECRET \
  -n mcm
```

**3. Deploy resources:**

```bash
kubectl apply -f k8s/ -n mcm
```

### Kubernetes Configuration Files

See `docs/deployment/KUBERNETES.md` for complete examples.

---

## Monitoring & Logging

### Monitoring Stack

**Using Prometheus + Grafana:**

```yaml
# Add to docker-compose.yml
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - mcm-network

  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana-data:/var/lib/grafana
    ports:
      - "3000:3000"
    networks:
      - mcm-network
```

### Centralized Logging

**Using ELK Stack (Elasticsearch, Logstash, Kibana):**

See `docs/deployment/MONITORING.md` for detailed setup.

---

## Backup & Recovery

### Database Backups

**SQLite:**

```bash
# Backup
sqlite3 data/sqlite/memory.db ".backup 'backup-$(date +%Y%m%d).db'"

# Restore
cp backup-20240115.db data/sqlite/memory.db
```

**PostgreSQL:**

```bash
# Backup
docker-compose exec postgres pg_dump -U mcm_user mcm_db > backup-$(date +%Y%m%d).sql

# Restore
docker-compose exec -T postgres psql -U mcm_user mcm_db < backup-20240115.sql
```

### Automated Backups

**Cron job for daily backups:**

```bash
# Add to crontab
0 2 * * * /path/to/backup-script.sh
```

**`backup-script.sh`:**

```bash
#!/bin/bash
BACKUP_DIR=/backups
DATE=$(date +%Y%m%d)

# Backup database
docker-compose exec -T postgres pg_dump -U mcm_user mcm_db > $BACKUP_DIR/db-$DATE.sql

# Backup vector store
tar -czf $BACKUP_DIR/chroma-$DATE.tar.gz data/chroma/

# Keep only last 7 days
find $BACKUP_DIR -type f -mtime +7 -delete
```

---

## Troubleshooting

### Common Issues

**Port already in use:**

```bash
# Find process using port
lsof -i :8002

# Kill process
kill -9 <PID>
```

**Docker permission denied:**

```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

**Database locked:**

```bash
# Enable WAL mode for SQLite
sqlite3 data/sqlite/memory.db "PRAGMA journal_mode=WAL;"
```

**Out of memory:**

```bash
# Check memory usage
docker stats

# Increase Docker memory limit
# Edit Docker Desktop settings or daemon.json
```

---

## Support

For deployment help:
- **Documentation**: https://github.com/VoiceLessQ/multi-context-memory
- **Issues**: https://github.com/VoiceLessQ/multi-context-memory/issues
- **Discussions**: https://github.com/VoiceLessQ/multi-context-memory/discussions

---

**Copyright (c) 2024 VoiceLessQ**
**Licensed under MIT License**
