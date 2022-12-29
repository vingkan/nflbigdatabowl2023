import math
from typing import Dict, List

import ipywidgets as widgets
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import MultipleLocator

PLOT_RATIO = 0.4
PIXEL_RATIO = 100

PLAYER_DIAMETER = 1
FONT_SIZE = 10 * PLAYER_DIAMETER
PLAYER_RADIUS = 0.5 * PLAYER_DIAMETER
FOOTBALL_RADIUS = 0.5 * PLAYER_RADIUS

Y_OFFSET = 0.175 * PLAYER_DIAMETER
X_OFFSET_DOUBLE_JERSEY_NUMBER = 0.375 * PLAYER_DIAMETER
X_OFFSET_SINGLE_JERSEY_NUMBER = 0.2 * PLAYER_DIAMETER

RIGHT_ANGLE_DEGREES = 90

MAJOR_YARD_LINE = 5
MINOR_YARD_LINE = 1

FOOTBALL_ROLE = "Football"
RELEVANT_ROLES = "('Pass', 'Pass Block', 'Pass Rush', 'Football')"

ROLE_TO_COLOR = {
    "Football": "#4a3600",
    "Pass": "#02bda4",
    "Pass Block": "#027bbd",
    "Pass Rush": "#bd0250",
}


def create_interactive_play(df_tracking_display: pd.DataFrame):
    """
    Creates an interactive plot of a play, with a slider to seek frames.

    The inner function plot_play_frame(frame_id) contains all the logic needed
    on each frame redraw. The outer function scope contains the logic that can
    be run once before activating the interactive plot.

    Parameters:
        df_tracking_display: DataFrame transformed to contain all the
            columns needed for displaying tracking data, already
            filtered to only include a single play.
    """

    # Filter to relevant roles
    df_relevant = df_tracking_display.query(f"pff_role in {RELEVANT_ROLES}")

    # Get bounding box for entire play.
    x = df_relevant["x"]
    y = df_relevant["y"]
    x_min = x.min()
    x_max = x.max()
    y_min = y.min()
    y_max = y.max()
    x_dim = PLOT_RATIO * (x_max - x_min)
    y_dim = PLOT_RATIO * (y_max - y_min)

    # Get frame range.
    max_frames = df_relevant["frameId"].max()

    # Store objects for each frame to avoid filtering cost on each redraw.
    objects_per_frame: Dict[int, List[Dict]] = {}
    for obj in df_relevant.to_dict(orient="records"):
        frame_id = obj["frameId"]
        if frame_id not in objects_per_frame:
            objects_per_frame[frame_id] = []
        objects_per_frame[frame_id].append(obj)

    def plot_play_frame(frame_id: int):
        """Inner function to redraw plot for the given frame."""
        # Retrieve only the objects for this frame.
        objects = objects_per_frame.get(frame_id, [])

        # Configure figure and axes.
        fig, ax = plt.subplots(1, 1)
        fig.set_size_inches(x_dim, y_dim)

        ax.set_title(f"Frame {frame_id}")
        ax.set_axisbelow(True)

        ax.set_xlim(x_min - MINOR_YARD_LINE, x_max + MINOR_YARD_LINE)
        ax.set_ylim(y_min - MINOR_YARD_LINE, y_max + MINOR_YARD_LINE)

        ax.xaxis.set_major_locator(MultipleLocator(MAJOR_YARD_LINE))
        ax.yaxis.set_major_locator(MultipleLocator(MAJOR_YARD_LINE))
        ax.xaxis.set_minor_locator(MultipleLocator(MINOR_YARD_LINE))
        ax.yaxis.set_minor_locator(MultipleLocator(MINOR_YARD_LINE))

        ax.grid(which="both", color="lightgray", linestyle="-", linewidth=1)

        # Create graphics for each object in the frame.
        for p in objects:
            # Get attributes used by all objects.
            x, y = p["x"], p["y"]
            role = p["pff_role"]
            color = ROLE_TO_COLOR.get(role, "lightgray")

            # Render football.
            if role == FOOTBALL_ROLE:
                ball = plt.Circle((x, y), FOOTBALL_RADIUS, color=color)
                ax.add_patch(ball)
                continue

            # Render player orientation arrow.
            degrees = p["o"]
            radians = math.radians((-1 * degrees) + 90)
            dx = math.cos(radians)
            dy = math.sin(radians)
            orientation = ax.arrow(x, y, dx, dy, color=color)

            # Render player direction arrow.
            degrees = p["dir"]
            radians = math.radians((-1 * degrees) + 90)
            dx = math.cos(radians)
            dy = math.sin(radians)
            direction = ax.arrow(x, y, dx, dy, color="lightgray")

            # Render player.
            circle = plt.Circle((x, y), PLAYER_RADIUS, color=color)
            ax.add_patch(circle)

            # Render player jersey number.
            y_offset = Y_OFFSET
            x_offset = X_OFFSET_SINGLE_JERSEY_NUMBER
            if len(str(p["jerseyNumber"])) > 1:
                x_offset = X_OFFSET_DOUBLE_JERSEY_NUMBER
            text = ax.text(
                x - x_offset,
                y - y_offset,
                p["jerseyNumber"],
                fontsize=FONT_SIZE,
                color="white",
            )

    # Attach an interactive slider to the redraw function.
    slider_pixels = PIXEL_RATIO * x_dim
    layout = widgets.Layout(width=f"{slider_pixels}px")
    slider = widgets.IntSlider(
        min=1, max=max_frames, step=1, value=1, layout=layout
    )
    _ = widgets.interact(plot_play_frame, frame_id=slider)
