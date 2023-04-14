# Endpoint: `/GET_CHANNELS`
Example request:
```json
{ }
```

Example response:
```json
{
  "channels": {
    "release": "0.1.2",
    "nightly": "0.1.2+6"
  }
}
```

# Endpoint: `/GET_VERSION`
Example requests:
```json
{
  "channel" : "release"
}
```

```json
{
  "version_id": "1.2.3"
}
```

Example response:
```json
{
  "version_id": "1.2.3",
  "date": "2023-04-14 17:28:39",
  "archive_bytes": 64977,
  "archive_md5": "7efb4582d8bc95e0eac7e7625c9e57c4",
  "archive_url": "http://0.0.0.0/version_zips/1.2.3.zip",
  "files": {
    ".gitignore": {
      "md5": "9117c65ed9ff083256a86af10ab88d65",
      "archive_bytes": 246,
      "file_url": "http://0.0.0.0/hashed_files/9117c65ed9ff083256a86af10ab88d65.zip"
    }
  }
}
```
