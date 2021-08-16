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

    @property
    def valid_channels(self):
        channels = map(self.bot.get_channel, self.valid_channel_ids)
        return (getattr(channel, "mention", "deleted-channel") for channel in channels)


class ResponseData(models.Model):
    class Meta:
        table = "response_data"

    id = fields.BigIntField(pk=True)
    keywords = ArrayField(fields.CharField(max_length=100))
    content = fields.TextField()
    uses = fields.IntField(default=0)
    upvote = fields.IntField(default=0)
    downvote = fields.IntField(default=0)
    author_id = fields.BigIntField()
    created_at = fields.DatetimeField(auto_now=True)
