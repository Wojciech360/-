"""
transformers.py — все функции трансформации для бота Википедии.
"""
import re

PROTECTED_TAGS = [
    'nowiki', 'pre', 'code', 'math', 'source',
    'syntaxhighlight', 'ref', 'gallery', 'timeline'
]

def protect_tags(text: str):
    store = {}
    for tag in PROTECTED_TAGS:
        pattern = rf'<{tag}(\s[^>]*)?>.*?</{tag}>'
        for m in re.finditer(pattern, text, re.DOTALL | re.IGNORECASE):
            key = f'\x00PROT{len(store)}\x00'
            store[key] = m.group()
            text = text[:m.start()] + key + text[m.end():]
    for m in re.finditer(r'^ .*$', text, re.MULTILINE):
        key = f'\x00PROT{len(store)}\x00'
        store[key] = m.group()
        text = text[:m.start()] + key + text[m.end():]
    return text, store

def restore_tags(text: str, store: dict) -> str:
    for key, val in store.items():
        text = text.replace(key, val)
    return text

def wikify(text: str) -> str:
    text = re.sub(r'<b>(.*?)</b>', r"'''\1'''", text, flags=re.IGNORECASE)
    text = re.sub(r'<strong>(.*?)</strong>', r"'''\1'''", text, flags=re.IGNORECASE)
    text = re.sub(r'<i>(.*?)</i>', r"''\1''", text, flags=re.IGNORECASE)
    text = re.sub(r'<em>(.*?)</em>', r"''\1''", text, flags=re.IGNORECASE)
    text = re.sub(r'<hr\s*/?>', '----', text, flags=re.IGNORECASE)
    text = re.sub(r'\[\[(Category|category):', '[[Категория:', text)
    text = re.sub(r'\[\[(Image|image|File|file):', '[[Файл:', text)
    text = re.sub(r'\[\[\s+', '[[', text)
    text = re.sub(r'\s+\]\]', ']]', text)
    text = re.sub(r'\[\[\s*([^|]+?)\s*\|\s*', r'[[\1|', text)
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    text = re.sub(r'[ \t]+\n', '\n', text)
    return text

def dewikify_dates(text: str) -> str:
    M = 'января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря'
    text = re.sub(rf'\[\[(\d{{1,2}}\s+(?:{M}))\]\]', r'\1', text)
    text = re.sub(r'\[\[(\d{4})\s*год\]\]а', r'\1 года', text)
    text = re.sub(r'\[\[(\d{4})\s*год\|(\d{4})\]\]', r'\2', text)
    text = re.sub(rf'\[\[\[\[(\d{{1,2}}\s+(?:{M}))\]\]\]\]', r'\1', text)
    return text

def fix_quotes(text: str) -> str:
    text = re.sub(r'"([^"]*?)"', r'«\1»', text)
    text = re.sub(r'\s+[-—]\s+', ' — ', text)
    text = re.sub(r'\.\.\.', '…', text)
    text = re.sub(r'\.\s\.\s\.', '…', text)
    return text

def normalize_numbers(text: str) -> str:
    text = re.sub(r'(\d)\.(\d)', r'\1,\2', text)
    text = re.sub(r'(\d)\s+%', r'\1\u00a0%', text)
    text = re.sub(r'(\d)\s+(тыс\.|млн|млрд|трлн)', r'\1\u00a0\2', text)
    text = re.sub(r'(\d)\s*°?\s*[Cc]\b', r'\1 °C', text)
    for u in ['м', 'км', 'см', 'мм']:
        text = re.sub(rf'(\d)\s*{u}\^?2\b', rf'\1 {u}²', text)
    return text

