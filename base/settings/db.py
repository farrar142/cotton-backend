from os import getenv
from dotenv import load_dotenv

load_dotenv()
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": getenv("DB_NAME"),  # Replace with your database name
        "USER": getenv("DB_USER"),  # Replace with your PostgreSQL username
        "PASSWORD": getenv("DB_PASSWORD"),  # Replace with your PostgreSQL password
        "HOST": getenv(
            "DB_HOST"
        ),  # Replace with the hostname of your PostgreSQL server (e.g., "127.0.0.1")
        "PORT": getenv(
            "DB_PORT"
        ),  # Replace with the port number used by your PostgreSQL server (default is 5432),
        "TEST": {
            "MIRROR": "default",
        },
    }
}
