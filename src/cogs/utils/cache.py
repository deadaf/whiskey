from aiocache import cached
from models import Response
from aiocache.serializers import PickleSerializer

import itertools


@cached(ttl=60, serializer=PickleSerializer())
async def get_guild_keywords(guild_id: int):
    records = await Response.get(guild_id=guild_id)
    _list = []
    async for record in records.data.all():
        _list.append(record.keywords)

    return list(itertools.chain(*_list))