def yoficate(text: str) -> str:
    d = {
        'еще': 'ещё', 'все': 'всё', 'берет': 'берёт',
        'желтый': 'жёлтый', 'счет': 'счёт', 'счета': 'счёта',
        'идет': 'идёт', 'придет': 'придёт', 'уйдет': 'уйдёт',
        'найдет': 'найдёт', 'пройдет': 'пройдёт',
        'передает': 'передаёт', 'признается': 'признаётся',
        'щелкать': 'щёлкать', 'щелчок': 'щёлчок',
        'совершенный': 'совершённый', 'решенный': 'решённый',
        'напряженный': 'напряжённый', 'введенный': 'введённый',
        'внесенный': 'внесённый', 'новорожденный': 'новорождённый',
        'рожденный': 'рождённый', 'включенный': 'включённый',
        'заключенный': 'заключённый', 'поврежденный': 'повреждённый',
        'осужденный': 'осуждённый', 'обнаженный': 'обнажённый',
        'вооруженный': 'вооружённый',
    }
    for w, r in d.items():
        text = re.sub(rf'(?<![а-яё])({w})(?![а-яё])', r, text, flags=re.IGNORECASE)
    return text

TRIVIAL = [
    r'родился\s+\d', r'родилась\s+\d', r'умер\s+\d', r'умерла\s+\d',
    r'численность\s+населения', r'площадь\s+—\s*\d',
    r'население\s+—\s*\d', r'основан\s+в\s+\d{4}',
    r'основана\s+в\s+\d{4}', r'расположен\s+в\s',
    r'расположена\s+в\s', r'столица\s+—', r'высота\s+—\s*\d',
]

def _is_trivial(s: str) -> bool:
    for p in TRIVIAL:
        if re.search(p, s, re.IGNORECASE):
            return True
    return len(s.split()) < 5

def mark_no_ai(text: str) -> str:
    markers = [
        'считается', 'полагают', 'утверждается', 'по мнению',
        'по словам', 'якобы', 'по некоторым данным',
        'предположительно', 'вероятно', 'возможно'
    ]
    for marker in markers:
        pat = rf'([.!?]\s+|^)(([^.!?]*\b{marker}\b[^.!?]*[.!?]))'
        for m in re.finditer(pat, text, re.IGNORECASE):
            sentence = m.group(2)
            end_pos = m.end()
            chunk = text[end_pos:end_pos + 150]
            if re.search(r'<ref|{{источник|{{ссылка|{{cite', chunk, re.IGNORECASE):
                continue
            before = text[max(0, m.start() - 30):m.start()]
            if 'нет АИ' in before.lower() or 'нет источников' in before.lower():
                continue
            if _is_trivial(sentence):
                continue
            replacement = re.sub(
                rf'(\b{marker}\b)', r'\1{{подст:Нет АИ|',
                sentence, count=1, flags=re.IGNORECASE
            )
            if replacement.endswith('.'):
                replacement = replacement[:-1] + '}}.'
            elif replacement.endswith('!'):
                replacement = replacement[:-1] + '}}!'
            elif replacement.endswith('?'):
                replacement = replacement[:-1] + '}}?'
            else:
                replacement += '}}'
            text = text[:m.start()] + m.group(1) + replacement + text[m.end():]
    return text
def remove_trivial(text: str) -> str:
    for pattern in TRIVIAL:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    return text

def mark_uncertainty(text: str) -> str:
    markers = [
        'считается', 'полагают', 'утверждается', 'по мнению',
        'по словам', 'якобы', 'по некоторым данным',
        'предположительно', 'вероятно', 'возможно'
    ]
    for marker in markers:
        text = re.sub(
            rf'([.!?]\s+|^)(([^.!?]*\b{marker}\b[^.!?]*[.!?]))', 
            r'\1{{подст:Нет АИ|\2}}', text, count=1, flags=re.IGNORECASE
        )
    return text

# Пример использования всех функций
text = "Считается, что население — 1000 человек. Площадь — 100 км². Основан в 2000 году."
text = remove_trivial(text)
text = yoficate(text)
text = mark_uncertainty(text)
print(text)
