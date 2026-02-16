from setuptools import setup, find_packages

setup(
    name="portal_backend_client",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "pandas>=1.0.0",
    ],
    author="Konstantinos Filippopolitis",
    description="Python client for the Portal Backend API",
)
