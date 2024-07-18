from copy import deepcopy

class DataFrame:
    def __init__(self, loader = None, path = None):
        """
        Initializes a new instance of the Dataset class.

        Parameters:
            loader (Loader, optional): The loader object used to load the data from the specified path. Defaults to None.
            path (str, optional): The path to the data file. Defaults to None.

        Returns:
            None
        """
        self.path = path
        if (loader == None):
            self.data = None
        else: 
            self.data = loader.load(path)
            
    def copy(self):
        """
        Returns a copy of the current dataset.

        Returns:
            Dataset: A copy of the current dataset.
        """
        return deepcopy(self)
    
    def getData(self):
        return self.data

    def setData(self, data):
        self.data = data
