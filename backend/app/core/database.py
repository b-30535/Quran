import logging
from typing import Any

from pymongo import AsyncMongoClient
from pymongo.errors import PyMongoError

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: AsyncMongoClient | None = None
_database: Any = None


async def connect_to_mongo() -> None:
    """Connect to MongoDB and create indexes needed for account uniqueness."""
    global _client, _database

    if not settings.mongodb_uri.strip():
        logger.warning("MONGODB_URI is not configured; database features are unavailable.")
        return

    _client = AsyncMongoClient(
        settings.mongodb_uri,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        appname="NoorAlQuran",
    )
    try:
        await _client.admin.command("ping")
        _database = _client[settings.mongodb_database]
        await _database.users.create_index("email", unique=True, name="users_email_unique")
        logger.info("Connected to MongoDB database '%s'.", settings.mongodb_database)
    except PyMongoError:
        await _client.close()
        _client = None
        _database = None
        logger.exception("Could not connect to MongoDB.")
        raise


async def close_mongo_connection() -> None:
    global _client, _database
    if _client is not None:
        await _client.close()
    _client = None
    _database = None


def get_database() -> Any:
    if _database is None:
        raise RuntimeError("Database is not configured or connected. Set MONGODB_URI.")
    return _database


def database_is_connected() -> bool:
    return _database is not None
