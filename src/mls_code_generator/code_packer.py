import shutil
class CodePacker():
    def __init__(self) -> None:
        pass

    def generatePackage(self, code, write_path, mls_path, out_name = "output.zip"):
        for module in code:
            module_code = code[module]
            module_write_path = write_path + str(module) + ".py"

            file = open(module_write_path, 'w')
            file.write(module_code)
            file.close()

        shutil.copytree(mls_path, write_path+'/mls')

            