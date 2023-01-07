import pandas as pd

from src.pipeline.tasks.eligibility import (
    get_passer_out_of_pocket,
    get_pocket_eligibility,
)


def test_get_passer_out_of_pocket():
    max_yards_from_snap = 10
    p = {"gameId": 1, "playId": 1}
    df_tracking = pd.DataFrame(
        [
            {
                **p,
                "frameId": 1,
                "team": "football",
                "x": 20,
                "event": "ball_snap",
            },
            {**p, "frameId": 1, "team": "CHI", "nflId": 1, "x": 20},
            {**p, "frameId": 1, "team": "CHI", "nflId": 32, "x": 25},
            {**p, "frameId": 2, "team": "CHI", "nflId": 1, "x": 11},
            {**p, "frameId": 3, "team": "CHI", "nflId": 1, "x": 10},
            {**p, "frameId": 4, "team": "CHI", "nflId": 1, "x": 9},
            {**p, "frameId": 5, "team": "CHI", "nflId": 1, "x": 10},
        ]
    )
    df_pff = pd.DataFrame([{**p, "nflId": 1, "pff_role": "Pass"}])
    actual = get_passer_out_of_pocket(df_tracking, df_pff, max_yards_from_snap)
    expected = [
        {**p, "frameId": 1, "passer_out_of_pocket": False},
        {**p, "frameId": 2, "passer_out_of_pocket": False},
        {**p, "frameId": 3, "passer_out_of_pocket": False},
        {**p, "frameId": 4, "passer_out_of_pocket": True},
        # TODO(vinesh): Possibly do not allow passer to come back into pocket.
        {**p, "frameId": 5, "passer_out_of_pocket": False},
    ]
    assert actual.to_dict(orient="records") == expected


def test_get_pocket_eligibility():
    play_1 = {"gameId": 1, "playId": 1}
    df_events = pd.DataFrame(
        [
            {**play_1, "frameId": 1, "event": None},
            {**play_1, "frameId": 2, "event": None},
            {**play_1, "frameId": 3, "event": "ball_snap"},
            {**play_1, "frameId": 4, "event": None},
            {**play_1, "frameId": 5, "event": None},
            {**play_1, "frameId": 6, "event": None},
            {**play_1, "frameId": 7, "event": "fumble"},
            {**play_1, "frameId": 8, "event": None},
            {**play_1, "frameId": 9, "event": "fumble_recovered_offense"},
            {**play_1, "frameId": 10, "event": None},
            {**play_1, "frameId": 11, "event": "fumble"},
            {**play_1, "frameId": 12, "event": None},
        ]
    )
    df_passer_out_of_pocket = pd.DataFrame(
        [
            {**play_1, "frameId": frame_id, "passer_out_of_pocket": False}
            for frame_id in range(1, 13)
        ]
    )
    actual = get_pocket_eligibility(df_events, df_passer_out_of_pocket)
    p = {"gameId": 1, "playId": 1}
    pocket = {"frame_start": 3, "frame_end": 7}
    expected = [
        {**p, "frameId": 1, "event": None, **pocket},
        {**p, "frameId": 2, "event": None, **pocket},
        {**p, "frameId": 3, "event": "ball_snap", **pocket},
        {**p, "frameId": 4, "event": None, **pocket},
        {**p, "frameId": 5, "event": None, **pocket},
        {**p, "frameId": 6, "event": None, **pocket},
        {**p, "frameId": 7, "event": "fumble", **pocket},
        {**p, "frameId": 8, "event": None, **pocket},
        {**p, "frameId": 9, "event": "fumble_recovered_offense", **pocket},
        {**p, "frameId": 10, "event": None, **pocket},
        {**p, "frameId": 11, "event": "fumble", **pocket},
        {**p, "frameId": 12, "event": None, **pocket},
    ]
    assert actual.to_dict(orient="records") == expected


