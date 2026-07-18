# VC Music Bot — Free Hosting Guide (Render)

Ye bot Telegram group ke **Voice Chat** mein music bajata hai — YouTube search/links aur Spotify links (track name resolve karke YouTube se stream) dono support karta hai.

⚠️ **Important:** Telegram bots khud VC join nahi kar sakte — sirf commands handle kar sakte hain. Isliye is setup mein 2 accounts lagte hain:
1. **Bot account** (@BotFather se) → commands sunta hai (`/play`, `/skip`, etc.)
2. **Tumhara personal Telegram account (as "assistant")** → VC mein actually join karke audio stream karta hai

---

## Step 1 — Credentials collect karo

1. **API_ID & API_HASH**: https://my.telegram.org → API Development Tools → new app banao
2. **BOT_TOKEN**: Telegram pe @BotFather ko `/newbot` bhejo
3. **SESSION_STRING**: `generate_session.py` apne phone (Termux) ya PC pe chalao:
   ```
   pip install pyrogram tgcrypto
   python generate_session.py
   ```
   Apna API_ID, API_HASH daalo, phone number se login karo (OTP aayega). End mein ek lambi session string print hogi — ise **kisi ke saath share mat karna**, ye tumhare account jitni sensitive hai.

## Step 2 — GitHub pe code push karo

```
cd vc_music_bot
git init
git add .
git commit -m "VC music bot"
git remote add origin https://github.com/<tumhara-username>/vc-music-bot.git
git push -u origin main
```

## Step 3 — Render pe free deploy

1. https://render.com pe signup/login karo (GitHub se connect karna easy hai)
2. **New +** → **Blueprint** → apna GitHub repo select karo (ye `render.yaml` file khud padh lega)
3. Jab prompt aaye, ye 4 environment variables fill karo:
   - `API_ID`
   - `API_HASH`
   - `SESSION_STRING`
   - `BOT_TOKEN`
4. Deploy karo. Free tier pe worker chalna shuru ho jayega.

⚠️ Render free tier **web services** ko inactivity pe sula deta hai, but ye **background worker** hai (`type: worker`), so wo continuously chalta rehta hai — free plan mein bhi 24/7 uptime milta hai (kuch monthly hour limits ho sakte hain, Render dashboard mein check kar lena).

## Step 4 — Group mein use karo

1. Bot ko apne group mein add karo
2. Apne personal account (jiska SESSION_STRING banaya) ko bhi usi group mein add karo — wahi VC join karega
3. Group VC start karo, phir bot ko commands do:
   - `/play tera hone laga hoon`
   - `/play https://open.spotify.com/track/...`
   - `/skip`, `/stop`, `/queue`

---

### Legal/safety note
Ye bot sirf publicly available YouTube audio stream karta hai (Spotify se sirf track ka naam nikalta hai, audio nahi) — koi paid/DRM content download ya bypass nahi karta.
