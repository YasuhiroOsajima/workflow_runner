"""
$ pip install -e .
"""

from setuptools import setup, find_packages

setup(
    name="workflow_runner",
    version='0.1.1',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
)
