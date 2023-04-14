# Endpoint: `/GET_CHANNELS`
Example request:
```json
{ }
```

Example response:
```json
{
	"channels" : {
		"release" : "0.1.2",
		"nightly" : "0.1.2+6"
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
	"version_id" : "0.1.2"
}
```

Example response:
```json
{
	"version_id" : "0.1.2",
	"date" : "2023_04_13 21:51:34",
	"archive_url" : "https://...",
	"archive_bytes" : 1234,
	"archive_md5" : "(md5)",
	"files" : {
		"relative/path/to/file" : {
			"md5" : "(md5)",
			"bytes" : 1234
		}
	}
}
```
