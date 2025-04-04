from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().splitlines()

try:
    long_description = open("README.md").read()
except FileNotFoundError:
    long_description = ""

setup(
    name="search-engine",
    version="1.0.0",
    author="Vijay Shankar",
    author_email="vijayshankar@example.com",
    description="A search engine project",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/search-engine",
    packages=find_packages(),
    install_requires=install_requires,
    classifiers=[],
    python_requires=">=3.11",
)
