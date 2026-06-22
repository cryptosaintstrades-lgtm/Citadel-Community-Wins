import os
import sys
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import discord
import requests

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "").strip()
WINS_CHANNEL_ID = os.getenv("WINS_CHANNEL_ID", "").strip()
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN", "").strip()
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "").strip()
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "Community Wins").strip()

# Optional: if true, bot reacts with trophy after drafting the win.
ADD_REACTION = os.getenv("ADD_REACTION", "true").lower() == "true"

REQUIRED_ENV = {
    "DISCORD_BOT_TOKEN": DISCORD_BOT_TOKEN,
    "WINS_CHANNEL_ID": WINS_CHANNEL_ID,
    "AIRTABLE_TOKEN": AIRTABLE_TOKEN,
    "AIRTABLE_BASE_ID": AIRTABLE_BASE_ID,
}

missing = [key for key, value in REQUIRED_ENV.items() if not value]
if missing:
    print(f"Missing required environment variables: {', '.join(missing)}", flush=True)
    sys.exit(1)

try:
    WINS_CHANNEL_ID_INT = int(WINS_CHANNEL_ID)
except ValueError:
    print("WINS_CHANNEL_ID must be the numeric Discord channel ID.", flush=True)
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)


def airtable_url() -> str:
    from urllib.parse import quote
    table = quote(AIRTABLE_TABLE_NAME, safe="")
    return f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{table}"


def build_attachment_records(message: discord.Message) -> List[Dict[str, str]]:
    attachments = []
    for att in message.attachments:
        if att.content_type and not att.content_type.startswith("image/"):
            continue
        attachments.append({"url": att.url, "filename": att.filename})
    return attachments


def message_jump_url(message: discord.Message) -> str:
    return f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"


def create_airtable_record(message: discord.Message) -> Optional[Dict[str, Any]]:
    attachments = build_attachment_records(message)
    content = message.content.strip()

    if not content and not attachments:
        print("Skipped message with no text and no image attachment.", flush=True)
        return None

    display_name = getattr(message.author, "display_name", None) or message.author.name
    username = str(message.author)
    created = message.created_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    fields: Dict[str, Any] = {
        "Member Name": display_name,
        "Discord Username": username,
        "Message": content or "[Image only win post]",
        "Date": created,
        "Approved": False,
        "Published": False,
        "Featured": False,
    }

    # Optional fields: if they exist in Airtable, these will populate.
    # If the fields do not exist, Airtable will reject the record, so keep only your confirmed fields above
    # unless you add these fields to Airtable later.
    # fields["Discord Message Link"] = message_jump_url(message)

    if attachments:
        fields["Screenshot URL"] = attachments

    payload = {"fields": fields}
    headers = {
        "Authorization": f"Bearer {AIRTABLE_TOKEN}",
        "Content-Type": "application/json",
    }

    response = requests.post(airtable_url(), json=payload, headers=headers, timeout=20)

    if not response.ok:
        print("Airtable push failed:", response.status_code, response.text, flush=True)
        return None

    data = response.json()
    print(f"Drafted Community Win in Airtable: {data.get('id')}", flush=True)
    return data


@client.event
async def on_ready():
    print(f"Citadel Wins Bot online as {client.user}", flush=True)
    print(f"Watching channel ID: {WINS_CHANNEL_ID}", flush=True)
    print(f"Airtable table: {AIRTABLE_TABLE_NAME}", flush=True)


@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.channel.id != WINS_CHANNEL_ID_INT:
        return

    print(f"New win post from {message.author}: {message.content[:80]}", flush=True)
    record = create_airtable_record(message)

    if record and ADD_REACTION:
        try:
            await message.add_reaction("🏆")
        except Exception as exc:
            print(f"Could not add reaction: {exc}", flush=True)


if __name__ == "__main__":
    client.run(DISCORD_BOT_TOKEN)
