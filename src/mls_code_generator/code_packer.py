""" CodePacker: Component that writes the code. """
import os
import shutil
import yaml

class CodePacker():
    """ CodePacker: Component that writes the code. """
    def __init__(self) -> None:
        pass

    def generate_package(self, code, params, write_path, mls_path, services_mode: bool = False):
        """
        Generates a package from the provided code and writes it to the specified path.

        This function writes the Python modules and parameters to disk, and optionally 
        sets up the shared data volume folder if the services mode is enabled.

        Parameters:
            code (dict): A dictionary containing the generated code modules.
            params (dict): The parameters to be written into params.yaml.
            write_path (str): The path where the package will be written.
            mls_path (str): The path to the MLS library.
            services_mode (bool): Flag indicating if the output is for services.

        Returns:
            None
        """
        os.makedirs(write_path, exist_ok=True)

        if services_mode:
            data_dir = os.path.join(write_path, "data")
            os.makedirs(data_dir, exist_ok=True)

        if not services_mode:
            for module in code:
                if str(module).startswith("service_"):
                    continue

                module_code = code[module]
                module_write_path = os.path.join(write_path, f"{module}.py")

                with open(module_write_path, 'w', encoding='utf-8') as file:
                    file.write(module_code.replace("\t", "    "))

        params_file_path = os.path.join(write_path, "params.yaml")
        with open(params_file_path, 'w', encoding='utf-8') as file:
            yaml.dump(params, file)

        dest_mls = os.path.join(write_path, 'mls_lib')
        if os.path.exists(dest_mls):
            shutil.rmtree(dest_mls)
        shutil.copytree(mls_path, dest_mls)
