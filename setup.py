from setuptools import Extension, setup
from Cython.Build import cythonize
import numpy as np

extensions = [
    Extension(
        name='gaussel',
        sources=['gaussel.pyx'],
        include_dirs=[np.get_include()],
    ),
]

setup(
    ext_modules=cythonize(extensions, language_level='3'),
    zip_safe=False,
)
