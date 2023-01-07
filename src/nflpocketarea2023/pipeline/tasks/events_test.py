import pandas as pd

from nflpocketarea2023.pipeline.tasks.events import clean_event_data


def test_clean_event_data():
    df_tracking = pd.DataFrame(
        [
            # Set this `None` event to null.
            {
                "gameId": 1,
                "playId": 1,
                "frameId": 2,
                "nflId": 10,
                "event": "None",
            },
            # Rename this autoevent for `ball_snap`.
            {
                "gameId": 1,
                "playId": 1,
                "frameId": 5,
                "nflId": 10,
                "event": "autoevent_ballsnap",
            },
            # Set this redundant snap to null because it was not the first.
            {
                "gameId": 1,
                "playId": 1,
                "frameId": 8,
                "nflId": 10,
                "event": "ball_snap",
            },
            # Keep both these `fumble` events because the event is repeatable.`
            {
                "gameId": 1,
                "playId": 1,
                "frameId": 7,
                "nflId": 10,
                "event": "fumble",
            },
            {
                "gameId": 1,
                "playId": 1,
                "frameId": 9,
                "nflId": 10,
                "event": "fumble",
            },
            # Keep this `pass_forward` because it was the first.
            {
                "gameId": 1,
                "playId": 1,
                "frameId": 12,
                "nflId": 10,
                "event": "pass_forward",
            },
            # Remove duplicate rows for different players in the same frame.
            {
                "gameId": 1,
                "playId": 1,
                "frameId": 12,
                "nflId": 20,
                "event": "pass_forward",
            },
            # Set this redundant pass to null because it was not the first.
            {
                "gameId": 1,
                "playId": 1,
                "frameId": 14,
                "nflId": 10,
                "event": "autoevent_passforward",
            },
            # Handle multiple plays.
            {
                "gameId": 1,
                "playId": 2,
                "frameId": 3,
                "nflId": 10,
                "event": "autoevent_ballsnap",
            },
            {
                "gameId": 1,
                "playId": 2,
                "frameId": 9,
                "nflId": 10,
                "event": "ball_snap",
            },
        ]
    )
    actual = clean_event_data(df_tracking)
    expected = [
        {"gameId": 1, "playId": 1, "frameId": 2, "event": None},
        {"gameId": 1, "playId": 1, "frameId": 5, "event": "ball_snap"},
        {"gameId": 1, "playId": 1, "frameId": 8, "event": None},
        {"gameId": 1, "playId": 1, "frameId": 7, "event": "fumble"},
        {"gameId": 1, "playId": 1, "frameId": 9, "event": "fumble"},
        {"gameId": 1, "playId": 1, "frameId": 12, "event": "pass_forward"},
        {"gameId": 1, "playId": 1, "frameId": 14, "event": None},
        {"gameId": 1, "playId": 2, "frameId": 3, "event": "ball_snap"},
        {"gameId": 1, "playId": 2, "frameId": 9, "event": None},
    ]
    assert actual.to_dict(orient="records") == expected
