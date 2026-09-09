from enum import Enum


class MapStatus(str, Enum):
    LIVE = "live"
    WAITLIST = "waitlist"
    DROPPED = "dropped"
    

class WaitlistEntriesStatus(str, Enum):
    PENDING = "pending"
    NOTIFIED = "notified"
    JOINED = "joined"
