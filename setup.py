from setuptools import setup, find_packages

with open('requirements.txt') as f:
    reqs = f.read().splitlines()

setup(
    name='wq_sat',
    packages=find_packages(),
    version='0.1.0',
    description='Service to monitor the water quality of the continental water bodies and coastal water through satellite data',
    author='CSIC',
    license='MIT',
    setup_requires=reqs,
    pbr=True)
