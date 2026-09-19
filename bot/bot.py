#!/usr/bin/env python3
"""
Бот для русской Википедии 
"""

import re
import pywikibot
from transformers import (
    protect_tags, restore_tags,
    wikify, dewikify_dates, fix_quotes,
    normalize_numbers, yoficate, mark_no_ai
)

def process_page(page):
    text = page.text
    original = text

    # 1. Защита блоков, которые нельзя трогать
    text, store = protect_tags(text)

    # 2. Цепочка правок (порядок важен!)
    text = wikify(text)              # Викификация разметки
    text = dewikify_dates(text)      # Даты без лишних ссылок
    text = fix_quotes(text)          # Кавычки и тире
    text = normalize_numbers(text)  # Числа и единицы измерения
    text = yoficate(text)            # Ёфикация
    text = mark_no_ai(text)          # Пометка без АИ

    # 3. Возврат защищённых блоков
    text = restore_tags(text, store)

    if text != original:
        page.text = text
        page.save(
            'Автоматические правки: викификация, типографика, ёфикация',
            bot=True
        )
        pywikibot.info(f'✓ Обновлено: {page.title()}')
    else:
        pywikibot.info(f'— Без изменений: {page.title()}')

if __name__ == '__main__':
    site = pywikibot.Site('ru', 'wikipedia')
    
    test_page_title = 'Участник:Spähpanzer/Тест бота'
    
    page = pywikibot.Page(site, test_page_title)
    try:
        process_page(page)
    except Exception as e:
        pywikibot.error(f'Ошибка: {e}')
