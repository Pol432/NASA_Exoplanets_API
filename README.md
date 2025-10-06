# NASA Exoplanet Research Platform

A FastAPI-based platform for collaborative exoplanet detection and analysis. This project provides a robust API for processing, analyzing, and managing exoplanet data using machine learning techniques.

## Features

- 🪐 Exoplanet data processing and analysis
- 🤖 Machine learning models for exoplanet detection
- 🔐 Secure authentication and authorization
- 📊 Data upload and processing capabilities
- 💡 Feedback system for collaborative research
- 📈 Bulk analysis support
- 🔍 Advanced querying and filtering options

## Technology Stack

- **Framework:** FastAPI 0.104.1
- **Database:** PostgreSQL with SQLAlchemy 2.0.0
- **Authentication:** JWT with Python-Jose
- **ML Libraries:**
  - scikit-learn 1.6.1
  - pandas 2.2.2
  - numpy 2.0.0
- **Development:** Python 3.13+

## Prerequisites

- Python 3.13 or higher
- PostgreSQL database
- Docker (optional, for containerized deployment)

## Installation and Setup

### Using Docker (Recommended)

The easiest way to run the application is using Docker, which ensures consistent environments and easy setup:

1. Clone the repository:

```bash
git clone https://github.com/Pol432/NASA_Exomplanets_API.git
cd NASA_Exomplanets_API
```

2. Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql://user:password@db:5432/exoplanets
API_V1_STR=/api/v1
SECRET_KEY=your-secret-key
DEBUG=False
```

3. Build and start the containers:

```bash
docker-compose up -d --build
```

This will set up both the API and PostgreSQL database in containers, handle all dependencies, and initialize the database automatically.

### Manual Setup (Alternative)

If you prefer not to use Docker, you'll need:

- PostgreSQL installed and running
- Python 3.13+ installed

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up environment variables and initialize the database as described in the `.env` example above (using localhost for DATABASE_URL)

3. Run the application:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Key API Endpoints

### Authentication

```
POST /api/v1/auth/register         # Register new user
POST /api/v1/auth/login           # Login and get access token
GET  /api/v1/auth/me              # Get current user profile
```

### Data Upload and Management

```
POST /api/v1/data/upload-csv      # Upload astronomical data CSV file
GET  /api/v1/data/uploads/me      # Get user's uploaded candidates
GET  /api/v1/data/candidates      # List all candidates with filters
```

### AI Analysis

```
POST /api/v1/analysis/predict/{candidate_id}    # Run AI analysis on a candidate
POST /api/v1/analysis/bulk-predict              # Analyze multiple candidates
GET  /api/v1/analysis/results/{candidate_id}    # Get analysis results
PUT  /api/v1/analysis/results/{candidate_id}/verdict  # Update researcher's verdict
```

For complete API documentation, once the application is running, you can access:

- Interactive API documentation (Swagger UI): `http://localhost:8000/api/v1/docs`
- Alternative API documentation (ReDoc): `http://localhost:8000/api/v1/redoc`

### Example Workflow

1. Register and obtain an authentication token
2. Upload a CSV file containing astronomical data
3. Run AI analysis on the uploaded candidates
4. Review the AI predictions and provide researcher verdicts
5. Use bulk analysis for processing multiple candidates efficiently

## Project Structure

```
app/
├── api/           # API endpoints and routers
├── core/          # Core configurations
├── db/            # Database models and initialization
├── ml/            # Machine learning models and handlers
├── models/        # SQLAlchemy models
├── schemas/       # Pydantic schemas
├── services/      # Business logic
└── utils/         # Utility functions
```

## Testing

Run the tests using pytest:

```bash
pytest
```

For testing requirements:

```bash
pip install -r tests/requirements-test.txt
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## Acknowledgments

- NASA for providing exoplanet data
- FastAPI for the excellent framework
- The open-source community for their invaluable contributions
