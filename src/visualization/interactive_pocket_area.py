import math
from typing import Dict, List, Optional, Tuple

import ipywidgets as widgets
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.patches import Arrow, Circle, Patch
from matplotlib.patches import Polygon as PolygonPatch
from matplotlib.patches import Rectangle
from matplotlib.ticker import MultipleLocator
from shapely import Polygon as ShapelyPolygon

from src.metrics.pocket_area.base import InvalidPocketError, PocketArea
from src.metrics.pocket_area.helpers import pocket_from_json
from src.visualization.pocket_area import (
    POCKET_KWARGS,
    PocketAreaNestedMap,
    get_pocket_area_nested_map,
    get_pocket_patch,
)

PLOT_RATIO = 0.4
FIG_X_RATIO_ONE_COL = 1.0
FIG_X_RATIO_MULTIPLE_COLS = 1.15
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


def get_frame_plotter(df_tracking, df_areas):
    def plot(game_id, play_id, frame_ids):
        # Get tracking and area data for play.
        query_play = f"gameId == {game_id} and playId == {play_id}"
        df_tracking_play = df_tracking.query(query_play)
        df_areas_play = df_areas.query(query_play)

        def get_patch(frame_id):
            row = df_areas_play[df_areas_play["frameId"] == frame_id].iloc[0]
            pocket = pocket_from_json(row["pocket"])
            patch = get_pocket_patch(pocket)
            area_value = row["area"]
            return [patch], area_value

        # Duplicate pocket underlay for each frame.
        patches_and_area = [get_patch(f) for f in frame_ids]

        # Plot each frame.
        n_cols = len(frame_ids)
        fig, axes = create_play_pocket_figure(df_tracking_play, n_cols)
        for ax, frame, (ps, area) in zip(axes, frame_ids, patches_and_area):
            plot_play_pocket(ax, df_tracking_play, frame, ps)
            area_title = f"Pocket Area = {area:.1f} sq yds"
            frame_and_area_title = f"Frame: {frame}\n{area_title}"
            ax.set_title(frame_and_area_title)

    return plot


def patch_from_polygon(shape: ShapelyPolygon, **kwargs) -> PolygonPatch:
    vertices = list(shape.exterior.coords)
    patch = PolygonPatch(vertices, **kwargs)
    return patch


def get_spotlight_patches(spotlight):
    start_patch = patch_from_polygon(
        spotlight["polygon_difference"],
        color="#ff9cc5",
        alpha=0.5,
    )
    end_patch = patch_from_polygon(
        spotlight["polygon_end"],
        color="#b0e3ff",
        alpha=0.5,
    )
    return [start_patch, end_patch]


