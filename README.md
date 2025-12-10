# 🕷️ WebScraper Platform

A production-grade, full-stack web scraping platform with a modern admin dashboard, powerful API, and intelligent job scheduling.

## 🎯 Features

### Core Capabilities
- **Intelligent Scraping Engine**: Support for both JavaScript-heavy sites (Playwright) and fast HTML parsing
- **Multi-Tenant Architecture**: Isolated projects and data for multiple users
- **Flexible Scheduling**: One-time, hourly, daily, weekly scraping jobs with cron support
- **Rich Extraction Schemas**: CSS selectors, XPath, JSONPath for structured data extraction
- **Real-Time Monitoring**: Track job status, success rates, and performance metrics
- **Webhook Support**: Push notifications on job completion
- **Proxy Rotation**: Built-in proxy management for rate limiting and IP rotation
- **Result Export**: JSON, CSV formats with API access

### Admin Dashboard
- 📊 **Dashboard Overview**: KPIs, charts, and real-time statistics
- 🗂️ **Project Management**: Create, edit, and manage scraping projects
- ⚙️ **Job Control**: Manual triggers, status monitoring, log inspection
- 📋 **Results Viewer**: Paginated data tables with JSON viewer and CSV export
- 🔐 **User Management**: Role-based access control (admin, client, viewer)
- 🛠️ **System Settings**: Proxy configuration, rate limits, API keys

### API
- **RESTful API**: Comprehensive endpoints for all operations
- **JWT Authentication**: Secure token-based auth
- **Rate Limiting**: Configurable per-user limits
- **Pagination**: Efficient data retrieval
- **OpenAPI/Swagger**: Auto-generated interactive documentation

---

## 🏗️ Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   Next.js UI    │─────▶│  FastAPI API    │─────▶│   PostgreSQL    │
│   (Dashboard)   │      │   (Backend)     │      │   (Database)    │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                                │
                                ▼
                         ┌─────────────────┐      ┌─────────────────┐
                         │  Celery Worker  │◀─────│      Redis      │
                         │  (Scraper Jobs) │      │  (Queue/Cache)  │
                         └─────────────────┘      └─────────────────┘
                                │
                                ▼
                         ┌─────────────────┐
                         │   Playwright    │
                         │   (Browser)     │
                         └─────────────────┘
```

---

## 🛠️ Tech Stack

### Backend
- **Python 3.11+** with **FastAPI**
- **PostgreSQL** for data persistence
- **Redis** for caching and task queue
- **Celery** for background job processing
- **Playwright** for browser automation
- **SQLAlchemy** + **Alembic** for ORM and migrations

### Frontend
- **Next.js 14** (App Router) with **React 18**
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **TanStack Query** for data fetching
- **Zustand** for state management
- **Recharts** for data visualization

### DevOps
- **Docker** + **Docker Compose** for containerization
- **Flower** for Celery monitoring
- **Structured logging** (JSON) with OpenTelemetry-ready format

---

## 🚀 Quick Start

### Prerequisites
- **Docker** and **Docker Compose** installed
- **Make** (optional, for convenient commands)
- **Git**

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/webscraper.git
   cd webscraper
   ```

2. **Create environment file**
   ```bash
   make create-env
   # OR
   cp .env.example .env
   ```

3. **Update environment variables**
   Edit `.env` and set required values:
   - `SECRET_KEY`: Generate with `openssl rand -hex 32`
   - `POSTGRES_PASSWORD`: Set a strong password
   - Update `CORS_ORIGINS` if needed

4. **Initialize and start the project**
   ```bash
   make init
   ```

   This will:
   - Build Docker images
   - Start all services
   - Run database migrations
   - Seed initial data

5. **Access the services**
   - **Frontend Dashboard**: http://localhost:3000
   - **Backend API**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs
   - **Flower (Celery Monitor)**: http://localhost:5555

---

## 📖 Usage

### Using Make Commands

```bash
# Development
make dev              # Start development environment
make logs             # View all logs
make logs-backend     # View backend logs only
make logs-worker      # View worker logs only

# Database
make migrate          # Run migrations
make migrate-create MESSAGE="your migration"  # Create new migration
make db-reset         # Reset database (WARNING: destructive)
make seed             # Seed sample data

# Testing
make test             # Run all tests
make test-backend     # Run backend tests
make test-backend-cov # Run backend tests with coverage

# Code Quality
make format           # Format code (Python & TypeScript)
make lint             # Lint code
make lint-fix         # Fix linting issues

# Shell Access
make backend-shell    # Access backend container
make db-shell         # Access PostgreSQL
make redis-shell      # Access Redis CLI

# Utilities
make playwright-install  # Install Playwright browsers
make backup-db        # Backup database
make api-docs         # Open API documentation
```

### Manual Docker Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild images
docker-compose build

