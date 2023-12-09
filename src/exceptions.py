class ParserFindTagException(Exception):
    """Вызывается, когда парсер не может найти тег."""
    pass


class StatusNotMatch(Exception):
    """Вызывается, когда в функции pep не совпадают статусы с искомыми."""
    pass
