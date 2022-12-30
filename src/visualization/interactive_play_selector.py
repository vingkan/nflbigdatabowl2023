import ipywidgets as widgets
import pandas as pd

from src.visualization.interactive_pocket_area import (
    create_interactive_pocket_area,
)


def create_interactive_play_selector(
    df_plays_all: pd.DataFrame,
    df_tracking_display_all: pd.DataFrame,
    df_areas_all: pd.DataFrame,
    **kwargs,
):
    """
    Allows the user to choose a play and then renders a nested interactive plot
    of pocket area analytics.

    Parameters:
        df_plays_all: DataFrame of raw play data, for all available plays.
        df_tracking_display_all: DataFrame transformed to contain all columns
            needed for displaying tracking data, for all available plays.
        df_areas_all: DataFrame that includes pocket area data by frame
            and by method, for all available plays.

    For additional visualization parameters in kwargs, see the docstring of the
    create_interactive_play() function.
    """

    def select_play(game_id: str, play_id: str):
        """Update visualization for the given play."""
        # Filter datasets to the given play.
        query = f"gameId == {game_id} and playId == {play_id}"
        df_play = df_plays_all.query(query).iloc[0]
        df_tracking_display = df_tracking_display_all.query(query)
        df_areas = df_areas_all.query(query)

        # Display the play description and another interactive plot.
        print(df_play["playDescription"])
        create_interactive_pocket_area(df_tracking_display, df_areas, **kwargs)

    # Create play ID dropdown, which depends on the selected game ID.
    game_options = df_tracking_display_all["gameId"].unique()
    game_dropdown = widgets.Dropdown(
        options=game_options, value=game_options[0], description="Game ID"
    )
    play_dropdown = widgets.Dropdown(
        options=[], value=None, description="Play ID"
    )

    def update_play_options():
        """When the game dropdown changes, update the play dropdown."""
        game_id = game_dropdown.value
        play_options = df_tracking_display_all.query(f"gameId == {game_id}")[
            "playId"
        ].unique()
        play_dropdown.options = play_options
        play_dropdown.value = play_options[0]

    game_dropdown.observe(update_play_options)
    update_play_options()

    _ = widgets.interact(
        select_play, game_id=game_dropdown, play_id=play_dropdown
    )
