# Deployment Guide

This guide covers deploying PyFrame applications to production environments, from simple cloud platforms to enterprise infrastructure.

## 🚀 Quick Deployment Options

### 1. Platform-as-a-Service (PaaS)

#### Heroku

```bash
# Install Heroku CLI and create app
heroku create my-pyframe-app

# Add Python buildpack
heroku buildpacks:set heroku/python

# Create Procfile
echo "web: python main.py" > Procfile

# Create requirements.txt
echo "pyframe>=0.1.0" > requirements.txt
echo "gunicorn>=20.1.0" >> requirements.txt
echo "psycopg2-binary>=2.9.0" >> requirements.txt

# Configure environment
heroku config:set PYFRAME_ENV=production
heroku config:set DEBUG=False
heroku config:set SECRET_KEY="your-secret-key-here"

# Add database
heroku addons:create heroku-postgresql:mini

# Deploy
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

#### Railway

```toml
# railway.toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python main.py"
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"

[env]
PYFRAME_ENV = "production"
PORT = { default = "3000" }
```

#### Render

```yaml
# render.yaml
services:
  - type: web
    name: pyframe-app
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python main.py"
    envVars:
      - key: PYFRAME_ENV
        value: production
      - key: DEBUG
        value: false
```

### 2. Docker Deployment

#### Basic Dockerfile

```dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYFRAME_ENV=production

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Run application
CMD ["python", "main.py"]
```

#### Production Dockerfile

```dockerfile
FROM python:3.11-slim as builder

# Build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt

# Production stage
FROM python:3.11-slim

# Runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels and install
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache /wheels/*

# Application setup
WORKDIR /app
COPY . .

# Security
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 3000
CMD ["gunicorn", "--bind", "0.0.0.0:3000", "--workers", "4", "main:app"]
```

#### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "3000:3000"
    environment:
      - PYFRAME_ENV=production
      - DATABASE_URL=postgresql://postgres:password@db:5432/pyframe_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./static:/app/static
      - ./media:/app/media

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=pyframe_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
      - ./static:/var/www/static
    depends_on:
      - web

volumes:
  postgres_data:
  redis_data:
```

## ⚙️ Production Configuration

### Application Configuration

```python
# config/production.py
import os
from pyframe import PyFrameConfig

config = PyFrameConfig(
    # Server settings
    debug=False,
    host="0.0.0.0",
    port=int(os.getenv("PORT", 3000)),
    hot_reload=False,
    
    # Security
    secret_key=os.getenv("SECRET_KEY"),
    allowed_hosts=os.getenv("ALLOWED_HOSTS", "").split(","),
    secure_cookies=True,
    session_cookie_secure=True,
    csrf_protection=True,
    
    # Database
    database_url=os.getenv("DATABASE_URL"),
    database_pool_size=20,
    database_max_overflow=30,
    
    # Caching
    cache_backend="redis",
    cache_url=os.getenv("REDIS_URL"),
    cache_default_timeout=300,
    
    # Static files
    static_url="/static/",
    static_root=os.path.join(os.getcwd(), "staticfiles"),
    media_url="/media/",
    media_root=os.path.join(os.getcwd(), "media"),
    
    # Logging
    log_level="INFO",
    log_format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    
    # Performance
    enable_gzip=True,
    gzip_level=6,
    max_request_size=10 * 1024 * 1024,  # 10MB
    
    # Security headers
    security_headers={
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
    }
)
```

### Environment Variables

```bash
# .env.production
PYFRAME_ENV=production
DEBUG=False
SECRET_KEY=your-super-secret-key-here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/pyframe_prod
DATABASE_POOL_SIZE=20

# Cache
REDIS_URL=redis://localhost:6379/0

# Security
ALLOWED_HOSTS=example.com,www.example.com
SECURE_COOKIES=True

# External services
EMAIL_URL=smtp://user:password@smtp.example.com:587
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
MONITORING_ENABLED=True
```

## 🌐 Web Server Configuration

### Nginx

```nginx
# nginx.conf
upstream pyframe_app {
    server web:3000;
    # Add more servers for load balancing
    # server web2:3000;
    # server web3:3000;
}

server {
    listen 80;
    server_name example.com www.example.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com www.example.com;
    
    # SSL configuration
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    
    # Gzip compression
    gzip on;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    # Static files
    location /static/ {
        alias /var/www/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /var/www/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # WebSocket support
    location /ws/ {
        proxy_pass http://pyframe_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
    
    # Main application
    location / {
        proxy_pass http://pyframe_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;
    }
    
    # Health check
    location /health {
        proxy_pass http://pyframe_app/health;
        access_log off;
    }
}
```

### Apache

```apache
# apache.conf
<VirtualHost *:80>
    ServerName example.com
    DocumentRoot /var/www/html
    
    # Redirect to HTTPS
    RewriteEngine On
    RewriteCond %{HTTPS} off
    RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]
</VirtualHost>

<VirtualHost *:443>
    ServerName example.com
    DocumentRoot /var/www/html
    
    # SSL Configuration
    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/fullchain.pem
    SSLCertificateKeyFile /etc/ssl/private/privkey.pem
    
    # Static files
    Alias /static /var/www/static
    <Directory "/var/www/static">
        Require all granted
        ExpiresActive On
        ExpiresDefault "access plus 1 year"
    </Directory>
    
    # Proxy to PyFrame app
    ProxyPreserveHost On
    ProxyPass /static !
    ProxyPass /media !
    ProxyPass / http://localhost:3000/
    ProxyPassReverse / http://localhost:3000/
    
    # WebSocket support
    ProxyPass /ws/ ws://localhost:3000/ws/
    ProxyPassReverse /ws/ ws://localhost:3000/ws/
</VirtualHost>
```

## 🏗️ Infrastructure as Code

### Terraform (AWS)

```hcl
# main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "pyframe-vpc"
  }
}

# Subnets
resource "aws_subnet" "public" {
  count = 2
  
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
  
  tags = {
    Name = "pyframe-public-${count.index + 1}"
  }
}

resource "aws_subnet" "private" {
  count = 2
  
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  
  tags = {
    Name = "pyframe-private-${count.index + 1}"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "pyframe-cluster"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# RDS Database
resource "aws_db_instance" "main" {
  identifier = "pyframe-db"
  
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.micro"
  
  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp2"
  storage_encrypted     = true
  
  db_name  = "pyframe"
  username = var.db_username
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  skip_final_snapshot = true
  deletion_protection = false
  
  tags = {
    Name = "pyframe-database"
  }
}

# ElastiCache (Redis)
resource "aws_elasticache_subnet_group" "main" {
  name       = "pyframe-cache-subnet"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_elasticache_cluster" "main" {
  cluster_id           = "pyframe-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.redis.id]
  
  tags = {
    Name = "pyframe-cache"
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "pyframe-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets           = aws_subnet.public[*].id
  
  enable_deletion_protection = false
  
  tags = {
    Name = "pyframe-alb"
  }
}
```

### Kubernetes

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: pyframe

---
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pyframe-app
  namespace: pyframe
spec:
  replicas: 3
  selector:
    matchLabels:
      app: pyframe-app
  template:
    metadata:
      labels:
        app: pyframe-app
    spec:
      containers:
      - name: pyframe
        image: your-registry/pyframe-app:latest
        ports:
        - containerPort: 3000
        env:
        - name: PYFRAME_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: pyframe-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: pyframe-secrets
              key: redis-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: pyframe-secrets
              key: secret-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5

---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: pyframe-service
  namespace: pyframe
spec:
  selector:
    app: pyframe-app
  ports:
  - protocol: TCP
    port: 80
    targetPort: 3000
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: pyframe-ingress
  namespace: pyframe
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - example.com
    secretName: pyframe-tls
  rules:
  - host: example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: pyframe-service
            port:
              number: 80
```

## 📊 Monitoring and Logging

### Application Monitoring

```python
# monitoring.py
import os
import logging
from pyframe.monitoring import setup_monitoring

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/pyframe/app.log')
    ]
)

# Setup Sentry for error tracking
if os.getenv('SENTRY_DSN'):
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration
    
    sentry_logging = LoggingIntegration(
        level=logging.INFO,
        event_level=logging.ERROR
    )
    
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[sentry_logging],
        traces_sample_rate=0.1,
        environment=os.getenv('PYFRAME_ENV', 'development')
    )

# Setup Prometheus metrics
if os.getenv('PROMETHEUS_ENABLED'):
    from prometheus_client import Counter, Histogram, generate_latest
    
    REQUEST_COUNT = Counter('pyframe_requests_total', 'Total requests', ['method', 'endpoint'])
    REQUEST_DURATION = Histogram('pyframe_request_duration_seconds', 'Request duration')
    
    @app.middleware
    async def metrics_middleware(context, call_next):
        start_time = time.time()
        
        response = await call_next(context)
        
        REQUEST_COUNT.labels(context.method, context.path).inc()
        REQUEST_DURATION.observe(time.time() - start_time)
        
        return response
    
    @app.route('/metrics')
    async def metrics(context):
        return {
            'status': 200,
            'headers': {'Content-Type': 'text/plain'},
            'body': generate_latest()
        }
```

### Health Checks

```python
# health.py
from pyframe import Component
from pyframe.database import get_db_connection
from pyframe.cache import get_cache_connection

class HealthCheck(Component):
    async def check_database(self):
        try:
            conn = await get_db_connection()
            await conn.execute('SELECT 1')
            return {'status': 'healthy', 'latency': '< 10ms'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    async def check_cache(self):
        try:
            cache = get_cache_connection()
            await cache.set('health_check', 'ok', expire=10)
            result = await cache.get('health_check')
            return {'status': 'healthy' if result == 'ok' else 'unhealthy'}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    async def render(self):
        db_health = await self.check_database()
        cache_health = await self.check_cache()
        
        overall_status = 'healthy' if (
            db_health['status'] == 'healthy' and 
            cache_health['status'] == 'healthy'
        ) else 'unhealthy'
        
        return {
            'status': overall_status,
            'checks': {
                'database': db_health,
                'cache': cache_health
            },
            'timestamp': datetime.now().isoformat()
        }

@app.route('/health')
async def health_check(context):
    health = HealthCheck()
    result = await health.render()
    
    status_code = 200 if result['status'] == 'healthy' else 503
    
    return {
        'status': status_code,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(result)
    }
```

## 🔒 Security Best Practices

### SSL/TLS Configuration

```python
# security.py
from pyframe.security import SecurityMiddleware

security_config = {
    # Force HTTPS
    'force_https': True,
    'https_redirect_permanent': True,
    
    # Security headers
    'security_headers': {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Content-Security-Policy': (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' wss: ws:;"
        )
    },
    
    # CSRF protection
    'csrf_protection': True,
    'csrf_cookie_secure': True,
    'csrf_cookie_httponly': True,
    
    # Session security
    'session_cookie_secure': True,
    'session_cookie_httponly': True,
    'session_cookie_samesite': 'Strict',
    
    # Rate limiting
    'rate_limiting': {
        'default': '100/hour',
        'login': '5/minute',
        'api': '1000/hour'
    }
}

app.use_middleware(SecurityMiddleware(security_config))
```

### Secrets Management

```python
# secrets.py
import os
from cryptography.fernet import Fernet

class SecretsManager:
    def __init__(self):
        # Use environment variable or secrets service
        self.encryption_key = os.getenv('ENCRYPTION_KEY')
        if not self.encryption_key:
            raise ValueError("ENCRYPTION_KEY environment variable is required")
        
        self.cipher = Fernet(self.encryption_key.encode())
    
    def encrypt_secret(self, value):
        return self.cipher.encrypt(value.encode()).decode()
    
    def decrypt_secret(self, encrypted_value):
        return self.cipher.decrypt(encrypted_value.encode()).decode()
    
    def get_secret(self, key):
        # Try environment first
        value = os.getenv(key)
        if value:
            return value
        
        # Try encrypted secrets file
        encrypted_value = self.get_encrypted_secret(key)
        if encrypted_value:
            return self.decrypt_secret(encrypted_value)
        
        raise ValueError(f"Secret '{key}' not found")

secrets = SecretsManager()

# Usage
database_password = secrets.get_secret('DATABASE_PASSWORD')
api_key = secrets.get_secret('EXTERNAL_API_KEY')
```

## 📈 Performance Optimization

### Application Performance

```python
# performance.py
from pyframe.performance import PerformanceMiddleware

performance_config = {
    # Response compression
    'gzip_compression': True,
    'gzip_level': 6,
    'gzip_min_size': 1024,
    
    # Static file optimization
    'static_file_caching': True,
    'static_file_max_age': 31536000,  # 1 year
    
    # Database connection pooling
    'db_pool_size': 20,
    'db_max_overflow': 30,
    'db_pool_timeout': 30,
    
    # Caching
    'cache_middleware': True,
    'cache_default_timeout': 300,
    
    # Request/response optimization
    'max_request_size': 10 * 1024 * 1024,  # 10MB
    'request_timeout': 30,
}

app.use_middleware(PerformanceMiddleware(performance_config))

# Database query optimization
@app.middleware
async def query_optimization_middleware(context, call_next):
    # Enable query debugging in development
    if app.config.debug:
        from pyframe.database import enable_query_logging
        enable_query_logging()
    
    response = await call_next(context)
    
    # Log slow queries
    if hasattr(context, 'db_queries'):
        slow_queries = [q for q in context.db_queries if q['duration'] > 0.1]
        if slow_queries:
            logger.warning(f"Slow queries detected: {len(slow_queries)}")
    
    return response
```

### CDN Configuration

```python
# cdn.py
import os

CDN_CONFIG = {
    'enabled': os.getenv('CDN_ENABLED', 'false').lower() == 'true',
    'url': os.getenv('CDN_URL', ''),
    'static_url': os.getenv('CDN_STATIC_URL', ''),
    'media_url': os.getenv('CDN_MEDIA_URL', ''),
    
    # CloudFront settings
    'cloudfront_distribution_id': os.getenv('CLOUDFRONT_DISTRIBUTION_ID'),
    
    # CloudFlare settings
    'cloudflare_zone_id': os.getenv('CLOUDFLARE_ZONE_ID'),
    'cloudflare_api_token': os.getenv('CLOUDFLARE_API_TOKEN'),
}

if CDN_CONFIG['enabled']:
    app.config.static_url = CDN_CONFIG['static_url']
    app.config.media_url = CDN_CONFIG['media_url']
```

## 🔄 CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest --cov=pyframe tests/
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to registry
      uses: docker/login-action@v2
      with:
        registry: {% raw %}${{ secrets.REGISTRY_URL }}{% endraw %}
        username: {% raw %}${{ secrets.REGISTRY_USERNAME }}{% endraw %}
        password: {% raw %}${{ secrets.REGISTRY_PASSWORD }}{% endraw %}
    
    - name: Build and push
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: {% raw %}${{ secrets.REGISTRY_URL }}/pyframe-app:${{ github.sha }}{% endraw %}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy:
    needs: build
    runs-on: ubuntu-latest
    
    steps:
    - name: Deploy to production
      run: |
        # Deploy using your preferred method
        # kubectl, helm, terraform, etc.
        echo "Deploying to production..."
```

## 📚 Best Practices Summary

### 1. Security
- Use HTTPS everywhere
- Implement proper authentication and authorization
- Keep dependencies updated
- Use environment variables for secrets
- Enable security headers
- Implement rate limiting

### 2. Performance  
- Use a reverse proxy (Nginx/Apache)
- Enable compression and caching
- Optimize database queries
- Use a CDN for static files
- Monitor application performance

### 3. Reliability
- Implement health checks
- Use multiple application instances
- Set up proper logging and monitoring
- Have a backup and disaster recovery plan
- Test your deployment pipeline

### 4. Scalability
- Use container orchestration (Kubernetes/Docker Swarm)
- Implement horizontal scaling
- Use managed database services
- Cache frequently accessed data
- Monitor resource usage

This deployment guide covers the essential aspects of taking your PyFrame application from development to production. Choose the deployment strategy that best fits your needs and scale! 🚀
