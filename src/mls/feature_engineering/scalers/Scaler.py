import numpy as np

class Scaler:
    def __init__(self, scaler) -> None:
        """
        Initializes the class instance with a given scaler and column.

        Args:
            scaler (object): The scaler object to be used for scaling the data.
            columns (list): A list containing the column name(s) to be scaled.

        Returns:
            None
        """
        super().__init__()
        self.scaler = scaler
        self.column = None
        pass

    def fit_transform(self, data, column):
        """
        Fits the scaler to the data and performs a transform operation on the specified column.

        Parameters:
            data (numpy.ndarray): The input data to be scaled.

        Returns:
            None
        """
        self.column = column
        print(np.array(data.data[self.column]))
        data.data[self.column] = self.scaler.fit_transform(np.array(data.data[self.column]).reshape(-1,1))

    def transform(self, data):
        """
        Transforms the specified column of the input data using the scaler object.

        Parameters:
            data (object): The input data to be transformed.

        Returns:
            None

        """
        data.data[self.column] = self.scaler.transform(np.array(data.data[self.column]).reshape(-1,1))