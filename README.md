# Husanboy Telegram Bot

Telegram mini app uchun deploy-ready Python servis.

## Nima qiladi
- `/start` bosilganda Husanboy Scan haqida tushuntiradi
- mini app tugmasini chiqaradi
- frontend tayyor PDF'ni shu foydalanuvchining private chatiga yuboradi

## Render env
- `TELEGRAM_BOT_TOKEN` = BotFather bergan token
- `WEBAPP_URL` = Netlify frontendingiz URL'i
- `ALLOWED_ORIGINS` = Netlify domeni, masalan `https://example.netlify.app`

## Ishga tushirish
1. BotFather'da bot yarating.
2. Shu loyihani Render Web Service sifatida deploy qiling.
3. Env'larni kiriting.
4. Deploy bo'lgach Telegram'da botga `/start` yuboring.
5. Bot pastda `📄 Husanboy Scan ochish` tugmasini beradi.
6. Mini app ichida PDF tayyor bo'lgach `Telegramga yuborish` tugmasi ishlaydi.

## Eslatma
Bu servis foydalanuvchi `initData` sini tekshiradi va PDF'ni foydalanuvchining o'z private chatiga yuboradi.
