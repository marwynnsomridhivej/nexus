__all__ = (
    "PlayerAlreadyExists",
    "PlayerDoesNotExist",
)


class PlayerAlreadyExists(Exception):
    def __init__(self, user_id: int):
        self.user_id = user_id

    def __str__(self) -> str:
        return f"PlayerAlreadyExist[user_id={self.user_id}]"


class PlayerDoesNotExist(Exception):
    def __init__(self, user_id: int):
        self.user_id = user_id

    def __str__(self) -> str:
        return f"PlayerDoesNotExist[user_id={self.user_id}]"
