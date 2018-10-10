# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='dep',
    version='0.1.0',
    description='Data Evaluation and Processing',
    long_description=readme,
    author='Josh Riley - KOA TEAM',
    author_email='jriley@keck.hawaii.edu',
    url='https://github.com/KeckObservatoryArchive/data-evaluation-and-processing',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)
