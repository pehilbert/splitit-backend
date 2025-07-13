# Flask REST API

This project is a Flask REST API that uses SQLAlchemy for database interactions and is set up to run with Docker and Docker Compose. It connects to a PostgreSQL database.

## Project Structure

```
flask-rest-api
├── app
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   └── config.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd flask-rest-api
   ```

2. **Build and run the application using Docker Compose:**
   ```
   docker-compose up --build
   ```

3. **Access the API:**
   The API will be available at `http://localhost:5000`.

## Usage

- The API supports various endpoints defined in `app/routes.py`. You can interact with the API using tools like Postman or curl.

## Dependencies

The project requires the following Python packages, which are listed in `requirements.txt`:

- Flask
- SQLAlchemy
- psycopg2-binary

## Contributing

Feel free to submit issues or pull requests for improvements or bug fixes. 

## License

This project is licensed under the MIT License.