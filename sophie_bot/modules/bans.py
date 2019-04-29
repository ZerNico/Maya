import time

from sophie_bot.events import register
from sophie_bot.modules.users import get_user_and_text, is_user_admin, user_link
from sophie_bot import MONGO

from telethon.tl.functions.channels import EditBannedRequest

from telethon.tl.types import ChatBannedRights


@register(incoming=True, pattern="^/ban (.*)")
async def event(event):
    user, reason = await get_user_and_text(event)
    if await ban_user(event, user['user_id'], event.chat_id, None) is True:
        admin_str = user_link(event.from_id)
        user_str = user_link(user['user_id'])
        await event.reply("User {} banned by {}!\nReason: `{}`".format(
            user_str, admin_str, reason), link_preview=False)


@register(incoming=True, pattern="^/tban (.*)")
async def event(event):
    K = await is_user_admin(event.chat_id, event.from_id)
    if K is False:
        await event.reply("You don't have rights to ban users here!")
        return
    user, data = await get_user_and_text(event)
    data = data.split(' ', 2)
    reason = data[1]
    time_val = data[0]

    unit = time_val[-1]
    if any(time_val.endswith(unit) for unit in ('m', 'h', 'd')):
        time_num = time_val[:-1]  # type: str
        if unit == 'm':
            bantime = int(time.time() + int(time_num) * 60)
            unit_str = 'minutes'
        elif unit == 'h':
            bantime = int(time.time() + int(time_num) * 60 * 60)
            unit_str = 'hours'
        elif unit == 'd':
            bantime = int(time.time() + int(time_num) * 24 * 60 * 60)
            unit_str = 'days'
        else:
            await event.reply("Time value isn't a correct!")

    if await ban_user(event, user.id, event.chat_id, bantime) is True:
        admin_str = user_link(event.from_id)
        user_str = user_link(user['user_id'])
        text = "User {} banned by {}!\n".format(user_str, admin_str)
        text += "For `{}` {}\n".format(time_val[:-1], unit_str)
        text += "Reason: `{}`".format(reason)
        await event.reply(text, link_preview=False)


async def ban_user(event, user_id, chat_id, time_val):

    K = await is_user_admin(event.chat_id, event.from_id)
    if K is False:
        await event.reply("You don't have rights to ban users here!")
        return

    banned_rights = ChatBannedRights(
        until_date=time_val,
        view_messages=True,
        send_messages=True,
        send_media=True,
        send_stickers=True,
        send_gifs=True,
        send_games=True,
        send_inline=True,
        embed_links=True,
    )

    if user_id == 885745757:
        await event.reply("Are you crazy?! Ban myself!")
        return False
    if await is_user_admin(chat_id, user_id) is True:
        await event.reply("This is admin, i can't ban him.")
        return False

    try:
        await event.client(
            EditBannedRequest(
                chat_id,
                user_id,
                banned_rights
            )
        )

    except Exception as err:
        await event.edit(str(err))
        return False

    return True