# -*- coding: utf-8 -*-
"""
Белгiлер векторын қалыптастыру модулi (зерттеу жұмысының 3.1-тармағы).

17 арна (5 иiлу + 6 алақан + 6 бiлек) x 5 статистика = 85 белгi.
"""
import numpy as np

N_CH = 17
WIN = 50          # 1 секунд, 50 Гц
ACC_DIV = 8.0     # +-8g      (2.4-тармақ)
GYR_DIV = 1000.0  # +-1000 градус/с


def mean_(x):
    return float(np.mean(x))


def std_(x):
    return float(np.sqrt(np.mean((x - np.mean(x)) ** 2)))


def range_(x):
    return float(np.max(x) - np.min(x))


def slope_(x):
    """Ең кіші квадраттар әдісімен еңкею коэффициенті, ti = i."""
    n = len(x)
    t = np.arange(n, dtype=float)
    tm = t.mean()
    den = np.sum((t - tm) ** 2)
    return float(np.sum((t - tm) * (x - np.mean(x))) / den)


def zcr_(x):
    """
    Орташа сызықты қиып өту жиілігі.

    Қиылысу есептеулердің арасындағы аралықта тіркеледі, сондықтан N есептеу
    үшін бөлгіш N - 1 болады.
    """
    d = x - np.mean(x)
    k = int(np.sum(d[:-1] * d[1:] < 0))
    return k / float(len(x) - 1)


STATS = (mean_, std_, range_, slope_, zcr_)
STAT_NAMES = ('Mean', 'STD', 'Range', 'Slope', 'ZCR')


def normalize(win, flex_min, flex_max):
    """
    Арналарды қалыпқа келтiру.
    win        : (WIN, 17) массив - 5 иiлу, 6 алақан IMU, 6 бiлек IMU
    flex_min/max : сессия калибрлеуiнiң тұрақтылары, 5 элемент
    """
    out = np.empty_like(win, dtype=float)
    rng = np.asarray(flex_max, dtype=float) - np.asarray(flex_min, dtype=float)
    rng[rng == 0] = 1.0
    out[:, 0:5] = (win[:, 0:5] - np.asarray(flex_min)) / rng
    for base in (5, 11):                 # екі инерциялық модуль
        out[:, base:base + 3] = win[:, base:base + 3] / ACC_DIV
        out[:, base + 3:base + 6] = win[:, base + 3:base + 6] / GYR_DIV
    return out


def extract(win):
    """(WIN, 17) терезеден 85 элементті белгілер векторын қайтарады."""
    f = np.empty(N_CH * len(STATS), dtype=float)
    k = 0
    for ch in range(win.shape[1]):
        col = win[:, ch]
        for st in STATS:
            f[k] = st(col)
            k += 1
    return f
