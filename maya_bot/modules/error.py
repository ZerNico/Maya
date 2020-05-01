# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2019 Aiogram

#
# This file is part of SophieBot.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import html
import sys

from redis.exceptions import RedisError

from maya_bot import dp, bot, OWNER_ID
from maya_bot.services.redis import redis
from maya_bot.utils.logger import log

SENT = []


def catch_redis_error(**dec_kwargs):
    def wrapped(func):
        async def wrapped_1(*args, **kwargs):
            global SENT
            # We can't use redis here
            # So we save data - 'message sent to' in a list variable
            message = args[0]
            msg = message.callback_query.message if 'callback_query' in message else message.message
            chat_id = msg.chat.id
            try:
                return await func(*args, **kwargs)
            except RedisError:
                if chat_id not in SENT:
                    text = 'Sorry for inconvience! I encountered error in my redis DB, which is necessary for running '\
                           'bot \n\nPlease report this to my support group immediately when you see this error!'
                    if await bot.send_message(chat_id, text):
                        SENT.append(chat_id)
                # Alert bot owner
                if OWNER_ID not in SENT:
                    text = 'Maya panic: Got redis error'
                    if await bot.send_message(OWNER_ID, text):
                        SENT.append(OWNER_ID)
                return False
        return wrapped_1
    return wrapped


@dp.errors_handler()
@catch_redis_error()
async def all_errors_handler(message, dp):
    msg = message.callback_query.message if 'callback_query' in message else message.message
    chat_id = msg.chat.id
    err_tlt = sys.exc_info()[0].__name__
    err_msg = str(sys.exc_info()[1])

    if redis.get(chat_id) == err_tlt:
        # by err_tlt we assume that it is same error
        return

    if err_tlt == 'BadRequest' and err_msg == 'Have no rights to send a message':
        return True

    text = "<b>Sorry, I encountered a error!</b>\n"
    text += f'<code>{html.escape(err_tlt)}: {html.escape(err_msg)}</code>'
    redis.set(chat_id, err_tlt, ex=120)
    await bot.send_message(chat_id, text, reply_to_message_id=msg.message_id)

    # Protect Privacy
    msg['chat'] = ['HIDDEN']
    msg['from'] = ['HIDDEN']
    msg['message_id'] = ['HIDDEN']
    if hasattr(msg, 'reply_to_message'):
        msg['reply_to_message'] = ['HIDDEN']

    log.error('Error caused update is: \n' + str(msg))
