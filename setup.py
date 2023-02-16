import setuptools

with open('requirements.txt') as f:
    reqs = f.read().splitlines()

setuptools.setup(
    setup_requires=reqs,
    pbr=True)