from setuptools import setup

setup(
    name="nflpocketarea2023",
    version="0.0.1",
    description="NFL Big Data Bowl 2023: Analyzing pocket area.",
    py_modules=["nflpocketarea2023"],
    package_dir={"nflpocketarea2023": "src"},
    author="Vinesh Kannan, Tabor Alemu, Alek Popovic",
    author_email="v@hawk.iit.edu",
    long_description="NFL Big Data Bowl 2023: Analyzing pocket area.",
    long_description_content_type="text/markdown",
    url="https://github.com/vingkan/nflbigdatabowl2023",
    include_package_data=True,
    classifiers=[],
    install_requires=[
        "dacite>=1.7.0",
        "matplotlib>=3.6.2",
        "numpy>=1.24.1",
        "pandas>=1.5.2",
        "prefect>=2.7.4",
        "seaborn>=0.12.2",
        "scipy>=1.9.3",
        "shapely>=2.0.0",
    ],
    keywords=[],
)
