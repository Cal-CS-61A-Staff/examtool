from setuptools import setup, find_packages

setup(
    name="examtool",
    version="0.1.8",
    author="Rahul Arya",
    author_email="rahularya@berkeley.edu",
    licence="MIT",
    packages=find_packages(include=["examtool.api", "examtool.cli"]),
    entry_points={
        "console_scripts": [
            "examtool=examtool.cli.__main__:cli",
        ]
    }, install_requires=['click', 'pikepdf', 'pytz', 'requests', 'fpdf', 'cryptography']
)