# Run migrations
docker-compose exec backend alembic upgrade head
```

---

## 📁 Project Structure

```
webscraper/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   ├── repositories/   # Data access layer
│   │   ├── scraper/        # Scraping engine
│   │   ├── workers/        # Celery tasks
│   │   └── db/            # Database & migrations
│   ├── tests/             # Test suite
│   └── requirements.txt   # Python dependencies
│
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/           # App Router pages
│   │   ├── components/    # React components
│   │   ├── lib/           # Utilities
│   │   ├── hooks/         # Custom hooks
│   │   ├── types/         # TypeScript types
│   │   └── contexts/      # React contexts
│   └── package.json       # Node dependencies
│
├── docs/                   # Documentation
├── scripts/                # Utility scripts
├── docker-compose.yml      # Development orchestration
└── Makefile               # Convenience commands
```

---

## 🔐 Security Considerations

### Best Practices Implemented
- ✅ **JWT-based authentication** with secure token handling
- ✅ **Password hashing** using bcrypt
- ✅ **Multi-tenant data isolation** at database level
- ✅ **CORS configuration** for API security
- ✅ **Rate limiting** to prevent abuse
- ✅ **Environment-based secrets** (never hardcoded)
- ✅ **robots.txt compliance** (configurable per project)
- ✅ **Request throttling** to avoid DoS on target sites

### Configuration
- Always use strong, unique `SECRET_KEY` in production
- Enable HTTPS in production environments
- Rotate API keys regularly
- Configure proxy settings to avoid IP bans
- Review and respect target website ToS and rate limits

---

## 🧪 Testing

### Backend Tests
```bash
# Run all backend tests
make test-backend

# Run with coverage report
make test-backend-cov

# Run specific test file
docker-compose exec backend pytest tests/unit/test_scraper.py -v
```

### Frontend Tests
```bash
# Run all frontend tests
make test-frontend

# Run in watch mode
docker-compose exec frontend npm run test:watch

# Run E2E tests
make test-frontend-e2e
```

---

## 📊 API Documentation

Once the backend is running, access interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Authentication
- `POST /api/v1/auth/login` - Login and get JWT token
- `POST /api/v1/auth/register` - Register new user

#### Projects
- `GET /api/v1/projects` - List all projects
- `POST /api/v1/projects` - Create new project
- `GET /api/v1/projects/{id}` - Get project details
- `PATCH /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project

#### Jobs
- `GET /api/v1/jobs` - List jobs (with filters)
- `POST /api/v1/projects/{id}/jobs` - Trigger manual job
- `GET /api/v1/jobs/{id}` - Get job details

#### Results
- `GET /api/v1/jobs/{id}/results` - Get job results
- `GET /api/v1/projects/{id}/results` - Get all project results

---

## 🔧 Configuration

### Environment Variables

Key environment variables (see `.env.example` for full list):

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://...` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `SECRET_KEY` | JWT secret key | **Must set in production** |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |
| `PLAYWRIGHT_BROWSER` | Browser type | `chromium` |
| `MAX_CONCURRENT_JOBS` | Max parallel scraping jobs | `5` |
| `DEFAULT_REQUEST_DELAY` | Delay between requests (ms) | `1000` |
| `PROXY_ENABLED` | Enable proxy rotation | `false` |

---

## 📈 Monitoring

### Celery Monitoring with Flower
Access Flower at http://localhost:5555 to monitor:
- Active workers
- Task success/failure rates
- Queue length
- Task runtime statistics

### Logs
Structured JSON logs are written to `./logs/app.log` and stdout.

```bash
# View real-time logs
make logs

# Filter backend logs
make logs-backend

# Filter worker logs
make logs-worker
```

---

## 🚀 Deployment

### Production Checklist

1. **Update environment variables**
   - Set strong `SECRET_KEY`
   - Use production database credentials
   - Configure proper `CORS_ORIGINS`
   - Enable HTTPS

2. **Build production images**
   ```bash
   make build-prod
   ```

3. **Run database migrations**
   ```bash
   docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
   ```

4. **Start production services**
   ```bash
   make up-prod
   ```

### Recommended Infrastructure
- **Containerization**: Deploy with Kubernetes or managed container services (AWS ECS, Google Cloud Run)
- **Database**: Managed PostgreSQL (AWS RDS, Google Cloud SQL, Azure Database)
- **Cache**: Managed Redis (AWS ElastiCache, Redis Cloud)
- **CDN**: CloudFlare, AWS CloudFront for static assets
- **Monitoring**: Sentry for error tracking, Datadog/New Relic for APM

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style
- Backend: Follow PEP 8, use `black` and `isort`
- Frontend: Use Prettier with default settings
- Run `make format` and `make lint` before committing

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- Playwright for reliable browser automation
- Next.js for the modern React framework
- The open-source community

---

## 📞 Support

- **Issues**: https://github.com/yourusername/webscraper/issues
- **Discussions**: https://github.com/yourusername/webscraper/discussions
- **Email**: support@webscraper.com

---

**Built with ❤️ for the web scraping community**
#   w e b s c r a p e r  
 #   w e b s c r a p e r  
 