from enum import Enum


class MapStatus(str, Enum):
    LIVE = "live"
    WAITLIST = "waitlist"
    DROPPED = "dropped"
    NEXT = "next"
    

class WaitlistEntriesStatus(str, Enum):
    PENDING = "pending"
    NOTIFIED = "notified"
    JOINED = "joined"
