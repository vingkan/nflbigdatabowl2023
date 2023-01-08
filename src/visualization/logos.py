import time
from io import BytesIO
from typing import Any, Dict

import pandas as pd
import requests
from PIL import Image

TEAM_LOGOS_URL = "https://raw.githubusercontent.com/statsbylopez/BlogPosts/master/nfl_teamlogos.csv"


# Should be Dict[str, Image] but the type hint is tricky.
LogoMap = Dict[str, Any]


def get_team_logos(thumbnail_size: int = 32) -> LogoMap:
    """Gets NFL team logos from the URL and resizes them to icons."""
    dim = (thumbnail_size, thumbnail_size)
    df_logos = pd.read_csv(TEAM_LOGOS_URL)
    logo_tuples = df_logos[["team_code", "url"]].itertuples(index=False)
    team_logos: LogoMap = {}
    # Create an ID to identify these requests, with one header per batch.
    user_agent = f"nflpocketarea2023-{int(time.time())}"
    headers = {"User-Agent": user_agent}
    for team, url in logo_tuples:
        time.sleep(0.1)
        logo_response = requests.get(url, headers=headers)
        image_source = BytesIO(logo_response.content)
        image = Image.open(image_source)
        image.thumbnail(dim, Image.Resampling.LANCZOS)
        team_logos[team] = image
    return team_logos
