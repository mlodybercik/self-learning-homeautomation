from setuptools import setup, find_packages

setup(
    name="automation",
    version="0.1.0",    
    description="Automation",
    author="Przemysław Barcicki",
    install_requires=["appdaemon", "numpy", "tensorflow", "hassapi"],
    package_dir = {"": "src"},
    package_data = {"": ["logging.json"]},
    packages = find_packages(where="src"),
    classifiers=[
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
)
