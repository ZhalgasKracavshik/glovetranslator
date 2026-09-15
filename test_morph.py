# -*- coding: utf-8 -*-
"""
Морфологиялық автоматты тексеру.
Сөздiктiң жабық болуы токендердiң барлық жарамды тiркесiмiн санап шығуға
мүмкiндiк бередi. Әр тiркесiм үшiн күтiлетiн тұлға қолмен жазылған және
қазақ тiлiнiң септеу-жiктеу кестелерi бойынша тексерiлген.
"""
import io, itertools, time
from morph_fsm import MorphFSM, dative, ablative

R = io.open('test_morph_report.txt', 'w', encoding='utf-8')


def w(s=''):
    R.write(s + '\n')


# ---------------------------------------------------------------- күтілетін тұлғалар
# Қолмен жазылған эталон: «түбір -> септік тұлғасы».
# Тексеру көзі: қазақ тілі грамматикасының септеу кестесі, apertium-kaz ережелері.
EXPECT_CASE = {
    ('дәріхана', 'dat'): 'дәріханаға',  ('дәріхана', 'abl'): 'дәріханадан',
    ('аурухана', 'dat'): 'ауруханаға',  ('аурухана', 'abl'): 'ауруханадан',
    ('ана',      'dat'): 'анаға',       ('ана',      'abl'): 'анадан',
    ('су',       'dat'): 'суға',        ('су',       'abl'): 'судан',
    ('көмек',    'dat'): 'көмекке',     ('көмек',    'abl'): 'көмектен',
    ('жедел жәрдем', 'dat'): 'жедел жәрдемге',
    ('жедел жәрдем', 'abl'): 'жедел жәрдемнен',
    ('мектеп',   'dat'): 'мектепке',    ('мектеп',   'abl'): 'мектептен',
}

w('1-БЛОК. СЕПТIК ЖАЛҒАУЛАРЫН ГЕНЕРАЦИЯЛАУДЫ ТЕКСЕРУ')
w('=' * 62)
w('%-16s %-6s %-18s %-18s %s' % ('Түбiр', 'Септiк', 'Автомат', 'Эталон', 'Нәтиже'))
case_ok = case_bad = 0
for (stem, case), exp in sorted(EXPECT_CASE.items()):
    got = dative(stem) if case == 'dat' else ablative(stem)
    ok = (got == exp)
    case_ok += ok
    case_bad += (not ok)
    w('%-16s %-6s %-18s %-18s %s' % (stem, case, got, exp, 'сәйкес' if ok else 'ҚАТЕ'))
w('')
w('Барлығы: %d тұлға, дұрыс %d, қате %d' % (case_ok + case_bad, case_ok, case_bad))
w('')

# ---------------------------------------------------------------- тізбектер
DAT_NOUNS = [(4, 'дәріхана'), (6, 'аурухана'), (10, 'ана')]
VERBS = [(11, 'бару'), (12, 'келу')]
ALL_NOUNS = [(3, 'көмек'), (4, 'дәріхана'), (5, 'жедел жәрдем'),
             (6, 'аурухана'), (7, 'су'), (10, 'ана')]

VF = {('бару', 1, 'pres'): 'барамын', ('бару', 1, 'past'): 'бардым',
      ('бару', 3, 'pres'): 'барады',  ('бару', 3, 'past'): 'барды',
      ('келу', 1, 'pres'): 'келемін', ('келу', 1, 'past'): 'келдім',
      ('келу', 3, 'pres'): 'келеді',  ('келу', 3, 'past'): 'келді'}

cases = []   # (сипаттама, токендер, күтілетін сөйлем)

# А. Хабарлы сөйлем: зат есім + етістік (+ өткен шақ) (+ шығыс маркері)
for nid, noun in DAT_NOUNS:
    for vid, verb in VERBS:
        for past in (False, True):
            for abl in (False, True):
                toks = [15, nid] + ([14] if abl else []) + [vid] + ([13] if past else [])
                case = 'abl' if (abl or verb == 'келу') else 'dat'
                exp = 'Мен %s %s' % (EXPECT_CASE[(noun, case)],
                                     VF[(verb, 1, 'past' if past else 'pres')])
                cases.append(('хабарлы', toks, exp))

