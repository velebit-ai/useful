# useful-resource

The purpose of function `useful.resource.load` is to provide unified access and parsing for resources on various locations. The usage is extremely simple:

```python
import useful.resource

config = useful.resource.load('s3://bucket/config.yaml')
```

We achieve this unified access in multiple stages:

## 1. Scheme and format extraction

The only information we must have before we start is an URI for an object we want to access. Using URI `<scheme>://<string>.<extension>` we can easily extract scheme/protocol and format/extension.

## 2. Downloading the resource

In this step, depending on the scheme, we provide a `downloader` function that returns a file-like object and allows us to read data byte by byte, in the same way as built-in function `open()` does for local files. Currently we support multiple schemas

* `file://` - local storage - using built-in `open()` (on-demand)
* `<no scheme>` - local storage - using built-in `open()` (on-demand)
* `http://` - HTTP resource - in-memory download beforehand
* `https://` - HTTPS resource - in-memory download beforehand
* `ssh://` - SSH/SFTP - save the whole object in-memory beforehand
* `scp://` - SSH/SFTP - save the whole object in-memory beforehand
* `sftp://` - SSH/SFTP - save the whole object in-memory beforehand
* `s3://` - AWS S3 storage - save the whole object in-memory beforehand
* `s3fs://` - AWS S3 storage - read the object on-demand
* `gs://` - Google Cloud Storage - save the whole object in-memory beforehand
* `gsfs://` - Google Cloud Storage - read the object on-demand

but more can be easily added by using `useful.resource.downloaders.add_downloader` function.

## 3. Parsing the actual bytes

From step (2) we have a file-like object and now we want to parse the data inside. In the step (1) we extracted the format/extension and now we can use a `parser` function to actually parse the data. At the moment we only support:

* `.json` - JSON format
* `.yaml` - YAML format
* `.csv` - CSV format
* `.text` - plain text format
* `.yml` - YAML format
* `.pkl` - Python pickle format
* `.pickle` - Python pickle format
* `<anything else>` - raw binary data

but more can be easily added by using `useful.resource.parsers.add_parser` function.

## 4. [Optional] hook

`hook` is an optional argument for the function `useful.resource.load`. It is a `callable` that accepts the output from the step (3) and runs additional modification and/or creation of objects instances. For example, we could simply run

```python
model = useful.resource.load('s3://bucket/weights.json', hook=Model)
```

instead of running

```python
weights = useful.resource.load('s3://bucket/weights.json')
model = Model(weights)
```

***
