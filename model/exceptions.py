class GameStarted(BaseException):
    pass


class PreconditionsNotMet(BaseException):
    pass


class GameFull(BaseException):
    pass


class PlayerNotInGame(BaseException):
    pass
