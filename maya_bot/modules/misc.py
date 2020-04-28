# Copyright © 2018, 2019 MrYacha
# This file is part of SophieBot.
#
# SophieBot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SophieBot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License

import random

from requests import post

from aiogram.utils.exceptions import BadRequest

import maya_bot.modules.helper_func.bot_rights as bot_rights
from maya_bot import OWNER_ID, SUDO, BOT_ID, tbot, decorator, mongodb, bot
from maya_bot.modules.disable import disablable_dec
from maya_bot.modules.connections import connection
from maya_bot.modules.language import get_strings_dec
from maya_bot.modules.users import (user_admin_dec, aio_get_user, is_user_premium,
                                    user_link_html, is_user_admin, update_admin_cache)


@decorator.command("id")
@disablable_dec("id")
@get_strings_dec('misc')
async def get_id(message, strings):
    user, txt = await aio_get_user(message, allow_self=True)
    if not user:
        return
    text = strings["your_id"].format(message.from_user.id)
    if message.chat.id != message.from_user.id:
        text += strings["chat_id"].format(message.chat.id)

    if not user['user_id'] == message.from_user.id:
        userl = await user_link_html(user['user_id'])
        text += strings["user_id"].format(userl, user['user_id'])

    if "reply_to_message" in message and "forward_from" in message.reply_to_message and not \
       message.reply_to_message.forward_from.id == message.reply_to_message.from_user.id:
        userl = await user_link_html(message.reply_to_message.forward_from.id)
        text += strings["user_id"].format(userl, message.reply_to_message.forward_from.id)

    await message.reply(text)


@decorator.command("pin")
@user_admin_dec
@bot_rights.pin_messages()
@get_strings_dec('misc')
async def pinMessage(message, strings):
    if 'reply_to_message' not in message:
        await message.reply(strings['no_reply_msg'])
        return
    msg_2_pin = message.reply_to_message.message_id
    args = message.get_args().lower()
    tru_txt = ['loud', 'notify']
    if args in tru_txt:
        notify = False
    else:
        notify = True
    try:
        await bot.pin_chat_message(message.chat.id, msg_2_pin, disable_notification=notify)
    except BadRequest:
        await message.reply(strings['chat_not_modified_pin'])
        return


@decorator.command("runs")
@get_strings_dec("RUNS", mas_name="RANDOM_STRINGS")
async def runs(message, strings):
    await message.reply(strings[random.choice(list(strings))])


@decorator.command("unpin")
@user_admin_dec
@bot_rights.pin_messages()
@connection(admin=True, only_in_groups=True)
@get_strings_dec('misc')
async def unpin_message(message, strings, status, chat_id, chat_title):
    try:
        await bot.unpin_chat_message(chat_id)
    except BadRequest:
        await message.reply(strings['chat_not_modified_unpin'])
        return


@decorator.command("promote")
@bot_rights.add_admins()
@user_admin_dec
@connection(admin=True, only_in_groups=True)
@get_strings_dec('misc')
async def promote(message, strings, status, chat_id, chat_title):
    user, args = await aio_get_user(message)

    if not user:
        return

    text = strings['promote_success'].format(
        user=await user_link_html(user['user_id']),
        chat_name=chat_title
    )

    if args:
        title = args
        if len(title) > 16:
            await message.reply(strings['rank_to_loong'])
            return
        text += strings['promote_title'].format(role=title)
    else:
        title = args

    await tbot.edit_admin(
        chat_id,
        user['user_id'],
        add_admins=True,
        invite_users=True,
        change_info=True,
        ban_users=True,
        delete_messages=True,
        pin_messages=True,
        title=title
    )
    await update_admin_cache(chat_id)
    await message.reply(text)

    # except BadRequestError:
    #    await message.reply(strings['promote_failed'])
    #    return


@decorator.command("demote")
@bot_rights.add_admins()
@user_admin_dec
@connection(admin=True, only_in_groups=True)
@get_strings_dec('misc')
async def demote(message, strings, status, chat_id, chat_title):
    user, txt = await aio_get_user(message)
    if not user:
        return

    if user['user_id'] == BOT_ID:
        return

    await bot.promote_chat_member(
        chat_id,
        user['user_id']
    )

    # await message.reply(strings['demote_failed'])
    # return
    await update_admin_cache(chat_id)
    await message.reply(strings['demote_success'].format(
        user=await user_link_html(user['user_id']),
        chat_name=chat_title
    ))


@decorator.command('paste')
@get_strings_dec('misc')
async def paste_deldog(message, strings, **kwargs):
    DOGBIN_URL = "https://del.dog/"
    dogbin_final_url = None
    to_paste = None

    if 'reply_to_message' in message:
        to_paste = message.reply_to_message.text
    else:
        to_paste = message.text.split(' ', 1)[1]

    if not to_paste:
        await message.reply(strings['paste_no_text'])
        return

    resp = post(DOGBIN_URL + "documents", data=to_paste.encode('utf-8'))

    if resp.status_code == 200:
        response = resp.json()
        key = response['key']
        dogbin_final_url = DOGBIN_URL + key

        if response['isUrl']:
            full_url = "{}v/{}".format(DOGBIN_URL, key)
            reply_text = (strings["paste_success_extra"].format(dogbin_final_url, full_url))
        else:
            reply_text = (strings["paste_success"].format(dogbin_final_url))
    else:
        reply_text = (strings["paste_fail"])

    await message.reply(reply_text, disable_web_page_preview=True)


@decorator.command("info")
@get_strings_dec("misc")
async def user_info(message, strings, **kwargs):
    user, txt = await aio_get_user(message, allow_self=True)
    if not user:
        return

    chat_id = message.chat.id
    from_id = message.from_user.id

    text = strings["user_info"]
    text += strings["info_id"].format(id=user['user_id'])

    text += strings["info_first"].format(first_name=str(user['first_name']))

    if user['last_name'] is not None:
        text += strings["info_last"].format(last_name=str(user['last_name']))

    if user['username'] is not None:
        text += strings["info_username"].format(username="@" + str(user['username']))

    text += strings['info_link'].format(user_link=str(await user_link_html(user['user_id'])))

    text += '\n'

    if await is_user_admin(chat_id, user['user_id']) is True:
        text += strings['info_admeme']

    text += strings['info_saw'].format(num=len(user['chats']))

    if user['user_id'] == OWNER_ID:
        text += strings["father"]
    elif user['user_id'] in SUDO:
        text += strings['sudo_crown']
    elif is_user_premium(user['user_id']):
        text += strings['user_premium']
    else:
        text += "\n"

        fed = mongodb.fed_groups.find_one({'chat_id': chat_id})
        if fed:
            fbanned = mongodb.fbanned_users.find_one({'user': from_id, 'fed_id': fed['fed_id']})
            text += strings['info_fbanned']
            if fbanned:
                text += strings['gbanned_yes']
                text += strings["gbanned_reason"].format(reason=fbanned['reason'])
            else:
                text += strings['no']
        text += strings["gbanned"]

        check = mongodb.blacklisted_users.find_one({'user': user['user_id']})
        if check:
            text += strings['gbanned_yes']
            text += strings["gbanned_date"].format(data=check['date'])
            text += strings["gbanned_reason"].format(reason=check['reason'])
        else:
            text += strings['no']

    await message.reply(text)
