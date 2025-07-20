# Rawbify Backend

FastAPI backend for Rawbify - Raw Data In. BI Ready Out.

## Features

- **Waitlist Management**: Email collection and statistics
- **User Validation**: Trial access validation (stateless)
- **Data Processing**: File upload and processing with 'done' column addition
- **SQLite Integration**: Data persistence with `r_` prefixed tables (development)
- **PostgreSQL Ready**: Easy switch to PostgreSQL for production

## API Endpoints

### Waitlist
- `POST /api/waitlist/join` - Add email to waitlist
- `GET /api/waitlist/stats` - Get waitlist statistics

### User Validation
- `POST /api/validate-user` - Validate trial user ID

### Data Processing
- `POST /api/process-data` - Process uploaded files

## Setup

### Prerequisites
- Python 3.11+
- SQLite (built into Python) - for development
- PostgreSQL (optional) - for production
- Docker (optional)

### Installation

1. **Clone and navigate to the backend directory:**
```bash
cd rawbify-backend
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables (optional):**
Create a `.env` file with:
```env
# For development (SQLite - default)
DATABASE_URL=sqlite:///./rawbify.db

# For production (PostgreSQL)
# DATABASE_URL=postgresql://username:password@localhost:5432/rawbify

CORS_ORIGINS=http://localhost:3000,http://localhost:3001
SENDGRID_API_KEY=your_sendgrid_api_key
FROM_EMAIL=noreply@rawbify.com
```

4. **Run the application:**
```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Database Setup

The application will automatically create the required tables:
- `r_users` - Trial user management
- `r_waitlist` - Email waitlist
- `r_processing_jobs` - Processing job tracking

**SQLite Database File**: `rawbify.db` will be created in the project root.

### Docker Deployment

1. **Build the image:**
```bash
docker build -t rawbify-backend .
```

2. **Run the container:**
```bash
docker run -p 8000:8000 --env-file .env rawbify-backend
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Testing

### Test User IDs
For development, you can manually insert test users:
```sql
INSERT INTO r_users (email, user_id, trial_access_granted) 
VALUES ('test@example.com', 'test123', 1);
```

Or use the provided script:
```bash
python scripts/add_test_users.py
```

### API Testing
```bash
# Test waitlist
curl -X POST "http://localhost:8000/api/waitlist/join" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Test user validation
curl -X POST "http://localhost:8000/api/validate-user" \
  -H "Content-Type: application/json" \
  -d '{"userId": "test123"}'
```

## Frontend Integration

Update your frontend API calls to point to the backend:
```javascript
// In your frontend services/api.ts
const API_BASE_URL = 'http://localhost:8000/api';

// Update the fetch URLs to use the new endpoints
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./rawbify.db` |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |
| `SENDGRID_API_KEY` | SendGrid API key for emails | Optional |
| `FROM_EMAIL` | Sender email address | `noreply@rawbify.com` |
| `MAX_FILE_SIZE` | Maximum file upload size | `10485760` (10MB) |

## Development

### Project Structure
```
rawbify-backend/
├── app/
│   ├── api/           # API routes
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # Business logic
│   ├── config.py      # Configuration
│   ├── database.py    # Database setup
│   └── main.py        # FastAPI app
├── requirements.txt   # Dependencies
├── Dockerfile         # Docker configuration
├── rawbify.db         # SQLite database (created automatically)
└── main.py           # Entry point
```

### Adding New Features

1. **Models**: Add SQLAlchemy models in `app/models/`
2. **Schemas**: Add Pydantic schemas in `app/schemas/`
3. **Services**: Add business logic in `app/services/`
4. **API Routes**: Add endpoints in `app/api/`
5. **Update main.py**: Include new routers

## Production Deployment

### Switching to PostgreSQL
For production, update your `DATABASE_URL`:
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/rawbify
```

### GCP Cloud Run
1. Build and push Docker image to Container Registry
2. Deploy to Cloud Run with environment variables
3. Set up Cloud SQL connection

### Environment Variables for Production
```env
DATABASE_URL=postgresql://user:pass@/dbname?host=/cloudsql/project:region:instance
CORS_ORIGINS=https://rawbify.com
SENDGRID_API_KEY=your_production_key
``` 