def test_get_pocket_eligibility_passer_left_pocket():
    play_1 = {"gameId": 1, "playId": 1}
    df_events = pd.DataFrame(
        [
            {**play_1, "frameId": 1, "event": None},
            {**play_1, "frameId": 2, "event": "ball_snap"},
            {**play_1, "frameId": 3, "event": None},
            {**play_1, "frameId": 4, "event": None},
        ]
    )
    df_passer_out_of_pocket = pd.DataFrame(
        [
            {**play_1, "frameId": 1, "passer_out_of_pocket": False},
            {**play_1, "frameId": 2, "passer_out_of_pocket": False},
            {**play_1, "frameId": 3, "passer_out_of_pocket": False},
            {**play_1, "frameId": 4, "passer_out_of_pocket": True},
        ]
    )
    actual = get_pocket_eligibility(df_events, df_passer_out_of_pocket)
    p = {"gameId": 1, "playId": 1}
    pocket = {"frame_start": 2, "frame_end": 4}
    expected = [
        {**p, "frameId": 1, "event": None, **pocket},
        {**p, "frameId": 2, "event": "ball_snap", **pocket},
        {**p, "frameId": 3, "event": None, **pocket},
        {**p, "frameId": 4, "event": None, **pocket},
    ]
    assert actual.to_dict(orient="records") == expected


def test_get_pocket_eligibility_never_started():
    play_1 = {"gameId": 1, "playId": 1}
    df_events = pd.DataFrame(
        [
            {**play_1, "frameId": 1, "event": None},
            {**play_1, "frameId": 2, "event": "line_set"},
            {**play_1, "frameId": 3, "event": None},
            {**play_1, "frameId": 4, "event": None},
        ]
    )
    df_passer_out_of_pocket = pd.DataFrame(
        [
            {**play_1, "frameId": 1, "passer_out_of_pocket": False},
            {**play_1, "frameId": 2, "passer_out_of_pocket": False},
            {**play_1, "frameId": 3, "passer_out_of_pocket": False},
            {**play_1, "frameId": 4, "passer_out_of_pocket": False},
        ]
    )
    actual = get_pocket_eligibility(df_events, df_passer_out_of_pocket)
    p = {"gameId": 1, "playId": 1}
    pocket = {"frame_start": None, "frame_end": None}
    expected = [
        {**p, "frameId": 1, "event": None, **pocket},
        {**p, "frameId": 2, "event": "line_set", **pocket},
        {**p, "frameId": 3, "event": None, **pocket},
        {**p, "frameId": 4, "event": None, **pocket},
    ]
    assert actual.to_dict(orient="records") == expected


def test_get_pocket_eligibility_never_ended():
    play_1 = {"gameId": 1, "playId": 1}
    df_events = pd.DataFrame(
        [
            {**play_1, "frameId": 1, "event": None},
            {**play_1, "frameId": 2, "event": "ball_snap"},
            {**play_1, "frameId": 3, "event": None},
            {**play_1, "frameId": 4, "event": "pump_fake"},
            {**play_1, "frameId": 5, "event": None},
        ]
    )
    df_passer_out_of_pocket = pd.DataFrame(
        [
            {**play_1, "frameId": 1, "passer_out_of_pocket": False},
            {**play_1, "frameId": 2, "passer_out_of_pocket": False},
            {**play_1, "frameId": 3, "passer_out_of_pocket": False},
            {**play_1, "frameId": 4, "passer_out_of_pocket": False},
            {**play_1, "frameId": 5, "passer_out_of_pocket": False},
        ]
    )
    actual = get_pocket_eligibility(df_events, df_passer_out_of_pocket)
    p = {"gameId": 1, "playId": 1}
    pocket = {"frame_start": 2, "frame_end": 5}
    expected = [
        {**p, "frameId": 1, "event": None, **pocket},
        {**p, "frameId": 2, "event": "ball_snap", **pocket},
        {**p, "frameId": 3, "event": None, **pocket},
        {**p, "frameId": 4, "event": "pump_fake", **pocket},
        {**p, "frameId": 5, "event": None, **pocket},
    ]
    assert actual.to_dict(orient="records") == expected
