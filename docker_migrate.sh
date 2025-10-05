#!/bin/bash
# Docker migration script for the ML model fix

echo "🐳 Docker Migration Script for ML Model Fix"
echo "============================================"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install Docker Compose."
    exit 1
fi

# Function to check if containers are running
check_containers() {
    if docker-compose ps | grep -q "Up"; then
        return 0
    else
        return 1
    fi
}

echo ""
echo "📋 Available migration options:"
echo "1. Automatic migration (rebuild and restart)"
echo "2. Manual migration (run inside existing container)"
echo "3. Direct database migration"
echo "4. Just show status"
echo ""

read -p "Choose option (1-4): " choice

case $choice in
    1)
        echo ""
        echo "🔄 Option 1: Automatic migration (recommended)"
        echo "This will rebuild the container with the updated code and restart services."
        echo ""
        read -p "Continue? (y/N): " confirm
        if [[ $confirm =~ ^[Yy]$ ]]; then
            echo "⏹️  Stopping containers..."
            docker-compose down
            
            echo "🔨 Rebuilding web container..."
            docker-compose build web
            
            echo "🚀 Starting containers..."
            docker-compose up -d
            
            echo "📋 Checking status..."
            sleep 5
            docker-compose ps
            
            echo ""
            echo "✅ Migration completed! Check logs with: docker-compose logs web"
        fi
        ;;
    2)
        echo ""
        echo "🔧 Option 2: Manual migration"
        if check_containers; then
            echo "Running migration inside container..."
            docker-compose exec web python migrate_docker.py
        else
            echo "Containers not running. Starting them first..."
            docker-compose up -d
            sleep 10
            echo "Running migration..."
            docker-compose exec web python migrate_docker.py
        fi
        ;;
    3)
        echo ""
        echo "🗄️  Option 3: Direct database migration"
        if check_containers; then
            echo "Connecting to database container..."
            echo "Run these commands in the PostgreSQL prompt:"
            echo ""
            echo "ALTER TABLE exoplanet_candidates ADD COLUMN IF NOT EXISTS koi_fpflag_ss INTEGER;"
            echo "ALTER TABLE exoplanet_candidates ADD COLUMN IF NOT EXISTS koi_fpflag_co INTEGER;"
            echo "ALTER TABLE exoplanet_candidates ADD COLUMN IF NOT EXISTS koi_fpflag_nt INTEGER;"
            echo "ALTER TABLE exoplanet_candidates ADD COLUMN IF NOT EXISTS koi_fpflag_ec INTEGER;"
            echo ""
            echo "Press Enter to connect to database..."
            read
            docker-compose exec db psql -U exoplanet_user -d exoplanet_research
        else
            echo "❌ Containers not running. Start them first with: docker-compose up -d"
        fi
        ;;
    4)
        echo ""
        echo "📊 Current status:"
        docker-compose ps
        echo ""
        echo "📋 Recent logs:"
        docker-compose logs --tail=20 web
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

echo ""
echo "🎉 Migration script completed!"
echo ""
echo "Next steps:"
echo "- Test CSV upload to verify the fix works"
echo "- Check logs: docker-compose logs web"
echo "- Monitor application: docker-compose ps"