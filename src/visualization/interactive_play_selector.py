from typing import Dict, Optional

import ipywidgets as widgets
import pandas as pd
from IPython.display import HTML, display

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
        df_play_results = df_plays_all.query(query)
        if len(df_play_results) == 0:
            display(HTML("<p>No results.</p>"))
            return

        df_play = df_play_results.iloc[0]
        df_tracking_display = df_tracking_display_all.query(query)
        df_areas = df_areas_all.query(query)

        # Display the play description and another interactive plot.
        play_description = df_play["playDescription"]
        display(HTML(f"<p>{play_description}</p>"))
        create_interactive_pocket_area(df_tracking_display, df_areas, **kwargs)

    # Create play ID dropdown, which depends on the selected game ID.
    game_options = df_tracking_display_all["gameId"].unique()
    game_dropdown = widgets.Dropdown(
        options=game_options, value=game_options[0], description="Game ID"
    )
    play_dropdown = widgets.Dropdown(
        options=[], value=None, description="Play ID"
    )

    def update_play_options(change: Optional[Dict] = None):
        """When the game dropdown changes, update the play dropdown."""
        if change is None:
            return

        game_id = change.get("new")
        if game_id is None:
            return

        game_query = f"gameId == {game_id}"
        df_game_only = df_tracking_display_all.query(game_query)
        play_options = df_game_only["playId"].unique()
        play_dropdown.options = play_options
        play_dropdown.value = play_options[0]

    game_dropdown.observe(update_play_options, names="value")
    update_play_options({"new": game_dropdown.value})

    _ = widgets.interact(
        select_play, game_id=game_dropdown, play_id=play_dropdown
    )
