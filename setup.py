import os

from setuptools import setup, find_packages


setup(
    name='ophiuchus',
    version='0.1.0',
    author='Bryan Wyatt',
    author_email='brwyatt@gmail.com',
    description=(''),
    license='LGPLv3',
    keywords='aws web website serverless lambda',
    url='https://github.com/brwyatt/Ophiuchus',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    package_data={},
    python_requires='~=3.6',
    include_package_data=False,
    entry_points={},
    install_requires=[
        'boto3==1.10.26',
    ]
)
