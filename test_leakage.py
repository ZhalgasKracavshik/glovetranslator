# -*- coding: utf-8 -*-
"""
Деректердiң ағып кетуi туралы тұжырымды сандық тексеру (3.4-тармақ).

МАҢЫЗДЫ. Мұнда нақты қолғаптан алынған дерек жоқ және бұл сандар жүйенiң
тану дәлдiгi емес. Тексерiлетiн зат - бөлу схемасының өзi. Ол үшiн
статистикалық қасиеттерi алдын ала белгiлi жасанды дерек генераторы
қолданылады: бiр жазбаның терезелерi бiр-бiрiне жақын, ал әр жазбаның
өзiндiк ығысуы бар. Дәл осындай құрылым шынайы датасетте де болады,
өйткен терезелер бiр жесттiң iшiнен кесiледi.

Сұрақ: терезелердi кездейсоқ бөлгенде алынатын дәлдiк жазба бойынша
бөлгендегi дәлдiктен қаншалықты жоғары болады?
"""
import io
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupKFold, StratifiedKFold, cross_val_score

R = io.open('test_leakage_report.txt', 'w', encoding='utf-8')
def w(s=''):
    R.write(s + '\n')

N_CLASS = 18     # А қосымшасындағы сынып саны
N_REC = 20       # бір сыныпқа жазба
N_WIN = 6        # бір жазбадан шығатын терезе (В қосымшасы)
N_FEAT = 85      # белгілер векторының өлшемділігі (3.1-тармақ)
SIG_CLASS = 1.0  # сыныптар арасындағы қашықтық
SIG_WIN = 0.10   # бір жазба ішіндегі терезелердің шашырауы


def make_data(sig_rec, seed):
    """Жасанды датасет: (X, y, groups)."""
    rng = np.random.default_rng(seed)
    proto = rng.normal(0, SIG_CLASS, (N_CLASS, N_FEAT))
    X, y, g = [], [], []
    rid = 0
    for c in range(N_CLASS):
        for _ in range(N_REC):
            off = rng.normal(0, sig_rec, N_FEAT)       # жазбаның өзіндік ығысуы
            for _ in range(N_WIN):
                X.append(proto[c] + off + rng.normal(0, SIG_WIN, N_FEAT))
                y.append(c)
                g.append(rid)
            rid += 1
    return np.array(X), np.array(y), np.array(g)


def clf():
    return RandomForestClassifier(n_estimators=100, criterion='gini',
                                  max_depth=12, min_samples_leaf=2,
                                  random_state=0, n_jobs=-1)


w('ДЕРЕКТЕРДIҢ АҒЫП КЕТУIН БОЛДЫРМАУ СХЕМАСЫН ТЕКСЕРУ')
w('=' * 70)
w('Жасанды дерек. Бұл сандар жүйенiң тану дәлдiгi ЕМЕС.')
w('')
w('Датасет: %d сынып x %d жазба x %d терезе = %d үлгi, %d белгi.'
  % (N_CLASS, N_REC, N_WIN, N_CLASS * N_REC * N_WIN, N_FEAT))
w('Сыныптар арасындағы қашықтық тұрақты (сигма = %.1f),' % SIG_CLASS)
w('жазбаның өзiндiк ығысуы өзгертiлiп отырады.')
w('')
w('%-26s %14s %14s %12s' % ('Жазба ығысуы, сигма', 'Кездейсоқ бөлу',
                            'GroupKFold', 'Айырма'))
w('-' * 70)

rows = []
for sig_rec in (0.25, 0.5, 1.0, 2.0, 4.0):
    X, y, g = make_data(sig_rec, seed=20260914)
    a_leak = cross_val_score(clf(), X, y, cv=StratifiedKFold(5, shuffle=True,
                                                             random_state=0)).mean()
    a_ok = cross_val_score(clf(), X, y, groups=g, cv=GroupKFold(5)).mean()
    rows.append((sig_rec, a_leak, a_ok))
    w('%-26.2f %13.1f %% %13.1f %% %11.1f' % (sig_rec, a_leak * 100,
                                              a_ok * 100, (a_leak - a_ok) * 100))
w('')
w('Кездейсоқ бөлуде бiр жазбаның терезелерi оқыту мен тексеру')
w('iрiктемелерiнiң екеуiне де түседi. Жазбаның ығысуы үлкейген сайын')
w('модель сыныпты емес, жазбаны жаттап алады, ал дәлдiк соған қарамастан')
w('жоғары болып қала бередi.')
w('')
sig, al, ao = rows[3]
w('Сигма = %.1f нүктесiнде айырма %.0f пайыздық тармақ құрады' % (sig, (al - ao) * 100))
w('(%.1f %% және %.1f %%). Демек жазба идентификаторы бойынша бөлмеу' % (al * 100, ao * 100))
w('дәлдiктi бiрнеше есе асыра көрсетуi мүмкiн.')
w('')

# қатысушыны шығару
w('ҚАТЫСУШЫНЫ ШЫҒАРЫП ТАСТАУ СХЕМАСЫ (LOSO)')
w('=' * 70)
w('Бес қатысушы модельденедi. Әр қатысушының өзiндiк тұрақты ығысуы бар:')
w('қолдың мөлшерi мен қолғаптың отырысы әркiмде басқаша.')
w('')
N_SUBJ = 5
w('%-26s %14s %14s %12s' % ('Қатысушы ығысуы, сигма', 'Жазба бойынша',
                            'LOSO', 'Айырма'))
w('-' * 70)
for sig_sub in (0.5, 1.0, 2.0, 3.0):
    rng = np.random.default_rng(7)
    proto = rng.normal(0, SIG_CLASS, (N_CLASS, N_FEAT))
    X, y, subj, grp = [], [], [], []
    rid = 0
    for s in range(N_SUBJ):
        s_off = rng.normal(0, sig_sub, N_FEAT)
        for c in range(N_CLASS):
            for _ in range(4):
                r_off = rng.normal(0, 0.5, N_FEAT)
                for _ in range(N_WIN):
                    X.append(proto[c] + s_off + r_off + rng.normal(0, SIG_WIN, N_FEAT))
                    y.append(c); subj.append(s); grp.append(rid)
                rid += 1
    X = np.array(X); y = np.array(y)
    subj = np.array(subj); grp = np.array(grp)
    a_rec = cross_val_score(clf(), X, y, groups=grp, cv=GroupKFold(5)).mean()
    a_sub = cross_val_score(clf(), X, y, groups=subj, cv=GroupKFold(N_SUBJ)).mean()
    w('%-26.1f %13.1f %% %13.1f %% %11.1f' % (sig_sub, a_rec * 100,
                                              a_sub * 100, (a_rec - a_sub) * 100))
w('')
w('LOSO схемасының саны барлық нүктеде төмен немесе тең. Айырма қатысушылар')
w('бiр-бiрiнен қаншалықты өзгеше болуына тәуелдi: қолдың мөлшерi мен')
w('қолғаптың отырысы әркiмде басқа болғандықтан, бұл айырманы алдын ала')
w('болжау мүмкiн емес және оны өлшеу қажет. 3.4-тармақтағы «екiншi схеманың')
w('сандары әрқашан төмен болады» деген тұжырым расталды, сондықтан есеп')
w('беруде екi сан да келтiрiлуi тиiс.')

R.close()
print('ok')
