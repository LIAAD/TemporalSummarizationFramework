#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

requirements = []
with open('requirements.txt') as req_file:
    requirements = req_file.readlines()

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest', ]

setup(
    author="Arian Pasquali",
    author_email='arrp@inesctec.pt',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    description="Retrive articles from Arquivo.pt web archive and produce a temporal summarization.",
    entry_points={
        'console_scripts': [
            'contamehistorias=contamehistorias.cli_arquivopt:main',

            'contamehistorias_arquivopt=contamehistorias.cli_arquivopt:main',
            'contamehistorias_signal=contamehistorias.cli_signal:main',
            'contamehistorias_mediacloud=contamehistorias.cli_mediacloud:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme,
    package_data={'contamehistorias': ['domains.txt']},
    include_package_data=True,
    keywords='contamehistorias',
    name='contamehistorias',
    packages=find_packages(),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/LIAAD/TemporalSummarizationFramework',
    version='0.1.0',
    zip_safe=False,
)
