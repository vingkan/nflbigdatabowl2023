import math
from typing import Dict, List

import dacite
import ipywidgets as widgets
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.patches import Circle, Patch, Polygon, Rectangle
from matplotlib.ticker import MultipleLocator

from src.metrics.pocket_area.base import InvalidPocketError, PocketArea
from src.visualization.pocket_area import (
    POCKET_KWARGS,
    PocketAreaNestedMap,
    get_pocket_area_nested_map,
    get_pocket_patch,
)

PLOT_RATIO = 0.4
FIG_X_RATIO = 1.15
PIXEL_RATIO = 80

PLAYER_DIAMETER = 1
FONT_SIZE = 10 * PLAYER_DIAMETER
PLAYER_RADIUS = 0.5 * PLAYER_DIAMETER
FOOTBALL_RADIUS = 0.5 * PLAYER_RADIUS

Y_OFFSET_JERSEY = 0.175 * PLAYER_DIAMETER
X_OFFSET_DOUBLE_JERSEY_NUMBER = 0.375 * PLAYER_DIAMETER
X_OFFSET_SINGLE_JERSEY_NUMBER = 0.2 * PLAYER_DIAMETER

Y_MAX_AREA_RATIO = 1.1

X_OFFSET_EVENT = 0.5
Y_OFFSET_FACTOR_EVENT = 0.075

RIGHT_ANGLE_DEGREES = 90

MAJOR_YARD_LINE = 5
MINOR_YARD_LINE = 1
MARGIN_YARD_LINES = 2

FOOTBALL_ROLE = "Football"
RELEVANT_ROLES = "('Pass', 'Pass Block', 'Pass Rush', 'Football')"

GRID_LINE_KWARGS = dict(color="lightgray", linestyle="--", linewidth=1)
EVENT_LINE_KWARGS = dict(color="#eb6734", linestyle="--", linewidth=1)
FRAME_LINE_KWARGS = dict(color="#02bda4", linestyle="--", linewidth=1)

INELIGIBILITY_WINDOW_KWARGS = dict(color="lightgray", alpha=0.25, hatch="///")

ROLE_TO_COLOR = {
    "Football": "#4a3600",
    "Pass": "#02bda4",
    "Pass Block": "#027bbd",
    "Pass Rush": "#bd0250",
}


def plot_pocket_area_timeline(
    ax: Axes,
    frame_id: int,
    df_play_areas: pd.DataFrame,
    df_events: pd.DataFrame,
):
    # Get data to plot.
    ser_frame = df_play_areas["frameId"]
    ser_area = df_play_areas["area"]
    max_frame = ser_frame.max()
    max_area = ser_area.max()
    plot_y_max = Y_MAX_AREA_RATIO * max_area

    # Configure axes for timeline plot.
    ax.set_xlabel("Frame")
    ax.set_ylabel("Pocket Area")
    ax.set_xlim(1, max_frame)
    ax.set_ylim(0, plot_y_max)
    ax.grid(axis="y", **GRID_LINE_KWARGS)

    # Plot window when the play was eligible for a pocket.
    # Accomplish this by shading out the frames that were ineligible.
    # Assumes the pocket window is continuous from min frame to max frame.
    eligibility_start = df_events.iloc[0]["frame_start"]
    eligibility_end = df_events.iloc[0]["frame_end"]
    ineligibility_start = Rectangle(
        xy=(0, 0),
        width=(eligibility_start),
        height=plot_y_max,
        **INELIGIBILITY_WINDOW_KWARGS,
    )
    ax.add_patch(ineligibility_start)
    ineligibility_end = Rectangle(
        xy=(eligibility_end, 0),
        width=(max_frame - eligibility_end),
        height=plot_y_max,
        **INELIGIBILITY_WINDOW_KWARGS,
    )
    ax.add_patch(ineligibility_end)

    # Plot pocket area over time.
    ax.fill_between(ser_frame, ser_area, **POCKET_KWARGS)

    # Plot play events.
    for i, row in df_events.iterrows():
        event_frame_id = row["frameId"]
        event = row["event"]
        x = event_frame_id
        y = plot_y_max
        x_offset = X_OFFSET_EVENT
        y_offset = Y_OFFSET_FACTOR_EVENT * plot_y_max * (i + 2)
        ax.axvline(x=x, ymin=0, ymax=plot_y_max, **EVENT_LINE_KWARGS)
        ax.text(
            x + x_offset,
            y - y_offset,
            event,
            fontsize=FONT_SIZE,
            color=EVENT_LINE_KWARGS.get("color"),
        )

    # Plot a vertical line at the current frame.
    x = frame_id
    y = plot_y_max
    x_offset = X_OFFSET_EVENT
    y_offset = Y_OFFSET_FACTOR_EVENT * plot_y_max
    ax.axvline(x=x, ymin=0, ymax=plot_y_max, **FRAME_LINE_KWARGS)
    ax.text(
        x + x_offset,
        y - y_offset,
        "Current Frame",
        fontsize=FONT_SIZE,
        color=FRAME_LINE_KWARGS.get("color"),
    )


