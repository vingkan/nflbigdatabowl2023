PLAY_PRIMARY_KEY = ["gameId", "playId"]
TRACKING_PRIMARY_KEY = ["gameId", "playId", "frameId", "nflId"]
FRAME_PRIMARY_KEY = PLAY_PRIMARY_KEY + ["frameId"]
PFF_PRIMARY_KEY = ["gameId", "playId", "nflId"]

FIELD_LENGTH = 120
FIELD_WIDTH = 53 + (1.0 / 3.0)
