import pandas as pd

def load(path):
    """
    Load the CSV data from the specified path.

    Args:
        path (str): The path to the CSV file.

    Returns:
        pandas.DataFrame: The loaded CSV data.

    Raises:
        FileNotFoundError: If the specified path does not exist.

    Example:
        >>> CSVLoader.load('data.csv')
        pandas.DataFrame
    """
    return pd.read_csv(path)