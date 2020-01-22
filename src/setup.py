"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# To use a consistent encoding

# Always prefer setuptools over distutils
from setuptools import setup, find_packages

setup(
    name='primetrust',
    version='1.0.3',
    private=True,
    description='API for primetrust',
    author='Amit Assaraf',
    author_email='amit.assaraf@gmail.com',
    license='MIT',
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7'
    ],
    keywords='setuptools development',
    package_data={'': ['*.yml', '*.html']},
    include_package_data=True,
    packages=find_packages(exclude=['contrib', 'docs', 'tests'])
)
