from __future__ import annotations

from typing import Any, NamedTuple, List
from discord import Member
from difflib import get_close_matches as GCM, SequenceMatcher as SM


class Match(NamedTuple):
    keyword: str
    confidence: float


def response_ignore_check(member: Member, ignored: List[int]) -> bool:
    return any((member._roles.has(i) for i in ignored))



def get_best_match(keywords: List[Any], sentence: str) -> List[Any]:
    matches = GCM(sentence, keywords, cutoff=0.5)
    if not matches:
        return None

    _list = []
    for match in matches:
        sequence_match = SM(None, match, sentence).ratio() * 100
        _list.append(Match(match, sequence_match))

    return sorted(_list, key=lambda x: x.confidence, reverse=True)


async def aenumerate(asequence, start=1):
    """Asynchronously enumerate an async iterator from a given start value"""
    n = start
    async for elem in asequence:
        yield n, elem
        n += 1
