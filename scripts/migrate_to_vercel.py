#!/usr/bin/env python3
"""
Script to help migrate from Railway to Vercel deployment
"""
import os
import sys
import json
from datetime import datetime

def create_env_template():
    """Create a .env template for Vercel deployment"""
    env_template = """# Vercel Environment Variables Template
# Copy these to your Vercel dashboard under Settings > Environment Variables

# Database (Required)
DATABASE_URL=postgresql://user:password@host:5432/database?sslmode=require

# Application Environment
ENVIRONMENT=production

# OpenAI API (Required for processing)
OPENAI_API_KEY=sk-your-openai-api-key

# Email Configuration (Optional - choose one)
SENDGRID_API_KEY=SG.your-sendgrid-key
FROM_EMAIL=noreply@rawbify.com

# OR Gmail SMTP
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-16-character-app-password

# CORS Origins (automatically configured in config.py)
# These are already set in the code, no need to configure manually
"""
    
    with open('.env.vercel.template', 'w') as f:
        f.write(env_template)
    
    print("✅ Created .env.vercel.template")
    print("📝 Use this as a reference for setting up Vercel environment variables")

def check_requirements():
    """Check if all requirements are compatible with Vercel"""
    print("🔍 Checking requirements.txt compatibility...")
    
    with open('requirements.txt', 'r') as f:
        requirements = f.read()
    
    # Check for potential issues
    issues = []
    warnings = []
    
    if 'sqlite' in requirements.lower():
        issues.append("❌ SQLite detected - won't work on Vercel (serverless)")
    
    if 'psycopg2-binary' not in requirements:
        warnings.append("⚠️  Consider adding psycopg2-binary for PostgreSQL")
    
    # Check file sizes for large packages
    large_packages = ['tensorflow', 'torch', 'opencv']
    for pkg in large_packages:
        if pkg in requirements.lower():
            warnings.append(f"⚠️  {pkg} is large - may cause deployment issues")
    
    if issues:
        print("\n🚨 Critical Issues:")
        for issue in issues:
            print(f"  {issue}")
        print("\n💡 Solution: Use PostgreSQL database (Neon, Supabase, or PlanetScale)")
    
    if warnings:
        print("\n⚠️  Warnings:")
        for warning in warnings:
            print(f"  {warning}")
    
    if not issues and not warnings:
        print("✅ Requirements look good for Vercel deployment!")
    
    return len(issues) == 0

def create_vercel_json():
    """Create or update vercel.json with optimized settings"""
    vercel_config = {
        "version": 2,
        "builds": [
            {
                "src": "main.py",
                "use": "@vercel/python"
            }
        ],
        "routes": [
            {
                "src": "/(.*)",
                "dest": "main.py"
            }
        ],
        "env": {
            "PYTHONPATH": "."
        },
        "functions": {
            "main.py": {
                "maxDuration": 30,
                "memory": 1024
            }
        }
    }
    
    with open('vercel.json', 'w') as f:
        json.dump(vercel_config, f, indent=2)
    
    print("✅ Created/updated vercel.json")

def print_deployment_checklist():
    """Print a deployment checklist"""
    checklist = """
🚀 Vercel Deployment Checklist

📋 Pre-deployment:
  □ Set up PostgreSQL database (Neon/Supabase/PlanetScale)
  □ Get database connection string
  □ Prepare OpenAI API key
  □ Push code to GitHub

🔧 Vercel Setup:
  □ Connect GitHub repository to Vercel
  □ Set root directory to 'rawbify-backend'
  □ Configure environment variables (see .env.vercel.template)
  □ Deploy!

🧪 Post-deployment Testing:
  □ Test GET / endpoint
  □ Test GET /health endpoint
  □ Test POST /api/waitlist/join
  □ Test POST /api/validate-user
  □ Test POST /api/process-data

🔄 Frontend Update:
  □ Update rawbify/app/config/api.ts with new Vercel URL
  □ Test frontend-backend integration

💡 Tips:
  - First deployment might take 2-3 minutes
  - Cold starts can add 1-2 seconds to first request
  - Monitor function duration (30s limit on free tier)
  - Check Vercel logs for any errors
"""
    print(checklist)

def main():
    print("🚀 Rawbify Backend - Vercel Migration Helper\n")
    
    # Check if we're in the right directory
    if not os.path.exists('requirements.txt'):
        print("❌ requirements.txt not found. Please run this from rawbify-backend directory.")
        sys.exit(1)
    
    # Check requirements compatibility
    if not check_requirements():
        print("\n❌ Please fix critical issues before deploying to Vercel")
        sys.exit(1)
    
    # Create configuration files
    create_env_template()
    create_vercel_json()
    
    # Print checklist
    print_deployment_checklist()
    
    print("\n✅ Migration preparation complete!")
    print("📁 Files created:")
    print("  - .env.vercel.template (environment variables reference)")
    print("  - vercel.json (deployment configuration)")
    print("\n🔗 Next: Follow the deployment checklist above")

if __name__ == "__main__":
    main()
