from setuptools import setup, find_packages

with open("README.md") as f:
    readme = f.read()


setup(
    name="examtool",
    version="1.0.2",
    author="Rahul Arya",
    author_email="rahularya@berkeley.edu",
    long_description=readme,
    long_description_content_type="text/markdown",
    licence="MIT",
    packages=find_packages(include=["examtool.api", "examtool.cli"]),
    entry_points={"console_scripts": ["examtool=examtool.cli.__main__:cli"]},
    python_requires=">=3.6",
    install_requires=["cryptography"],
    extras_require={
        "admin": ["pytz", "requests", "pypandoc"],
        "cli": ["pikepdf", "pytz", "requests", "fpdf", "pypandoc"],
    },
)
