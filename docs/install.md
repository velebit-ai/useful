# installation

You can find the module on [`pypi`](https://pypi.org/project/velebit-useful) and install it and **all** of the dependencies using

```sh
pip install velebit-useful[all]
```

Below is a list of all extras requirements provided by this package grouped by hierarchy

* all
  * config (`munch`)
  * resource-all
    * resource-downloader-all
      * resource-downloader-gs (`google-cloud-storage`)
      * resource-downloader-gsfs (`gcsfs`)
      * resource-downloader-s3 (`boto3`)
      * resource-downloader-s3fs (`s3fs`)
      * resource-downloader-ssh (`paramiko`)
      * resource-downloader-http (`requests`)
    * resource-parser-all
      * resource-parser-yaml (`ruamel.yaml`)
      * resource-parser-numpy (`numpy`)

Any combination of the extras above can be installed via

```sh
pip install velebit-useful[config,resource-downloader-s3,resource-parser-yaml]
```
