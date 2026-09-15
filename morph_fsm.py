# -*- coding: utf-8 -*-
"""
Морфологиялық постпроцессинг автоматы.
Зерттеу жұмысының 4.1-4.3 тармақтарында сипатталған ережелерді жүзеге асырады.

Кіріс  : жіктеуіш берген түбір-токендер тізбегі.
Шығыс  : қазақ тілінің грамматикасы бойынша құрастырылған сөйлем.
"""

# ---------------------------------------------------------------- дыбыс жиындары
JUAN = set('аоұы')          # жуан дауыстылар
JINISHKE = set('еөүі')      # жіңішке дауыстылар
QATAN = set('кқпстфхцчшщ')  # қатаң дауыссыздар
MURYN = set('мнң')          # мұрын жолды дауыссыздар
B_V_G_D = set('бвгд')       # ұяң, бірақ шығыс септікте қатаң нұсқаны талап етеді
VOWELS = JUAN | JINISHKE | set('әэеиуюяыі')


# ---------------------------------------------------------------- сингармонизм
def last_vowel(word):
    """Сөздегі соңғы дауысты дыбыс."""
    for ch in reversed(word.lower()):
        if ch in VOWELS:
            return ch
    return None


def is_hard(word):
    """Сөз жуан буынды ма? ә, ө, ү, і, е болса - жіңішке."""
    v = last_vowel(word)
    if v is None:
        return True
    if v in JINISHKE or v in set('әэеи'):
        return False
    return True


def dative(word):
    """Барыс септік: -ға/-ге (дауысты, ұяң, үнді соңынан), -қа/-ке (қатаң соңынан)."""
    stem = word.lower()
    last = stem[-1]
    hard = is_hard(stem)
    if last in QATAN:
        suf = 'қа' if hard else 'ке'
    else:
        suf = 'ға' if hard else 'ге'
    return stem + suf


def ablative(word):
    """Шығыс септік: -дан/-ден, -тан/-тен, -нан/-нен."""
    stem = word.lower()
    last = stem[-1]
    hard = is_hard(stem)
    if last in MURYN:
        suf = 'нан' if hard else 'нен'
    elif last in QATAN or last in B_V_G_D:
        suf = 'тан' if hard else 'тен'
    else:
        suf = 'дан' if hard else 'ден'
    return stem + suf


# ---------------------------------------------------------------- сөздік
# А қосымшасындағы сыныптар. Кілт - сынып нөмірі.
LEXICON = {
    0:  ('ТЫНЫШТЫҚ',      'silence'),
    1:  ('Сәлем',         'reply'),
    2:  ('Рахмет',        'reply'),
    3:  ('көмек',         'noun'),
    4:  ('дәріхана',      'noun'),
    5:  ('жедел жәрдем',  'noun'),
    6:  ('аурухана',      'noun'),
    7:  ('су',            'noun'),
    8:  ('Иә',            'reply'),
    9:  ('Жоқ',           'reply'),
    10: ('ана',           'noun'),
    11: ('бару',          'verb'),
    12: ('келу',          'verb'),
    13: ('ӨТКЕН',         'marker'),
    14: ('ШЫҒЫС',         'marker'),
    15: ('мен',           'pron'),
    16: ('қайда',         'wh'),
    17: ('қашан',         'wh'),
}

# Б қосымшасы: етістікті жіктеу кестесі
VERB_FORMS = {
    'бару': {(1, 'pres'): 'барамын', (1, 'past'): 'бардым',
             (3, 'pres'): 'барады',  (3, 'past'): 'барды'},
    'келу': {(1, 'pres'): 'келемін', (1, 'past'): 'келдім',
             (3, 'pres'): 'келеді',  (3, 'past'): 'келді'},
}

# Етістіктің меңгеруі: тиісті септік маркерсіз де қойылады
VERB_CASE = {'бару': 'dat', 'келу': 'abl'}


# ---------------------------------------------------------------- автомат
class MorphFSM(object):
    """Токендер буферін жинап, тыныштық белгісі бойынша сөйлем шығарады."""

    SILENCE_LIMIT = 2.5           # секунд, 4.1-тармақ

    def __init__(self):
        self.buf = []
        self.silence = 0.0

    def feed(self, cls, dt=0.02):
        """Жіктеуіштен келген бір сыныпты қабылдау. Сөйлем дайын болса қайтарады."""
        if cls == 0:
            self.silence += dt
            if self.silence >= self.SILENCE_LIMIT and self.buf:
                return self.flush()
            return None
        self.silence = 0.0
        if not self.buf or self.buf[-1] != cls:
            self.buf.append(cls)
        return None

    def flush(self):
        out = self.generate(self.buf)
        self.buf = []
        self.silence = 0.0
        return out

    # ------------------------------------------------------------ генерация
    @staticmethod
    def generate(tokens):
        """Токендер тізбегінен сөйлем құрастыру."""
        words = [LEXICON[t] for t in tokens if t in LEXICON]
        kinds = [k for _, k in words]

        # 1. Дербес реплика: жалғыз тұрған қайырым сөзі
        if all(k in ('reply', 'silence') for k in kinds):
            reps = [w for w, k in words if k == 'reply']
            return ' '.join(reps) if reps else ''

        nouns   = [w for w, k in words if k == 'noun']
        verbs   = [w for w, k in words if k == 'verb']
        whs     = [w for w, k in words if k == 'wh']
        markers = [w for w, k in words if k == 'marker']

        past    = 'ӨТКЕН' in markers
        abl_mk  = 'ШЫҒЫС' in markers

        # 2. Сұраулы токен бар ма? 4.3-тармақ: ереже басқалардан бұрын орындалады
        if whs:
            person = 3
            subject = None
        else:
            person = 1
            subject = 'Мен'

        tense = 'past' if past else 'pres'

        # 3. Зат есімнің септігі
        noun_out = None
        if nouns:
            n = nouns[0]
            if whs:
                # Сұраулы сөйлемде бастауыш жоқ, зат есім соның орнын алады:
                # «Дәріхана қайда?», «Жедел жәрдем қашан келеді?» - атау септік.
                case = 'nom'
            elif verbs:
                case = 'abl' if abl_mk else VERB_CASE[verbs[0]]
            else:
                case = 'abl' if abl_mk else 'nom'
            if case == 'dat':
                noun_out = dative(n)
            elif case == 'abl':
                noun_out = ablative(n)
            else:
                noun_out = n

        # 4. Етістікті жіктеу
        verb_out = None
        if verbs:
            verb_out = VERB_FORMS[verbs[0]][(person, tense)]

        # 5. Сөз тәртібі: бастауыш - толықтауыш - сұраулы сөз - баяндауыш
        parts = []
        if subject:
            parts.append(subject)
        if noun_out:
            parts.append(noun_out)
        if whs:
            parts.append(whs[0])
        if verb_out:
            parts.append(verb_out)

        if not parts:
            return ''
        s = ' '.join(parts)
        s = s[0].upper() + s[1:]
        return s + ('?' if whs else '')
