# Rawbify Backend - Vercel Deployment Guide

## Overview
This guide will help you deploy your FastAPI backend from Railway to Vercel.

## Prerequisites
- Vercel account (free tier available)
- GitHub repository with your backend code
- Database solution (Neon PostgreSQL, Supabase, or PlanetScale)

## Step 1: Database Setup

Since Vercel doesn't provide managed databases, you'll need a serverless database:

### Option A: Neon PostgreSQL (Recommended)
1. Go to [neon.tech](https://neon.tech)
2. Sign up for free account
3. Create a new project
4. Copy the connection string (looks like: `postgresql://user:pass@host/db?sslmode=require`)

### Option B: Supabase
1. Go to [supabase.com](https://supabase.com)
2. Create new project
3. Go to Settings > Database
4. Copy the connection string

### Option C: PlanetScale
1. Go to [planetscale.com](https://planetscale.com)
2. Create new database
3. Get connection string

## Step 2: Deploy to Vercel

### 2.1 Connect Repository
1. Go to [vercel.com](https://vercel.com)
2. Click "New Project"
3. Import your GitHub repository
4. Select the `rawbify-backend` folder as the root directory

### 2.2 Configure Build Settings
- **Framework Preset**: Other
- **Root Directory**: `rawbify-backend`
- **Build Command**: (leave empty)
- **Output Directory**: (leave empty)
- **Install Command**: `pip install -r requirements.txt`

### 2.3 Environment Variables
Add these environment variables in Vercel dashboard:

```
DATABASE_URL=your_postgresql_connection_string
ENVIRONMENT=production
OPENAI_API_KEY=your_openai_api_key
SENDGRID_API_KEY=your_sendgrid_key (optional)
FROM_EMAIL=noreply@rawbify.com
GMAIL_USER=your_gmail_user (optional)
GMAIL_APP_PASSWORD=your_gmail_app_password (optional)
```

## Step 3: Update Frontend Configuration

Update your frontend to point to the new Vercel backend URL.

## Step 4: Test Deployment

After deployment, test these endpoints:
- `GET /` - Should return API info
- `GET /health` - Should return {"status": "healthy"}
- `POST /api/waitlist/join` - Test waitlist functionality
- `POST /api/validate-user` - Test user validation

## Important Notes

### Database Considerations
- **SQLite won't work on Vercel** (serverless environment)
- Use PostgreSQL-compatible database
- Connection pooling is handled automatically by most providers

### File Uploads
- Vercel has request size limits (4.5MB for Hobby, 100MB for Pro)
- For larger files, consider using:
  - Direct S3 uploads with presigned URLs
  - Cloudinary for file processing
  - Vercel Blob for file storage

### Cold Starts
- First request might be slower (serverless cold start)
- Consider implementing a health check ping

### Limitations
- Function timeout: 10s (Hobby), 60s (Pro)
- Memory limit: 1024MB (Hobby), 3008MB (Pro)
- No persistent file system

## Troubleshooting

### Common Issues

1. **Module Import Errors**
   - Ensure all dependencies are in `requirements.txt`
   - Check Python version compatibility

2. **Database Connection Errors**
   - Verify DATABASE_URL format
   - Ensure database allows external connections
   - Check SSL requirements

3. **CORS Issues**
   - Update CORS_ORIGINS in config.py
   - Add your Vercel domain

4. **File Upload Issues**
   - Check file size limits
   - Ensure multipart/form-data is supported

### Environment-Specific Config

The app will automatically:
- Create database tables on first run
- Handle PostgreSQL URL format conversion
- Set appropriate CORS origins

## Migration from Railway

1. Export any data from Railway database
2. Import to new PostgreSQL database
3. Update environment variables
4. Deploy to Vercel
5. Update frontend configuration
6. Test all functionality

## Cost Comparison

| Feature | Railway (Free) | Vercel (Hobby) | Vercel (Pro) |
|---------|----------------|----------------|--------------|
| Price | $0 (trial only) | $0 | $20/month |
| Function timeout | 500MB | 10s | 60s |
| Memory | 512MB | 1024MB | 3008MB |
| Requests | Limited | 100GB bandwidth | 1000GB bandwidth |
| Database | Included | Separate cost | Separate cost |

**Database costs (monthly):**
- Neon: $0-19 (512MB-3GB)
- Supabase: $0-25 (500MB-8GB)
- PlanetScale: $0-39 (1-5GB)

## Next Steps

1. Set up your chosen database
2. Deploy to Vercel
3. Update frontend configuration
4. Test thoroughly
5. Consider upgrading to Pro if you need longer function timeouts
