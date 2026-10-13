# TITAN PRO V80 — Android

موتور تحلیل **TITAN PRO V80.0** به‌همراه شل اندروید (WebView).

## محتویات APK
- کل بسته `TITAN_PRO_V80_FINAL.zip` را در `app/src/main/assets/` قرار دهید
- هنگام اولین اجرا → استخراج به **Internal Storage/MMM**
- رابط WebView + تلاش خودکار برای `http://127.0.0.1:8080`

## ساخت APK (بالای ۳۰MB)
1. فایل `TITAN_PRO_V80_FINAL.zip` را در `app/src/main/assets/` بگذارید
2. تب **Actions** → **Build TITAN PRO V80 APK** → **Run workflow**
3. Artifact به نام `TITAN-PRO-V80-APK` را دانلود کنید

یا با Android Studio: Build → Build APK(s)

## اجرای موتور روی گوشی
Termux + `python run_titan.py` از مسیر `/storage/emulated/0/MMM/titan_pro`

**فقط تحلیل** — Live پیش‌فرض خاموش.
