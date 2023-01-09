import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Polygon as PolygonPatch
from matplotlib.ticker import MultipleLocator
from mpl_toolkits.axes_grid1 import make_axes_locatable
from shapely import Point as ShapelyPoint
from shapely import Polygon as ShapelyPolygon


def heatmap_from_points(points, total, bin_start, bin_end, bin_size):
    x = [p[0] for p in points]
    y = [p[1] for p in points]

    # Heatmap binning logic based on: https://stackoverflow.com/a/61632120
    bins = np.arange(bin_start, bin_end + bin_size, bin_size)
    heatmap, xedges, yedges = np.histogram2d(
        # Numpy uses the first dimension of the returned matrix for x and
        # the second dimension for y, but plotting this with imshow will
        # show a rotated image, so it is easier to swap the coordinates
        # before computing the Numpy histogram.
        x=y,
        y=x,
        bins=[bins, bins],
        # Actually we need to use bin_count / play_count, which
        # would be shape count in this case. So turn density off.
        # Density = bin_count / total_count / bin_area
        # Should we divide by bin area? If the results look wrong,
        # then we can just do bin_count / total_count ourselves.
        # density=True,
    )

    extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]

    # Reduce the heatmap values to the range [0, 1] by dividing by
    # the total number of observations the points were sampled from.
    # Note: This is not the total number of points.
    scaled_heatmap = heatmap / total

    return scaled_heatmap, extent


def sample_points_in_shapes(shapes, bin_start, bin_end, bin_size, progress):
    sample_range = np.arange(bin_start, bin_end + bin_size, bin_size)
    half_bin = bin_size / 2.0
    points_in_pocket = []
    # This triple for-loop is inefficient, optimize with vector operations.
    sample_points = [(x, y) for x in sample_range for y in sample_range]

    # Show progress bar, if requested.
    if progress:
        from tqdm.notebook import tqdm

        progress_bar = tqdm(sample_points)
    else:
        progress_bar = sample_points

    for x, y in progress_bar:
        # Sample point should be in the midpoint of the cell.
        sample_point = (x + half_bin, y + half_bin)
        # Display point for heatmap should be on the cell edge.
        display_point = (x, y)
        # Convert sample point to a shapely point to compare to polygon.
        shape_point = ShapelyPoint(*sample_point)
        for shape in shapes:
            # Also use the exterior so that both points inside the shape
            # use on the border are considered inside the shape.
            is_in_cell = shape.contains(shape_point) or shape.exterior.contains(
                shape_point
            )
            # Check the sample point, but save the display point.
            if is_in_cell:
                points_in_pocket.append(display_point)
    return points_in_pocket


def get_heatmap_from_pocket_shapes(
    pocket_shapes, bin_start, bin_end, bin_size, progress=False
):
    points_in_pocket = sample_points_in_shapes(
        pocket_shapes,
        bin_start,
        bin_end,
        bin_size,
        progress,
    )
    total = len(pocket_shapes)
    heatmap, extent = heatmap_from_points(
        points_in_pocket,
        total,
        bin_start,
        bin_end,
        bin_size,
    )
    return heatmap, extent


def get_play_pocket(df_play_metrics, df_areas, df_plays):
    """
    Choose one frame per play and area method and get
    the pocket object for that frame.
    """
    # Find the frame X seconds before the pocket ends.
    frames_per_second = 10
    df = pd.DataFrame(df_play_metrics)
    df = df[df["window_type"] == "before_end"]
    df["pocket_frame"] = (frames_per_second * df["time_start"]).astype(int)

    # Restrict the left side to one row per play, then
    # explode it with the right to get one row per play
    # and area type.
    left_cols = [
        "gameId",
        "playId",
        "pocket_frame",
        "frame_start",
        "frame_end",
    ]
    df = df[left_cols].drop_duplicates()

    # Extract vertices from pocket object, if any.
    def get_vertices(pocket):
        return pocket.get("metadata", {}).get("vertices")

    pocket_cols = [
        "gameId",
        "playId",
        "frameId",
        "method",
        "pocket",
    ]
    df_vertices = pd.DataFrame(df_areas[pocket_cols])
    df_vertices["vertices"] = df_vertices["pocket"].apply(get_vertices)
    df_vertices.drop(columns=["pocket"], inplace=True)

    # Drop plays without a polygon-shaped pocket.
    df_vertices = df_vertices[df_vertices["vertices"].notna()]

    # Inner join to keep only plays that have a window before
    # the pocket ends (left side) AND have a polygon-shaped
    # pocket (right side).
    df_pocket = df.merge(
        df_vertices,
        left_on=["gameId", "playId", "pocket_frame"],
        right_on=["gameId", "playId", "frameId"],
        how="inner",
    )
    df_pocket.drop(columns=["pocket_frame"], inplace=True)

    # Left join to plays to get metadata for these plays.
    df_out = df_pocket.merge(
        df_plays,
        on=["gameId", "playId"],
        how="left",
    )

    return df_out.query("method == 'adaptive_pocket_area'")


def vertices_to_shape(vertices):
    return ShapelyPolygon(vertices)


def get_pocket_shapes_for_area(df_pocket, default_area):
    df_pocket_default = df_pocket[df_pocket["method"] == default_area]
    pocket_shapes = df_pocket_default["vertices"].apply(vertices_to_shape)
    return pocket_shapes
