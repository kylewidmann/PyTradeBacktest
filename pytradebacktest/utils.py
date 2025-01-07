import pandas as pd


def load_csv(path, parse_dates: list[str] = []) -> pd.DataFrame:
    with open(path) as fh:
        data = pd.read_csv(fh, parse_dates=parse_dates)

    return data
