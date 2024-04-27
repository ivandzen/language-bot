import logging

from .config import Config
import psycopg2
import psycopg2.extras
from psycopg2.extensions import cursor
from time import sleep


logger = logging.getLogger(__name__)


class Database:
    _conn: any = None
    _config: Config

    def __init__(self, config: Config):
        self._config = config
        psycopg2.extras.register_uuid()
        self._reconnect()

    def _reconnect(self):
        logger.info("Initializing Database connection...")
        # Close old connection
        if self._conn:
            self._conn.close()

        # Reconnect
        self._conn = psycopg2.connect(
            dbname=self._config.DB_NAME,
            user=self._config.DB_USER,
            password=self._config.DB_PASSWORD,
            host=self._config.DB_HOST
        )

    def begin(self) -> cursor:
        try:
            return self._conn.cursor()
        except psycopg2.InterfaceError as e:
            logger.info(f'{e} - Database connection will be reset')
            sleep(2)
            self._reconnect()
            return self._conn.cursor()

    def commit(self):
        try:
            self._conn.commit()
        except psycopg2.InterfaceError as e:
            logger.info(f'{e} - Database connection will be reset')
            sleep(2)
            self._reconnect()

    def rollback(self):
        try:
            self._conn.rollback()
        except psycopg2.InterfaceError as e:
            logger.info(f'{e} - Database connection will be reset')
            sleep(2)
            self._reconnect()
