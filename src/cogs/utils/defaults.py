from typing import NamedTuple
from discord import Member
from difflib import get_close_matches as GCM, SequenceMatcher as SM


class Match(NamedTuple):
    keyword: str
    confidence: float


def response_ignore_check(member: Member, ignored: list):

    _ids = []

    _ids.append(member.id)
    for role in member.roles:
        _ids.append(role.id)

    return bool(any(i in _ids for i in ignored))


def get_best_match(keywords: list, sentence: str):
    matches = GCM(sentence, keywords, cutoff=0.5)
    if not matches:
        return None

    _list = []
    for match in matches:
        sequence_match = SM(None, match, sentence).ratio() * 100
        _list.append(Match(match, sequence_match))

    return sorted(_list, key=lambda x: x.confidence, reverse=True)
