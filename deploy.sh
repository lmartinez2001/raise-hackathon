#!/bin/bash

# Production deployment script for Vultr
set -e

echo "🚀 Starting deployment process..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-pip python3-venv nginx nodejs npm

# Install Node.js 18+ (required for Next.js)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Navigate to project directory
cd /home/ubuntu/hackathon

# Backend setup
echo "📦 Setting up backend..."
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install gunicorn
pip install -e .

# Copy production environment
cp .env.production .env

echo "🌐 Setting up frontend..."
cd ../frontend

# Install dependencies and build
npm install
npm run build

echo "✅ Application setup complete!"
echo "Next steps:"
echo "1. Update environment variables in .env files"
echo "2. Configure systemd service"
echo "3. Configure Nginx"
echo "4. Set up SSL certificate"
