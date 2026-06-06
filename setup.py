#!/usr/bin/env python

from setuptools import setup

with open("README.md", "r") as readme_file:
    long_description = readme_file.read()

setup(
    name="relations-sql",
    version="0.6.7",
    package_dir = {'': 'lib'},
    py_modules = [
        'relations_sql',
        'relations_sql.sql',
        'relations_sql.expression',
        'relations_sql.criterion',
        'relations_sql.criteria',
        'relations_sql.clause',
        'relations_sql.query',
        'relations_sql.ddl',
        'relations_sql.column',
        'relations_sql.index',
        'relations_sql.table',
        'relations_sql.source'
    ],
    install_requires=[
        'overscore==0.1.1'
    ],
    url="https://github.com/relations-dil/python-relations-sql",
    author="Gaffer Fitch",
    author_email="relations@gaf3.com",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license_files=('LICENSE.txt',),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License"
    ]
)
