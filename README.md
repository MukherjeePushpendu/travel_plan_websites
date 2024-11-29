# TravelBuddy

A simple web application to help solo travelers connect and plan trips together.

## Features

- User registration and authentication
- Create and manage trips
- View trips dashboard
- Simple and intuitive interface

## Prerequisites

- Python 3.9 or higher
- Docker (optional)

## Running Locally

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

The application will be available at http://localhost:5000

## Running with Docker

1. Build the Docker image:
```bash
docker build -t travel-buddy .
```

2. Run the container:
```bash
docker run -p 5000:5000 travel-buddy
```

The application will be available at http://localhost:5000

## Project Structure

- `app.py`: Main application file with routes and models
- `requirements.txt`: Python dependencies
- `templates/`: HTML templates
  - `base.html`: Base template with common elements
  - `home.html`: Landing page
  - `register.html`: User registration form
  - `login.html`: Login form
  - `dashboard.html`: User dashboard showing trips
  - `create_trip.html`: Form to create new trips

## Database

The application uses SQLite as the database, which is stored in `travelbuddy.db`. The database will be automatically created when you first run the application.
