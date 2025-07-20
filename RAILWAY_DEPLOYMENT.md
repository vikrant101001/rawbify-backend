# Railway Deployment Guide

## Prerequisites
- Railway account
- PostgreSQL database (Railway provides this)

## Deployment Steps

### 1. Connect to Railway
- Connect your GitHub repository to Railway
- Railway will automatically detect the Python project

### 2. Environment Variables
Set these environment variables in Railway:

```
DATABASE_URL=postgresql://... (Railway provides this automatically)
ENVIRONMENT=production
SENDGRID_API_KEY=your_sendgrid_key (optional)
FROM_EMAIL=noreply@rawbify.com (optional)
```

### 3. Build Configuration
Railway will use:
- `requirements.txt` for dependencies
- `Procfile` for startup command
- `runtime.txt` for Python version

### 4. Database Setup
The application will automatically create tables on first run.

### 5. Test Users
After deployment, you can add test users using:
```bash
python scripts/add_test_users.py
```

## Troubleshooting

### Missing Dependencies
If you see "ModuleNotFoundError", check that `requirements.txt` includes:
- pandas
- openpyxl
- psycopg2-binary
- fastapi
- uvicorn

### Database Connection
- Railway automatically provides `DATABASE_URL`
- The app converts `postgres://` to `postgresql://` automatically

### CORS Issues
- Make sure your frontend domain is in `CORS_ORIGINS` in `config.py`

## API Endpoints
- Health check: `GET /health`
- API base: `/api`
- Waitlist: `POST /api/waitlist`
- User validation: `POST /api/validate-user`
- Process data: `POST /api/process-data` 