import random
import uuid

PK_CHARS_1 = 'abcdefghjkmnpqrtuvwxy'
PK_CHARS_2 = '2346789'

def pk8():
    r = random.sample(PK_CHARS_1, 5) + random.sample(PK_CHARS_2, 2)
    random.shuffle(r)
    r = random.sample(PK_CHARS_1, 1) + r
    r = ''.join(r)
    return r

def pk16():
    r = random.sample(PK_CHARS_1, 10) + random.sample(PK_CHARS_2, 5)
    random.shuffle(r)
    r = random.sample(PK_CHARS_1, 1) + r
    r = ''.join(r)
    return r

def format_amount(amount, currency):
    if currency == 'EUR':
        currency = u'\u20ac'
    return unicode(amount) + ' ' + unicode(currency)
