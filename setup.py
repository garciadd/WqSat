from setuptools import setup, find_packages

with open('requirements.txt') as f:
    reqs = f.read().splitlines()

setup(
    name='wqsat',
    packages=find_packages(),
    version='0.1.0',
    description='Service to monitor the water quality of the continental water bodies through satellite data.',
    author='CSIC',
    license='Apache License 2.0',
    install_requires=reqs,
    extras_require={
        'get': ['wqsat-get @ git+https://github.com/garciadd/WqSat_Get.git@main'],
        'format': ['wqsat-format @ file:///home/dani/github/WqSat_format/'],
        'sr': ['wqsat-sr @ file:///home/dani/github/WqSat_sr/'],
        'all': [
            'wqsat-get @ file:///home/dani/github/WqSat_Get/',
            'wqsat-format @ file:///home/dani/github/WqSat_format/',
            'wqsat-sr @ file:///home/dani/github/WqSat_sr/'
        ]
    })