import hashlib

import discord

import ai
import config
import database as db
import imaging
import search


async def scan_message(message: discord.Message) -> None:
    guild_id = message.guild.id

    for attachment in message.attachments:
        if not (attachment.content_type and "image" in attachment.content_type):
            continue
        if attachment.size > config.MAX_FILE_SIZE:
            continue

        try:
            data = await attachment.read()
            content_hash = hashlib.sha256(data).hexdigest()

            if db.image_exists(guild_id, content_hash):
                continue

            small = await imaging.compress_image(data)
            tags = await ai.generate_tags(small)
            if not tags:
                continue

            added = db.add_image(
                guild_id, attachment.url, tags,
                str(message.author), message.jump_url, content_hash,
            )
            if added:
                try:
                    await search.ensure_vectors(guild_id)
                except Exception as e:
                    print(f"Could not embed tags: {e}")
        except Exception as e:
            print(f"Failed to process attachment {attachment.filename}: {e}")
