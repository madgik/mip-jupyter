from setuptools import setup, find_packages

setup(
    name="mip",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "pandas>=1.0.0",
        "numpy>=1.21.0",
        "scikit-learn>=1.0.0",
        "joblib>=1.0.0",
    ],
    author="Konstantinos Filippopolitis",
    description="Python client for the Platform Backend API",
)
