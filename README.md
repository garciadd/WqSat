wq_sat
=======

Service to monitor the water quality of the continental water bodies through satellite data

**Author/Mantainer:** [Daniel Garcia] (https://github.com/garciadd) (IFCA)

## Quickstart
Modify credentials.yml and regions.yml to define your credentials for Copernicus (sentinel) services and landsat.
Copernicus: [https://scihub.copernicus.eu/userguide/SelfRegistration](https://dataspace.copernicus.eu/)
Landsat: https://ers.cr.usgs.gov/

For regions, please add any region you want to explore adding the coordinates limits (N,E,S,W) in regions.yml

Whenver your config these files, reinstall the package to include your data.
```
python3 setup.py install
```
## Docker version
You can build the image from the Dockerfile:

```
docker build -t wq_sat:latest .
```
And then, running the Jupyter service:

```
docker run --name wq_sat -p 8888:8888 -dit wq_sat:latest
```
