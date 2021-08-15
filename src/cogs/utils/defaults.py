from discord import Member
from difflib import get_close_matches as gcm


def response_ignore_check(member: Member, ignored: list):

    _ids = []

    _ids.append(member.id)
    for role in member.roles:
        _ids.append(role.id)

    return bool(any(i in _ids for i in ignored))


def get_best_match(keywords: list, sentence: str):
    matches = gcm(sentence, keywords, cutoff=0.5)
    return matches[0] if matches else None
