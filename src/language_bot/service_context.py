from dataclasses import dataclass
from psycopg2.extensions import cursor
from telegram import Update
from telegram.ext import ContextTypes

from .translators.translation_service_interface import TranslationServiceInterface


@dataclass
class ServiceContext:
    update: Update
    context: ContextTypes.DEFAULT_TYPE
    translation_service: TranslationServiceInterface
    cur: cursor
