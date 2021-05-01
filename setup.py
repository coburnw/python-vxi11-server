from setuptools import setup

import os.path

setup(
    name = 'python-vxi11-server',
    description = '''Python VXI-11 driver for controlling instruments over Ethernet
and server for creating instruments''',
    version = '1.0.0',
    long_description = '''This Python package supports the VXI-11 Ethernet
instrument control protocol for controlling and creating VXI11 and LXI compatible instruments.''',
    download_url = 'https://github.com/ulda/python-vxi11-server',
    keywords = 'VXI LXI measurement instrument client server',
    license = 'MIT License',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3'
        ],
    packages = ['vxi11_server'],
    python_requires=">=3.5",
)

