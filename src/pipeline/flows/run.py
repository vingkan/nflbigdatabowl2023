import sys

sys.path.append("./")

from src.pipeline.flows.main import main_flow

if __name__ == "__main__":
    main_flow(max_weeks=3, max_games=3, max_plays=3)
