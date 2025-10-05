#!/bin/bash

echo "Stopping all running containers..."
docker compose down

echo "Removing postgres volume..."
docker volume rm nasa_exoplanets_postgres_data

echo "Removing any remaining containers..."
docker compose rm -f

echo "Rebuilding and starting services..."
docker compose up -d --build

echo "Waiting for database to be ready..."
sleep 5

echo "Running database initialization..."
docker compose exec web python -m app.db.init_db

echo "Database has been reset and reinitialized!"