def get_spotlight_plotter(df_tracking, df_spotlight_search):
    def plot(game_id, play_id):
        # Get tracking and spotlight data for play.
        query_play = f"gameId == {game_id} and playId == {play_id}"
        df_tracking_play = df_tracking.query(query_play)
        spotlight = df_spotlight_search.query(query_play).reset_index().iloc[0]

        # Select start, mid, and end frames.
        frame_start = spotlight["window_start"]
        frame_end = spotlight["window_end"]
        frame_mid = ((frame_end - frame_start) // 2) + frame_start
        frame_ids = [frame_start, frame_mid, frame_end]

        # Duplicate pocket underlay for each frame.
        patches_list = [get_spotlight_patches(spotlight) for _ in frame_ids]

        # Plot each frame.
        fig, axes = create_play_pocket_figure(df_tracking_play, n_cols=3)
        for ax, frame, patches in zip(axes, frame_ids, patches_list):
            plot_play_pocket(ax, df_tracking_play, frame, patches)

    return plot


def get_play_pocket_bounds(
    df_tracking_display: pd.DataFrame,
) -> Tuple[float, float, float, float]:
    # Filter tracking data for the play to players with pocket-related roles.
    df_pocket_only = df_tracking_display.query(f"pff_role in {RELEVANT_ROLES}")

    # Get bounding box only for the players involved in the pocket.
    x = df_pocket_only["x"]
    y = df_pocket_only["y"]
    x_min = x.min() - MARGIN_YARD_LINES
    x_max = x.max() + MARGIN_YARD_LINES
    y_min = y.min() - MARGIN_YARD_LINES
    y_max = y.max() + MARGIN_YARD_LINES

    return x_min, x_max, y_min, y_max


def get_viewable_objects(
    df_tracking_display: pd.DataFrame,
    pocket_bounds: Tuple[float, float, float, float],
) -> pd.DataFrame:
    # Get tracking data for players viewable within the pocket bounding box.
    x_min, x_max, y_min, y_max = pocket_bounds
    viewable_query = f"({x_min} <= x <= {x_max}) and ({y_min} <= y <= {y_max})"
    df_viewable = df_tracking_display.query(viewable_query)
    return df_viewable.to_dict(orient="records")


def create_play_pocket_figure(df_tracking: pd.DataFrame, n_cols: int):
    # Get bounding box only for the players involved in the pocket.
    pocket_bounds = get_play_pocket_bounds(df_tracking)

    # Determine figure dimensions based on play pocket bounds.
    x_min, x_max, y_min, y_max = pocket_bounds
    x_dim = PLOT_RATIO * (x_max - x_min)
    y_dim = PLOT_RATIO * (y_max - y_min)

    # Determine whether to create one plot or two (dual mode).
    n_rows = 1
    axes = []
    subplots = plt.subplots(n_rows, n_cols)
    if n_cols == 1:
        fig, ax0 = subplots
        axes = [ax0]
        fig_ratio = FIG_X_RATIO_ONE_COL
    elif n_cols == 2:
        fig, (ax0, ax1) = subplots
        axes = [ax0, ax1]
        fig_ratio = FIG_X_RATIO_MULTIPLE_COLS
    elif n_cols == 3:
        fig, (ax0, ax1, ax2) = subplots
        axes = [ax0, ax1, ax2]
        fig_ratio = FIG_X_RATIO_MULTIPLE_COLS
    else:
        raise ValueError(f"Invalid number of plot columns: {n_cols}")

    # Update figure dimensions.
    x_fig = fig_ratio * n_cols * x_dim
    y_fig = n_rows * y_dim
    fig.set_size_inches(x_fig, y_fig)

    # Configure axes for play pocket plot.
    for ax in axes:
        ax.set_axisbelow(True)
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.xaxis.set_major_locator(MultipleLocator(MAJOR_YARD_LINE))
        ax.yaxis.set_major_locator(MultipleLocator(MAJOR_YARD_LINE))
        ax.xaxis.set_minor_locator(MultipleLocator(MINOR_YARD_LINE))
        ax.yaxis.set_minor_locator(MultipleLocator(MINOR_YARD_LINE))
        ax.grid(which="both", **GRID_LINE_KWARGS)

    return subplots


def plot_play_pocket(
    ax: Axes,
    df_tracking: pd.DataFrame,
    frame_id: int,
    pocket_layer: Optional[List[Patch]] = None,
):
    if pocket_layer is None:
        pocket_layer = []

    # Get bounding box only for the players involved in the pocket.
    pocket_bounds = get_play_pocket_bounds(df_tracking)

    # Get objects for players viewable, just for this frame.
    df_tracking_frame = df_tracking[df_tracking["frameId"] == frame_id]
    viewable_objects = get_viewable_objects(df_tracking_frame, pocket_bounds)

    # Configure axes for frame and pocket area plot.
    frame_title = f"Frame {frame_id}"
    ax.set_title(frame_title)

    # Create and plot layers of patches.
    player_layer = get_player_patches(viewable_objects)
    patches_layers = [pocket_layer, player_layer]
    plot_pocket_players(ax, patches_layers)
    plot_jersey_numbers(ax, viewable_objects)


def plot_pocket_players(ax: Axes, patches_layers: List[List[Patch]]):
    # Plot patches in layer order.
    for layer in patches_layers:
        for patch in layer:
            ax.add_patch(patch)


def get_player_patches(objects: List[Dict]) -> List[Patch]:
    # Create graphics for each object in the frame.
    patches = []
    for p in objects:
        # Get attributes used by all objects.
        x, y = p["x"], p["y"]
        role = p["pff_role"]
        color = ROLE_TO_COLOR.get(role, "lightgray")

        # Render football.
        if role == FOOTBALL_ROLE:
            ball = Circle((x, y), FOOTBALL_RADIUS, color=color)
            patches.append(ball)
            continue

        # Render player direction arrow.
        degrees = p["dir"]
        radians = math.radians((-1 * degrees) + 90)
        dx = math.cos(radians)
        dy = math.sin(radians)
        direction = Arrow(x, y, dx, dy, color="lightgray")
        patches.append(direction)

        # Render player orientation arrow.
        degrees = p["o"]
        radians = math.radians((-1 * degrees) + 90)
        dx = math.cos(radians)
        dy = math.sin(radians)
        orientation = Arrow(x, y, dx, dy, color=color)
        patches.append(orientation)

        # Render player.
        circle = Circle((x, y), PLAYER_RADIUS, color=color)
        patches.append(circle)

        # Render player jersey number.
        y_offset = Y_OFFSET_JERSEY
        x_offset = X_OFFSET_SINGLE_JERSEY_NUMBER
        if len(str(p["jerseyNumber"])) > 1:
            x_offset = X_OFFSET_DOUBLE_JERSEY_NUMBER
        # text = ax.text(
        #     x - x_offset,
        #     y - y_offset,
        #     p["jerseyNumber"],
        #     fontsize=FONT_SIZE,
        #     color="white",
        # )
        # TODO(vinesh): Handle text for jersey number.

    return patches


def plot_jersey_numbers(ax: Axes, objects: List[Dict]):
    # Currently, we have to plot text for jersey numbers separately because
    # text is a method of the plot, not a patch.
    for p in objects:
        # Get attributes used by all objects.
        x, y = p["x"], p["y"]
        role = p["pff_role"]

        # No jersey number needed for the football.
        if role == FOOTBALL_ROLE:
            continue

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


def get_play_pocket_and_timeline_plotter_multiple(
    df_tracking_display: pd.DataFrame,
    df_areas: pd.DataFrame,
):
    # Get bounding box only for the players involved in the pocket.
    pocket_bounds = get_play_pocket_bounds(df_tracking_display)
    viewable_objects = get_viewable_objects(df_tracking_display, pocket_bounds)

    # Determine figure dimensions based on play pocket bounds.
    x_min, x_max, y_min, y_max = pocket_bounds
    x_dim = PLOT_RATIO * (x_max - x_min)
    y_dim = PLOT_RATIO * (y_max - y_min)

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
    for obj in viewable_objects:
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

    def plot_play_frame(frame_id: int, area_method: str, ax, ax2):
        """Inner function to redraw plot for the given frame."""
        # Retrieve only the objects for this frame.
        objects = objects_per_frame.get(frame_id, [])

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
        pocket_layer = []
        pocket = stored_pockets.get(frame_id, {}).get(area_method)
        if pocket:
            # Add pocket area to title.
            area_title = f"Pocket Area = {pocket.area:.1f} sq yds"
            frame_and_area_title = f"{frame_title}\n{area_title}"
            ax.set_title(frame_and_area_title)

            # Render pocket.
            pocket_patch = get_pocket_patch(pocket)
            if pocket_patch:
                pocket_layer.append(pocket_patch)

        # Plot layers for pocket play visualizer.
        player_layer = get_player_patches(objects)
        patches_layers = [pocket_layer, player_layer]
        plot_pocket_players(ax, patches_layers)
        plot_jersey_numbers(ax, objects)

    def plot_multiple(frame0: int, frame1: int, area_method: str):
        # Configure figure and axes.
        n_rows = 2
        n_cols = 2
        fig, ((ax0, ax1), (ax2, ax3)) = plt.subplots(n_rows, n_cols)
        x_fig = FIG_X_RATIO_MULTIPLE_COLS * n_cols * x_dim
        y_fig = n_rows * y_dim
        fig.set_size_inches(x_fig, y_fig)
        # Plot each frame and timeline.
        plot_play_frame(frame0, area_method, ax0, ax1)
        plot_play_frame(frame1, area_method, ax2, ax3)

    other_info = (pocket_area_methods, x_dim, max_frames)
    return plot_multiple, other_info


def get_play_pocket_and_timeline_plotter(
    df_tracking_display: pd.DataFrame,
    df_areas: pd.DataFrame,
):
    # Get bounding box only for the players involved in the pocket.
    pocket_bounds = get_play_pocket_bounds(df_tracking_display)
    viewable_objects = get_viewable_objects(df_tracking_display, pocket_bounds)

    # Determine figure dimensions based on play pocket bounds.
    x_min, x_max, y_min, y_max = pocket_bounds
    x_dim = PLOT_RATIO * (x_max - x_min)
    y_dim = PLOT_RATIO * (y_max - y_min)

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
    for obj in viewable_objects:
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
        x_fig = FIG_X_RATIO_MULTIPLE_COLS * n_cols * x_dim
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
        pocket_layer = []
        pocket = stored_pockets.get(frame_id, {}).get(area_method)
        if pocket:
            # Add pocket area to title.
            area_title = f"Pocket Area = {pocket.area:.1f} sq yds"
            frame_and_area_title = f"{frame_title}\n{area_title}"
            ax.set_title(frame_and_area_title)

            # Render pocket.
            pocket_patch = get_pocket_patch(pocket)
            if pocket_patch:
                pocket_layer.append(pocket_patch)

        # Plot layers for pocket play visualizer.
        player_layer = get_player_patches(objects)
        patches_layers = [pocket_layer, player_layer]
        plot_pocket_players(ax, patches_layers)
        plot_jersey_numbers(ax, objects)

    other_info = (pocket_area_methods, x_dim, max_frames)
    return plot_play_frame, other_info


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
    pocket_area_methods = list(df_areas["method"].unique())
    plot_play_frame, vis_info = get_play_pocket_and_timeline_plotter(
        df_tracking_display, df_areas
    )
    pocket_area_methods, x_dim, max_frames = vis_info

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