# Б. Сұраулы сөйлем: «қайда» - етістіксіз
for nid, noun in ALL_NOUNS:
    cases.append(('сұраулы', [nid, 16], '%s қайда?' % noun.capitalize()))

# В. Сұраулы сөйлем: «қашан» + етістік
for nid, noun in [(5, 'жедел жәрдем'), (10, 'ана')]:
    for vid, verb in VERBS:
        for past in (False, True):
            toks = [nid, 17, vid] + ([13] if past else [])
            exp = '%s қашан %s?' % (noun.capitalize(),
                                    VF[(verb, 3, 'past' if past else 'pres')])
            cases.append(('сұраулы', toks, exp))

# Г. Дербес реплика
for cid, word in [(1, 'Сәлем'), (2, 'Рахмет'), (8, 'Иә'), (9, 'Жоқ')]:
    cases.append(('реплика', [cid], word))

w('2-БЛОК. ТОКЕНДЕР ТIЗБЕГIНЕН СӨЙЛЕМ ГЕНЕРАЦИЯЛАУ')
w('=' * 62)
w('%-10s %-26s %-34s %s' % ('Түрi', 'Кiрiс токендер', 'Автомат шығысы', 'Нәтиже'))
ok = bad = 0
fails = []
for kind, toks, exp in cases:
    got = MorphFSM.generate(toks)
    good = (got == exp)
    ok += good
    bad += (not good)
    if not good:
        fails.append((toks, got, exp))
    w('%-10s %-26s %-34s %s' % (kind, str(toks), got, 'сәйкес' if good else 'ҚАТЕ'))
w('')
w('Барлығы тiзбек: %d' % len(cases))
w('  хабарлы : %d' % sum(1 for k, _, _ in cases if k == 'хабарлы'))
w('  сұраулы : %d' % sum(1 for k, _, _ in cases if k == 'сұраулы'))
w('  реплика : %d' % sum(1 for k, _, _ in cases if k == 'реплика'))
w('Эталонмен сәйкес келдi: %d' % ok)
w('Сәйкес келмедi       : %d' % bad)
for toks, got, exp in fails:
    w('   %s -> алынды «%s», күтiлдi «%s»' % (toks, got, exp))
w('')
uniq = set(MorphFSM.generate(t) for _, t, _ in cases)
w('Бiрегей сөйлем саны: %d' % len(uniq))
w('')

# ---------------------------------------------------------------- ағынмен жұмыс
w('3-БЛОК. ТЫНЫШТЫҚ БОЙЫНША СӨЙЛЕМДI АЯҚТАУ')
w('=' * 62)
fsm = MorphFSM()
stream = [15] * 6 + [0] * 20 + [4] * 6 + [0] * 20 + [11] * 6 + [0] * 130
produced = []
for c in stream:
    out = fsm.feed(c, dt=0.02)
    if out:
        produced.append(out)
w('Кiрiс ағыны: %d кадр (50 Гц, %.1f с)' % (len(stream), len(stream) * 0.02))
w('Iшкi үзiлiстер: 20 кадр = 0,40 с (шектен төмен, сөйлем үзiлмейдi)')
w('Соңғы үзiлiс : 130 кадр = 2,60 с (шектен жоғары, сөйлем аяқталады)')
w('Шыққан сөйлем саны: %d' % len(produced))
for s in produced:
    w('   «%s»' % s)
w('')

# ---------------------------------------------------------------- жылдамдық
t0 = time.perf_counter()
N = 20000
for _ in range(N):
    MorphFSM.generate([15, 4, 11])
t1 = time.perf_counter()
per = (t1 - t0) / N * 1e6
w('4-БЛОК. ГЕНЕРАЦИЯ УАҚЫТЫ')
w('=' * 62)
w('%d рет қайталау, бiр сөйлемге орташа %.1f мкс' % (N, per))
w('Сұрау циклiнiң 20 мс бюджетiмен салыстырғанда: %.4f %%' % (per / 20000 * 100))

R.close()
print('report written')
