from setuptools import find_packages
from setuptools import setup


setup(
    name="ophiuchus",
    version="0.1.0",
    author="Bryan Wyatt",
    author_email="brwyatt@gmail.com",
    description=(""),
    license="LGPLv3",
    keywords="aws web website serverless lambda",
    url="https://github.com/brwyatt/Ophiuchus",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={"ophiuchus": ["templates/lambdas/*"]},
    python_requires="~=3.6",
    include_package_data=False,
    entry_points={
        "console_scripts": ["ophiuchus = ophiuchus.cli:main"],
        "ophiuchus_subcommands": [
            "runlocal = ophiuchus.cli.runlocal:Run",
            "build = ophiuchus.cli.build:Build",
        ],
    },
    install_requires=["boto3>=1.10.0,<1.11.0", "Jinja2>=2.10.0,<2.11.0"],
    tests_require=["aiohttp>=3.6.0,<3.7.0"],
)
