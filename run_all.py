# -*- coding: utf-8 -*-
"""
Барлық тексеру сценарийлерін іске қосып, қорытынды кестені шығарады.
Зерттеу жұмысының 5.2-5.4-тармақтарындағы сандар осы шығыстан алынған.

Іске қосу:  python run_all.py
"""
import sys, time, subprocess, os

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
LINE = '=' * 64


def head(t):
    print('\n' + LINE)
    print(t)
    print(LINE)


def run(script):
    t0 = time.perf_counter()
    r = subprocess.run([sys.executable, script], cwd=HERE,
                       capture_output=True, text=True)
    dt = time.perf_counter() - t0
    ok = (r.returncode == 0)
    print('  %-22s %s   (%.1f с)' % (script, 'ОРЫНДАЛДЫ' if ok else 'ҚАТЕ', dt))
    if not ok:
        print(r.stderr[-800:])
    return ok


def tail(path, marker, n):
    """Есеп файлынан marker жолынан кейінгі n жолды оқу."""
    with open(os.path.join(HERE, path), encoding='utf-8') as f:
        rows = f.read().split('\n')
    for i, s in enumerate(rows):
        if marker in s:
            return rows[i:i + n]
    return []


print(LINE)
print('СЕНСОРЛЫҚ ҚОЛҒАП: БАҒДАРЛАМАЛЫҚ БӨЛІКТІ ТЕКСЕРУ')
print('Жалғас Данил, 10 «В» сынып, BINOM SCHOOL')
print(LINE)
print('Python', sys.version.split()[0])

head('1. СЦЕНАРИЙЛЕРДІ ІСКЕ ҚОСУ')
ok = all([run('test_morph.py'), run('test_features.py'), run('test_leakage.py')])

head('2. МОРФОЛОГИЯЛЫҚ АВТОМАТ  (5.2-тармақ)')
for s in tail('test_morph_report.txt', 'Барлығы: 14', 1):
    print('  ' + s)
for s in tail('test_morph_report.txt', 'Барлығы т', 7):
    if s.strip():
        print('  ' + s)
for s in tail('test_morph_report.txt', 'регей сөйлем', 1):
    print('  ' + s)

head('3. БЕЛГІЛЕРДІ ЕСЕПТЕУ МОДУЛІ  (5.3-тармақ)')
for s in tail('test_features_report.txt', 'Тексерiлген мән саны', 3):
    print('  ' + s)
for s in tail('test_features_report.txt', 'Белгiлер векторының өлшемдiлiгi', 1):
    print('  ' + s)
for s in tail('test_features_report.txt', 'орташа есептеу уақыты', 1):
    print('  ' + s)

head('4. БӨЛУ СХЕМАСЫ  (5.4-тармақ)')
for s in tail('test_leakage_report.txt', 'Жазба ығысуы', 8):
    print('  ' + s)

print('\n' + LINE)
print('ҚОРЫТЫНДЫ: барлық тексеру %s' % ('сәтті аяқталды' if ok else 'ҚАТЕМЕН аяқталды'))
print('Толық есептер: test_morph_report.txt, test_features_report.txt,')
print('               test_leakage_report.txt')
print(LINE)
