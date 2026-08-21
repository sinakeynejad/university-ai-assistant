# بک‌اند دستیار هوشمند RAG - دانشگاه خواجه نصیرالدین طوسی



## نصب و اجرا

```bash
cd backend
python -m venv venv
source venv/bin/activate   # ویندوز: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# سپس فایل .env را باز کرده و مقادیر LLM را تنظیم کنید (توضیحات در پایین)

uvicorn app.main:app --reload --port 8000
```

پس از اجرا:
- مستندات تعاملی API: http://localhost:8000/docs
- health check: http://localhost:8000/api/health

## مسیرهای API

| Method | مسیر | توضیح |
|---|---|---|
| GET | `/api/health` | بررسی سلامت سرویس |
| POST | `/api/chat` | ارسال سوال و دریافت پاسخ RAG به همراه منابع |
| POST | `/api/documents/upload` | آپلود یک یا چند فایل متنی (txt/md) و ورود به پایگاه دانش |
| GET | `/api/documents` | لیست اسناد موجود در پایگاه دانش |
| DELETE | `/api/documents/{document_name}` | حذف یک سند از پایگاه دانش |

## اتصال یک LLM واقعی

پیش‌فرض `LLM_PROVIDER=mock` است تا بتوانید بدون هیچ کلید API، مسیر
کامل فرانت -> بک -> بازیابی اسناد را تست کنید (پاسخ‌ها نمایشی خواهند بود).

برای اتصال LLM واقعی در `.env`:

```
LLM_PROVIDER=openai_compatible
LLM_API_KEY=<کلید شما>
LLM_BASE_URL=<آدرس endpoint>
LLM_MODEL_NAME=<نام مدل>
```

این پروژه هر endpoint سازگار با OpenAI Chat Completions API را پشتیبانی
می‌کند، از جمله:
- OpenAI مستقیم (`https://api.openai.com/v1`)
- سرویس‌های ایرانی سازگار مثل Aval AI یا Metis AI
- مدل‌های متن‌باز محلی از طریق Ollama یا vLLM با حالت OpenAI-compatible
  (مثلا `http://localhost:11434/v1` برای Ollama)

## نکات اجرای پروداکشن

- `--reload` فقط برای توسعه است؛ در سرور واقعی از
  `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2` یا Gunicorn
  با worker های uvicorn استفاده کنید.
- `CORS_ORIGINS` را از `*` به دامنه‌ی دقیق فرانت تغییر دهید.
- پوشه‌های `data/uploads` و `data/chroma_db` باید persist شوند (روی volume
  یا دیسک دائمی)، در غیر این صورت با هر ری‌استارت کانتینر، پایگاه دانش
  خالی می‌شود.
