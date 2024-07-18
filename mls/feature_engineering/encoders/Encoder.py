class Encoder():
    def __init__(self, encoder) -> None:
        """
        Initializes the class instance with a given encoder.

        Args:
            encoder: The encoder object to be used.

        Returns:
            None
        """
        self.encoder = encoder

    def fit_transform(self, data):
        """
        Fits the encoder to the data and performs a transform operation on the data.

        Parameters:
            data (numpy.ndarray): The input data to be encoded.

        Returns:
            None
        """
        data.data = self.encoder.fit_transform(data.data)

    def transform(self, data):
        """
        Transforms the input data using the encoder object.

        Parameters:
            data (object): The input data to be transformed.

        Returns:
            None
        """
        data.data = self.encoder.transform(data.data)
