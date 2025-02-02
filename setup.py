from setuptools import find_packages, setup

setup(
    name='py_epos',
    packages=find_packages(include=['py_epos']),
    version='0.1.8',
    description='python library for Epson EPOS over TCP/IP',
    author='Pascal Pieper',
    author_email='Accounts@pascalpieper.de',
    install_requires=['pillow'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest==4.4.1'],
    test_suite='tests',
    entry_points={
        'console_scripts': [
            'eposprint = py_epos:printImage',
        ]
    },
)