def create_interactive_pocket_area(
    df_tracking_display: pd.DataFrame,
    df_areas: pd.DataFrame,
    continuous_update: bool = False,
):
    """
    Creates an interactive plot of a play, with a slider to seek frames.

    The inner function plot_play_frame(frame_id) contains all the logic needed
    on each frame redraw. The outer function scope contains the logic that can
    be run once before activating the interactive plot.

    Parameters:
        df_tracking_display: DataFrame transformed to contain all columns
            needed for displaying tracking data, already filtered to only
            include a single play.
        df_areas: Optional DataFrame that includes pocket area data by frame
            and by method, already filtered to only include a single play.

    Additional Visualization Parameters:
        continuous_update: If True, redraw the plot while dragging the frame ID
            slider. If False (default), only redraw after releasing the slider.
    """

    # Filter to relevant roles
    df_pocket_only = df_tracking_display.query(f"pff_role in {RELEVANT_ROLES}")

    # Get bounding box only for the players involved in the pocket.
    x = df_pocket_only["x"]
    y = df_pocket_only["y"]
    x_min = x.min() - MARGIN_YARD_LINES
    x_max = x.max() + MARGIN_YARD_LINES
    y_min = y.min() - MARGIN_YARD_LINES
    y_max = y.max() + MARGIN_YARD_LINES
    x_dim = PLOT_RATIO * (x_max - x_min)
    y_dim = PLOT_RATIO * (y_max - y_min)

    # Get tracking data for players viewable within the pocket bounding box.
    viewable_query = f"({x_min} <= x <= {x_max}) and ({y_min} <= y <= {y_max})"
    df_viewable = df_tracking_display.query(viewable_query)

    # Get frame range.
    max_frames = df_tracking_display["frameId"].max()

    # Get the events in the play from the tracking data.
    df_events = (
        df_tracking_display[["frameId", "event", "frame_start", "frame_end"]][
            df_tracking_display["event"].notna()
        ]
        .drop_duplicates()
        .reset_index()
    )

    # Store objects for each frame to avoid filtering cost on each redraw.
    objects_per_frame: Dict[int, List[Dict]] = {}
    for obj in df_viewable.to_dict(orient="records"):
        frame_id = obj["frameId"]
        if frame_id not in objects_per_frame:
            objects_per_frame[frame_id] = []
        objects_per_frame[frame_id].append(obj)

    # Parse and store pocket for each frame and method.
    stored_pockets: PocketAreaNestedMap = get_pocket_area_nested_map(df_areas)

    # Store the area timeline data for each method.
    area_timeline_by_method: Dict[str, pd.DataFrame] = {}
    pocket_area_methods = list(df_areas["method"].unique())
    for method in pocket_area_methods:
        df_method_areas = df_areas.query(f"method == '{method}'")
        area_timeline_by_method[method] = df_method_areas

    def plot_play_frame(frame_id: int, area_method: str):
        """Inner function to redraw plot for the given frame."""
        # Retrieve only the objects for this frame.
        objects = objects_per_frame.get(frame_id, [])

        # Configure figure and axes.
        n_rows = 1
        n_cols = 2
        fig, (ax, ax2) = plt.subplots(n_rows, n_cols)
        x_fig = FIG_X_RATIO * n_cols * x_dim
        y_fig = n_rows * y_dim
        fig.set_size_inches(x_fig, y_fig)

        # Configure axes for frame and pocket area plot.
        frame_title = f"Frame {frame_id}"
        ax.set_title(frame_title)
        ax.set_axisbelow(True)

        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)

        ax.xaxis.set_major_locator(MultipleLocator(MAJOR_YARD_LINE))
        ax.yaxis.set_major_locator(MultipleLocator(MAJOR_YARD_LINE))
        ax.xaxis.set_minor_locator(MultipleLocator(MINOR_YARD_LINE))
        ax.yaxis.set_minor_locator(MultipleLocator(MINOR_YARD_LINE))

        ax.grid(which="both", **GRID_LINE_KWARGS)

        # Plot the pocket area over time for the play, if available.
        df_play_areas = area_timeline_by_method.get(area_method)
        if df_play_areas is not None:
            plot_pocket_area_timeline(ax2, frame_id, df_play_areas, df_events)

        # Render pocket, if any.
        pocket = stored_pockets.get(frame_id, {}).get(area_method)
        if pocket:
            # Add pocket area to title.
            area_title = f"Pocket Area = {pocket.area:.1f} sq yds"
            frame_and_area_title = f"{frame_title}\n{area_title}"
            ax.set_title(frame_and_area_title)

            # Render pocket.
            pocket_patch = get_pocket_patch(pocket)
            if pocket_patch:
                ax.add_patch(pocket_patch)

        # Create graphics for each object in the frame.
        for p in objects:
            # Get attributes used by all objects.
            x, y = p["x"], p["y"]
            role = p["pff_role"]
            color = ROLE_TO_COLOR.get(role, "lightgray")

            # Render football.
            if role == FOOTBALL_ROLE:
                ball = Circle((x, y), FOOTBALL_RADIUS, color=color)
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
            circle = Circle((x, y), PLAYER_RADIUS, color=color)
            ax.add_patch(circle)

            # Render player jersey number.
            y_offset = Y_OFFSET_JERSEY
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
    layout_width_pixels = PIXEL_RATIO * x_dim
    layout = widgets.Layout(width=f"{layout_width_pixels}px")
    slider = widgets.IntSlider(
        min=1,
        max=max_frames,
        step=1,
        value=1,
        description="Frame",
        layout=layout,
        continuous_update=continuous_update,
    )

    # Attach an interactive dropdown to choose the pocket area algorithm.
    dropdown = widgets.Dropdown(
        options=pocket_area_methods,
        value=pocket_area_methods[0],
        description="Area Type",
        layout=layout,
        disabled=False,
    )

    _ = widgets.interact(plot_play_frame, frame_id=slider, area_method=dropdown)
