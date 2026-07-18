"""
Run this ONCE, locally on your phone (Termux) or PC, to generate a SESSION_STRING.
This logs into YOUR personal Telegram account (the "assistant" that will join the VC).
Never share the printed session string with anyone — it's equivalent to your account login.
"""

from pyrogram import Client

API_ID = int(input("API_ID: "))
API_HASH = input("API_HASH: ")

with Client("vc_assistant", api_id=API_ID, api_hash=API_HASH) as app:
    print("\nYour SESSION_STRING (save this in Render env vars):\n")
    print(app.export_session_string())
