from .fields import *
from .functions import *
from tortoise import models, fields


class Response(models.Model):
    class Meta:
        table = "response_info"

    guild_id = fields.BigIntField(pk=True, index=True)
    valid_channel_ids = ArrayField(fields.BigIntField())
    ignored_ids = ArrayField(fields.BigIntField(), default=list)
    allow_all = fields.BooleanField(default=True)
    data: fields.ManyToManyRelation["ResponseData"] = fields.ManyToManyField("models.ResponseData", index=True)


class ResponseData(models.Model):
    class Meta:
        table = "response_data"

    id = fields.BigIntField(pk=True)
    keywords = ArrayField(fields.CharField(max_length=100))
    content = fields.TextField()
    uses = fields.IntField(default=0)
    author_id = fields.BigIntField()
    created_at = fields.DatetimeField(auto_now=True)


class Voice(models.Model):
    class Meta:
        table = "voice"

    guild_id = fields.BigIntField(pk=True)
    voice_channel_id = fields.BigIntField()
