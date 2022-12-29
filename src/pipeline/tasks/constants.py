PLAY_PRIMARY_KEY = ["gameId", "playId"]
TRACKING_PRIMARY_KEY = ["gameId", "playId", "frameId", "nflId"]
FRAME_PRIMARY_KEY = PLAY_PRIMARY_KEY + ["frameId"]
PFF_PRIMARY_KEY = ["gameId", "playId", "nflId"]
