import json
import os


class Config(object):
    __slots__ = [
        "__token",
        "__application_id",

        "owner_ids",
        "nexus_guild_id",
        "data_loc",
        "command_prefix",

        "cogs",
    ]

    def __init__(self):
        self.load()

    def serialise(self) -> dict:
        return {
            "token":            self.__token,
            "owner_ids":        self.owner_ids,
            "nexus_guild_id":   self.nexus_guild_id,
            "data_loc":         self.data_loc,
            "command_prefix":   self.command_prefix,
        }

    def load(self) -> None:
        with open("./config.json", "r") as file:
            data = json.loads(file.read())
        self.__token = data["token"]
        self.owner_ids = set(data["owner_ids"])
        self.nexus_guild_id = data["nexus_guild_id"]
        self.data_loc = data["data_loc"]
        self.command_prefix = data["command_prefix"]

        self.cogs = [f"cogs.{cog}" for cog in [
            "match_cog",
            "queue_cog",
            "stats_cog",
        ]]

        if not os.path.exists(self.data_loc):
            os.mkdir(self.data_loc)

    def save(self) -> None:
        with open("./config.json", "w") as file:
            file.write(json.dumps(self.serialise()))

    @property
    def token(self) -> str:
        return self.__token
