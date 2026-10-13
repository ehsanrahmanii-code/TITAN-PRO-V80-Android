# TITAN PRO V80 — Android + Engine

ریپوی آمادهِ ساخت **APK** و موتور TITAN PRO V80.

## ساخت APK (بدون نیاز به آپلود دستی)

1. بروید: https://github.com/ehsanrahmanii-code/TITAN-PRO-V80-Android/actions
2. ورکفلو **Build TITAN PRO V80 APK** → **Run workflow**
3. Artifact به نام `TITAN-PRO-V80-APK` را دانلود کنید

اگر تب Actions را نمی‌بینید:
**Settings → Actions → General → Allow all actions and reusable workflows**

## محتویات ریپو
| مسیر | شرح |
|------|------|
| `app/` | شل Android (WebView + استخراج MMM) |
| `titan_pro/` | موتور Python V80 |
| `.github/workflows/` | ساخت خودکار APK |

## اجرا روی گوشی
پس از نصب APK، با Termux:
```bash
cd /storage/emulated/0/MMM/titan_pro
pip install -r requirements.txt
python run_titan.py
```

**فقط تحلیل** — Live پیش‌فرض خاموش.
