from core.components.errors import ScrapperException


class DifferentTimezoneException(ScrapperException): ...


class DifferentSubjectException(ScrapperException): ...


class DifferentDatesException(ScrapperException): ...
