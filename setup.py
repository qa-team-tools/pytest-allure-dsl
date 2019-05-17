# -*- coding: utf-8 -*-

from setuptools import setup


setup(
    name='pytest-allure-dsl',
    version_format='{tag}',
    setup_requires=['setuptools-git-version'],
    description='pytest plugin to test case doc string dls instructions',
    author='Mikhail Trifonov',
    author_email='trifonov.net@gmail.com',
    url='https://github.com/trifonovmixail/pytest-allure-dsl',
    py_modules=['pytest_allure_dsl'],
    install_requires=[
        'pytest',
        'pytest-allure-adaptor==1.7.10',
        'PyYAML',
    ],
    keywords='py.test pytest allure dsl',
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Pytest',
        'Intended Audience :: Developers',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
        'Topic :: Utilities',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.0',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
)
