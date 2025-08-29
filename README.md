# Декларация о месте жительства — FPDF2 (Unicode, RU/PT)

**Важно:** для поддержки кириллицы добавьте TTF-шрифты в папку `fonts/` (в корне репозитория).  
Рекомендовано: DejaVu Sans (свободная лицензия):
- `fonts/DejaVuSans.ttf`
- `fonts/DejaVuSans-Bold.ttf`
- `fonts/DejaVuSans-Oblique.ttf` (или `DejaVuSans-Italic.ttf` — поправьте код при необходимости)

## Деплой на Streamlit Cloud
1. Залейте файлы в публичный GitHub-репозиторий.
2. Убедитесь, что в репозитории присутствует папка `fonts/` с TTF-файлами (см. выше).
3. В Streamlit Community Cloud выберите этот репозиторий и укажите `streamlit_app.py`.
4. Нажмите Deploy.

## Локальный запуск
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Если шрифты не найдены, приложение покажет предупреждение и попытается использовать Helvetica (кириллица не отобразится).
