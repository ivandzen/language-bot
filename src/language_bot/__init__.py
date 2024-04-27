# SPDX-FileCopyrightText: 2024-present Ivan Loboda <loboda.ivan.y@gmail.com>
#
# SPDX-License-Identifier: MIT

import logging
import sys
from telegram import Update
from telegram.ext import (ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler,
                          ChatMemberHandler, CallbackQueryHandler, StringCommandHandler)

from .common.config import Config, init_config
from .translators import init_translation_service
from .session.session import get_session
from .common.database import Database
from .service_context import ServiceContext
from .chatbots.gpt4all_bot import GPT4AllService

logLevels = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG
}

config: Config = init_config(sys.argv[1])
logging.basicConfig(level=logLevels.get(config.LOG_LEVEL))
logger = logging.getLogger(__name__)
logger.info("Starting Language Bot")
translation_service=init_translation_service(config)
database = Database(config)
gpt4all_service = GPT4AllService()


def bot_event_handler(method_name):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        with database.begin() as cur:
            session = get_session(
                platform="tg",
                platform_user_id=str(update.effective_user.id),
                chatbot_service=gpt4all_service,
                cur=cur
            )
            await getattr(session, method_name)(
                ServiceContext(
                    update=update,
                    context=context,
                    translation_service=translation_service,
                    cur=cur,
                )
            )
            database.commit()

    return wrapper


telegram_app = ApplicationBuilder().token(config.TG_API_KEY).build()
telegram_app.add_handler(CommandHandler(command="start", callback=bot_event_handler("start_command_handler")))
telegram_app.add_handler(CommandHandler(command="menu", callback=bot_event_handler("menu_command_handler")))
telegram_app.add_handler(MessageHandler(filters=None, callback=bot_event_handler("message_handler")))
telegram_app.add_handler(CallbackQueryHandler(callback=bot_event_handler("callback_query_handler")))

logger.info("Starting Telegram Bot...")
telegram_app.run_polling()
