# arxiu temporal pels meus tests en local

import os
import sys
import pytest

if __name__ == "__main__":
    # Canvi del directori de treball automaticament perque els JSON es trobin
    os.chdir("src/mls_code_generator")
    
    # Tests des d'aqui mitjancant codi, per evitar que la
    # carpeta "types" col-lapsi amb el sistema.
    sys.exit(pytest.main(["tests/"]))