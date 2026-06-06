import enum


class SearchSort(str, enum.Enum):
    RELEVANCE = "relevance"
    HOT = "hot"
    TIME = "time"

