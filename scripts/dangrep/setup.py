from setuptools import setup, find_packages

setup(
    name='projconfig',
    version='0.1',
    license='MIT License',
    long_description=open('README.md').read(),
    #url='https://github.com/dancps/',
    author='Danilo Calhes',
    packages=find_packages(),
    entry_points={'console_scripts': ['dangrep=dangrep.dangrep:main',],},
)