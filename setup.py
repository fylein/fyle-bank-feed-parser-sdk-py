from setuptools import setup, find_packages

from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='card_data_parsers',
    version='0.1.0',
    author='Siva Narayanan',
    author_email='siva@fyle.in',
    url='https://www.fylehq.com',
    license='MIT',
    description='Parsing bank feed data files',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(exclude=('tests',)),
    install_requires=[
        "pycountry >= 18.5.26"
    ],
    keywords=['fyle', 'api', 'python', 'sdk'],
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ]
)
