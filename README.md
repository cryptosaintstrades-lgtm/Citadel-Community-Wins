# Citadel Community Wins Bot

This bot watches one Discord channel for member win posts and drafts them into Airtable for approval.

## Railway Variables

Add these variables in Railway:

- `DISCORD_BOT_TOKEN`
- `WINS_CHANNEL_ID`
- `AIRTABLE_TOKEN`
- `AIRTABLE_BASE_ID`
- `AIRTABLE_TABLE_NAME` = `Community Wins`
- `ADD_REACTION` = `true`

## Airtable Fields

The table should be named `Community Wins` and include:

- Member Name — single line text
- Discord Username — single line text
- Message — long text
- Screenshot URL — attachment
- Date — single line text
- Approved — checkbox
- Published — checkbox
- Featured — checkbox

The bot creates records with Approved, Published, and Featured unchecked so you can review before showing anything publicly.
