""" CodePacker: Component that writes the code. """
import shutil
class CodePacker():
    """ CodePacker: Component that writes the code. """
    def __init__(self) -> None:
        pass

    def generate_package(self, code, write_path, mls_path):
        """
        Generates a package from the provided code and writes it to the specified path.
        
        Args:
            code (dict): A dictionary containing the code modules to be packaged.
            write_path (str): The path where the package will be written.
            mls_path (str): The path to the MLS library.
        
        Returns:
            None
        """
        for module in code:
            module_code = code[module]
            module_write_path = write_path + str(module) + ".py"

            file = open(module_write_path, 'w', encoding='utf-8')
            file.write(module_code)
            file.close()

        file = open(write_path + "__init__.py", 'w', encoding='utf-8')
        file.write("")
        file.close()

        shutil.copytree(mls_path, write_path+'/mls_lib')
