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

from telethon.tl.custom import Button

from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters.builtin import CommandStart

from maya_bot import BOT_USERNAME, decorator, logger, dp, bot, CONFIG
from maya_bot.modules.language import (LANGUAGES, get_chat_lang, get_string,
                                       lang_info, get_strings_dec, get_strings)

from aiogram.utils.callback_data import CallbackData
help_page_cp = CallbackData('help_page', 'module')
help_btn_cp = CallbackData('help_btn', 'module', 'btn')
NO_LOAD_MODULES = CONFIG["advanced"]["not_load_this_modules"]

# Generate help cache
HELP = []
for module in LANGUAGES['en']['HELPS']:
    if module not in NO_LOAD_MODULES:
        logger.debug("Loading help for " + module)
        HELP.append(module)
HELP = sorted(HELP)
logger.info("Help loaded for: {}".format(HELP))


@decorator.command('start', args=False, only_groups=True)
async def start(event):
    await event.reply('Hey there, My name is Maya!')
    return


@decorator.command('start', args=False, only_pm=True)
async def start_pm(message):
    text, buttons = get_start(message.chat.id)
    await message.reply(text, reply_markup=buttons)


@decorator.command('help', only_groups=True)
@get_strings_dec('misc')
async def help_btn(message, strings):
    buttons = InlineKeyboardMarkup().add(InlineKeyboardButton(
        strings['help_btn'], url=f'https://t.me/{BOT_USERNAME}?start=help'
    ))
    text = strings['help_txt']
    await message.reply(text, reply_markup=buttons)


@decorator.command('help', only_pm=True)
async def help(message):
    text, buttons = get_help(message.chat.id)
    await message.reply(text, reply_markup=buttons)


@decorator.CallBackQuery(b'get_start')
async def get_start_callback(event):
    text, buttons = get_start(event)
    await event.edit(text, reply_markup=buttons)


def get_start(chat_id):
    strings = get_strings(chat_id, module='pm_menu')

    text = strings["start_hi"]
    buttons = InlineKeyboardMarkup()
    buttons.add(InlineKeyboardButton(strings["btn_help"], callback_data='get_help'))
    buttons.add(InlineKeyboardButton(strings["btn_chat"], url='https://t.me/MayaSupportGroup'))

    return text, buttons


@decorator.CallBackQuery(b'set_lang')
async def set_lang_callback(event):
    text, buttons = lang_info(event.chat_id, pm=True)
    buttons.append([
        Button.inline("Back", 'get_start')
    ])
    try:
        await event.edit(text, buttons=buttons)
    except Exception:
        await event.reply(text, buttons=buttons)


@dp.callback_query_handler(regexp='get_help')
async def get_help_callback(query):
    chat_id = query.message.chat.id
    text, buttons = get_help(chat_id)
    await bot.edit_message_text(text, chat_id, query.message.message_id, reply_markup=buttons)


def get_help(chat_id):
    text = "Select module to get help"
    counter = 0
    buttons = InlineKeyboardMarkup(row_width=2)
    for module in HELP:
        counter += 1
        btn_name = get_string(module, "btn", chat_id, dir="HELPS")
        buttons.insert(InlineKeyboardButton(btn_name, callback_data=help_page_cp.new(module=module)))
    return text, buttons


@dp.callback_query_handler(help_page_cp.filter())
async def get_mod_help_callback(query, callback_data=False, **kwargs):
    chat_id = query.message.chat.id
    message = query.message
    module = callback_data['module']
    text = get_string(module, "title", chat_id, dir="HELPS")
    text += '\n'
    lang = get_chat_lang(chat_id)
    buttons = InlineKeyboardMarkup(row_width=2)
    for string in get_string(module, "text", chat_id, dir="HELPS"):
        text += LANGUAGES[lang]["HELPS"][module]['text'][string]
        text += '\n'
    if 'buttons' in LANGUAGES[lang]["HELPS"][module]:
        counter = 0
        for btn in LANGUAGES[lang]["HELPS"][module]['buttons']:
            counter += 1
            btn_name = LANGUAGES[lang]["HELPS"][module]['buttons'][btn]
            buttons.insert(InlineKeyboardButton(
                btn_name, callback_data=help_btn_cp.new(module=module, btn=btn)))
    buttons.add(InlineKeyboardButton("Back", callback_data='get_help'))
    await message.edit_text(text, reply_markup=buttons)


@dp.callback_query_handler(help_btn_cp.filter())
async def get_help_button_callback(query, callback_data=False, **kwargs):
    message = query.message
    module = callback_data['module']
    data = callback_data['btn']
    chat_id = query.message.chat.id
    lang = get_chat_lang(chat_id)
    text = ""
    if data in LANGUAGES[lang]["HELPS"][module]:
        for btn in get_string(module, data, chat_id, dir="HELPS"):
            text += LANGUAGES[lang]["HELPS"][module][data][btn]
            text += '\n'
    buttons = InlineKeyboardMarkup().add(InlineKeyboardButton("Back", callback_data='get_help'))
    await message.edit_text(text, reply_markup=buttons)


@dp.message_handler(CommandStart('help'))
async def help_start(message):
    text, buttons = get_help(message.chat.id)
    await message.answer(text, reply_markup=buttons)
