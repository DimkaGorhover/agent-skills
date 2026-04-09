# VRL Function Reference

Comprehensive reference for all VRL functions. Functions marked with **(F)** are fallible and require error handling (`!`, `??`, or `, err =`).

## Array Functions

| Function     | Signature                                | Description                           |
| ------------ | ---------------------------------------- | ------------------------------------- |
| `append`     | `append(value, items)`                   | Appends items to array                |
| `chunks`     | `chunks(value, chunk_size)`              | Splits array into chunks              |
| `filter`     | `filter(value) -> \|index, value\| { }`  | Filters array with closure **(F)**    |
| `flatten`    | `flatten(value)`                         | Flattens nested arrays one level      |
| `for_each`   | `for_each(value) -> \|index, item\| { }` | Iterates array or object with closure |
| `includes`   | `includes(value, item)`                  | Checks if array contains item         |
| `length`     | `length(value)`                          | Returns array/string/object length    |
| `map_values` | `map_values(value) -> \|value\| { }`     | Transforms values with closure        |
| `pop`        | `pop(value)`                             | Removes and returns last element      |
| `push`       | `push(value, item)`                      | Appends single item to array          |
| `reverse`    | `reverse(value)`                         | Reverses array order                  |
| `unique`     | `unique(value)`                          | Returns array with duplicates removed |
| `zip`        | `zip(array1, array2)`                    | Zips two arrays into array of pairs   |

## Codec Functions (Encode/Decode)

| Function                              | Description                            |
| ------------------------------------- | -------------------------------------- |
| `decode_base16` / `encode_base16`     | Hex encoding **(F decode)**            |
| `decode_base64` / `encode_base64`     | Base64 encoding **(F decode)**         |
| `decode_charset` / `encode_charset`   | Character set conversion **(F)**       |
| `decode_gzip` / `encode_gzip`         | Gzip compression **(F decode)**        |
| `decode_lz4` / `encode_lz4`           | LZ4 compression **(F decode)**         |
| `decode_mime_q`                       | MIME quoted-printable decoding **(F)** |
| `decode_percent` / `encode_percent`   | URL percent encoding **(F decode)**    |
| `decode_punycode` / `encode_punycode` | Punycode (IDN) **(F decode)**          |
| `decode_snappy` / `encode_snappy`     | Snappy compression **(F decode)**      |
| `decode_zlib` / `encode_zlib`         | Zlib compression **(F decode)**        |
| `decode_zstd` / `encode_zstd`         | Zstandard compression **(F decode)**   |
| `encode_csv`                          | Encode value as CSV string             |
| `encode_json`                         | Encode value as JSON string            |
| `encode_key_value`                    | Encode object as key=value string      |
| `encode_logfmt`                       | Encode object as logfmt string         |
| `encode_proto`                        | Encode to protobuf **(F)**             |
| `decode_proto`                        | Decode from protobuf **(F)**           |

## Coerce Functions (Type Conversion)

All coerce functions are fallible **(F)**.

| Function            | Converts To     | Example                                              |
| ------------------- | --------------- | ---------------------------------------------------- |
| `to_bool`           | Boolean         | `to_bool!("true")` → `true`                          |
| `to_float`          | Float           | `to_float!("3.14")` → `3.14`                         |
| `to_int`            | Integer         | `to_int!("42")` → `42`                               |
| `to_regex`          | Regex           | `to_regex!("\\d+")` → regex                          |
| `to_string`         | String          | `to_string(42)` → `"42"` (infallible for most types) |
| `to_timestamp`      | Timestamp       | `to_timestamp!("2021-01-01")`                        |
| `to_unix_timestamp` | Integer (epoch) | `to_unix_timestamp(now())`                           |

## Convert Functions

| Function                  | Description                           |
| ------------------------- | ------------------------------------- |
| `to_syslog_facility`      | Convert facility code to name **(F)** |
| `to_syslog_facility_code` | Convert facility name to code **(F)** |
| `to_syslog_level`         | Convert level code to name **(F)**    |
| `to_syslog_severity`      | Convert severity code to name **(F)** |

## Crypto Functions

| Function  | Description                                |
| --------- | ------------------------------------------ |
| `decrypt` | AES decryption (AES-256-CFB, etc.) **(F)** |
| `encrypt` | AES encryption **(F)**                     |
| `hmac`    | HMAC signature (SHA-256, etc.)             |
| `md5`     | MD5 hash                                   |
| `sha1`    | SHA-1 hash                                 |
| `sha2`    | SHA-2 hash (224, 256, 384, 512)            |
| `sha3`    | SHA-3 hash                                 |

Example:

```coffee
.hash = sha2(.message, variant: "SHA-256")
.hmac = hmac(.message, key: "secret", algorithm: "SHA-256")
```

## Debug Functions

| Function | Description                                       |
| -------- | ------------------------------------------------- |
| `log`    | Log message at runtime (debug, info, warn, error) |

```coffee
log("Processing event", level: "info")
log(.message, level: "debug")
log({"event": ., "step": "parsed"}, level: "debug")  # structured
```

## Diagnostics Functions

| Function    | Description                         |
| ----------- | ----------------------------------- |
| `assert`    | Assert condition is true **(F)**    |
| `assert_eq` | Assert two values are equal **(F)** |
| `abort`     | Abort processing, drop event        |

```coffee
assert!(.level != null, message: "level required")
assert_eq!(.environment, "production")
abort   # drops the current event
```

## Enrichment Functions

| Function                        | Description                            |
| ------------------------------- | -------------------------------------- |
| `find_enrichment_table_records` | Find multiple matching records **(F)** |
| `get_enrichment_table_record`   | Get single matching record **(F)**     |

```coffee
# Requires enrichment_tables config in Vector
row = get_enrichment_table_record!("geoip", {"ip": .src_ip})
.city = row.city
```

## Enumerate Functions

| Function       | Description                                |
| -------------- | ------------------------------------------ |
| `compact`      | Remove null/empty values from object/array |
| `contains`     | Check if string contains substring         |
| `contains_all` | Check if string contains all substrings    |
| `includes`     | Check if array contains item               |
| `keys`         | Get object keys as array                   |
| `length`       | Get length of string/array/object          |
| `match`        | Check if string matches regex              |
| `match_any`    | Check if string matches any regex in array |
| `match_array`  | Check if any array element matches regex   |
| `values`       | Get object values as array                 |
| `tally`        | Count occurrences of each value in array   |
| `tally_value`  | Count occurrences of a specific value      |

## Event Functions

| Function | Description                             |
| -------- | --------------------------------------- |
| `del`    | Delete field, returns deleted value     |
| `exists` | Check if field exists                   |
| `get`    | Get field value by path **(F)**         |
| `remove` | Remove field by path array              |
| `set`    | Set field value by path array           |
| `unnest` | Unnest array field into multiple events |

```coffee
del(.debug_info)                         # delete field
.hostname = del(.host)                   # move/rename
exists(.optional_field)                  # returns bool
set!(., ["nested", "path"], "value")     # dynamic path
remove!(., ["nested", "path"])           # dynamic delete
```

## Hash Functions

| Function  | Description                         |
| --------- | ----------------------------------- |
| `crc`     | CRC checksum (CRC-32, etc.)         |
| `md5`     | MD5 hash (also in crypto)           |
| `redact`  | Redact sensitive data with patterns |
| `seahash` | SeaHash                             |
| `sha1`    | SHA-1 hash                          |
| `sha2`    | SHA-2 family                        |
| `sha3`    | SHA-3 family                        |
| `xxhash`  | xxHash (fast non-crypto hash)       |

## IP Functions

| Function           | Description                                    |
| ------------------ | ---------------------------------------------- |
| `ip_aton`          | IP address to integer **(F)**                  |
| `ip_cidr_contains` | Check IP in CIDR range **(F)**                 |
| `ip_ntoa`          | Integer to IP address **(F)**                  |
| `ip_ntop`          | Binary to IP address string **(F)**            |
| `ip_pton`          | IP address string to binary **(F)**            |
| `ip_subnet`        | Extract subnet from IP **(F)**                 |
| `ip_to_ipv6`       | Convert IPv4 to IPv6 **(F)**                   |
| `ipv6_to_ipv4`     | Convert IPv6-mapped to IPv4 **(F)**            |
| `is_ipv4`          | Check if string is valid IPv4                  |
| `is_ipv6`          | Check if string is valid IPv6                  |
| `encrypt_ip`       | Encrypt IP address (format-preserving) **(F)** |
| `decrypt_ip`       | Decrypt IP address (format-preserving) **(F)** |

```coffee
if ip_cidr_contains!(.src_ip, "10.0.0.0/8") {
    .network = "internal"
}
.subnet = ip_subnet!(.src_ip, "24")  # /24 subnet
```

## Number Functions

| Function        | Description                          |
| --------------- | ------------------------------------ |
| `abs`           | Absolute value                       |
| `ceil`          | Round up                             |
| `floor`         | Round down                           |
| `format_int`    | Format integer as string (with base) |
| `format_number` | Format with locale/precision **(F)** |
| `max`           | Maximum of values                    |
| `min`           | Minimum of values                    |
| `mod`           | Modulo                               |
| `round`         | Round to precision                   |

## Object Functions

| Function              | Description                                           |
| --------------------- | ----------------------------------------------------- |
| `flatten`             | Flatten nested object (dot notation keys)             |
| `from_entries`        | Convert array of key-value pairs to object            |
| `keys`                | Get keys as array                                     |
| `map_keys`            | Transform object keys with closure                    |
| `map_values`          | Transform object values with closure                  |
| `match_datadog_query` | Match an object against a Datadog Search Syntax query |
| `merge`               | Merge two objects (second wins conflicts)             |
| `object`              | Assert/convert to object **(F)**                      |
| `object_from_array`   | Create object from parallel key/value arrays          |
| `to_entries`          | Convert object to array of key-value pairs            |
| `unflatten`           | Unflatten dot-notation keys to nested object          |
| `values`              | Get values as array                                   |

```coffee
. |= object!(parse_json!(.message))     # merge parsed into event
merged = merge(defaults, overrides)       # overrides win
flat = flatten(.)                         # {"a.b.c": 1}
nested = unflatten(flat)                  # {"a": {"b": {"c": 1}}}

# Datadog Search Syntax matching
match_datadog_query({"message": "contains this and that"}, "this OR that")  # true
match_datadog_query({"message": "only this"}, "this AND that")              # false
match_datadog_query({"name": "foobar"}, "@name:foo*")                       # true (attribute wildcard)
match_datadog_query({"tags": ["a:x", "b:y"]}, s'b:["x" TO "z"]')           # true (tag range)
```

## Parse Functions

The most commonly used category. All are fallible **(F)**.

| Function                                        | Parses                   | Example Input                    |
| ----------------------------------------------- | ------------------------ | -------------------------------- |
| `parse_apache_log`                              | Apache access/error logs | `GET /index.html HTTP/1.1...`    |
| `parse_aws_alb_log`                             | AWS ALB access logs      | ALB log line                     |
| `parse_aws_cloudwatch_log_subscription_message` | CloudWatch subscription  | CloudWatch JSON                  |
| `parse_aws_vpc_flow_log`                        | VPC Flow Logs            | VPC flow record                  |
| `parse_bytes`                                   | Byte size string         | `"1.5 KiB"`, `"100MB"`           |
| `parse_cbor`                                    | CBOR binary format       | CBOR bytes                       |
| `parse_cef`                                     | Common Event Format      | `CEF:0\|...`                     |
| `parse_common_log`                              | Common Log Format        | NCSA common log                  |
| `parse_csv`                                     | CSV string               | `"a,b,c"`                        |
| `parse_duration`                                | Duration string          | `"1h30m"`                        |
| `parse_etld`                                    | Effective TLD            | `"www.example.co.uk"`            |
| `parse_float`                                   | Float from string        | `"3.14"`                         |
| `parse_glog`                                    | Google glog format       | glog line                        |
| `parse_grok`                                    | Grok patterns            | Custom pattern                   |
| `parse_groks`                                   | Multiple grok patterns   | Array of patterns                |
| `parse_influxdb`                                | InfluxDB line protocol   | InfluxDB line                    |
| `parse_int`                                     | Integer from string      | `"42"`, `"0xFF"`                 |
| `parse_json`                                    | JSON string              | `'{"key": "val"}'`               |
| `parse_key_value`                               | Key=value (flexible)     | `"key1=val1 key2=val2"`          |
| `parse_klog`                                    | Kubernetes klog          | klog line                        |
| `parse_linux_authorization`                     | Linux auth logs          | auth.log line                    |
| `parse_logfmt`                                  | logfmt (strict)          | `"key=val ts=123"`               |
| `parse_nginx_log`                               | Nginx access/error       | nginx log line                   |
| `parse_proto`                                   | Protocol Buffers         | protobuf bytes                   |
| `parse_query_string`                            | URL query string         | `"?a=1&b=2"`                     |
| `parse_regex`                                   | Regex with captures      | Named groups `(?P<name>...)`     |
| `parse_regex_all`                               | All regex matches        | All named captures               |
| `parse_ruby_hash`                               | Ruby hash syntax         | `'{:key => "val"}'`              |
| `parse_syslog`                                  | Syslog (RFC 5424/3164)   | syslog line                      |
| `parse_timestamp`                               | Timestamp string         | Custom format                    |
| `parse_tokens`                                  | Space-delimited tokens   | `"val1 val2 val3"`               |
| `parse_url`                                     | URL components           | `"https://example.com/path?q=1"` |
| `parse_user_agent`                              | User-Agent string        | Browser UA string                |
| `parse_xml`                                     | XML to object            | XML string                       |
| `parse_yaml`                                    | YAML to object           | YAML string                      |

### Key Parse Examples

```coffee
# JSON
. |= object!(parse_json!(.message))

# Syslog
. = parse_syslog!(.message)

# Key-Value / logfmt
. = parse_key_value!(.message)

# Regex with named captures
. |= parse_regex!(.message, r'^(?P<ts>\S+) (?P<level>\w+) (?P<msg>.*)$')

# Timestamp
.timestamp = parse_timestamp!(.timestamp, format: "%Y-%m-%dT%H:%M:%S%.fZ")

# Grok
. = parse_grok!(.message, "%{COMMONAPACHELOG}")

# Multiple strategies with fallback
parsed = parse_syslog(.message) ??
         parse_json(.message) ??
         parse_key_value(.message) ?? {}
. = merge(., parsed)
```

## Path Functions

| Function     | Description                     |
| ------------ | ------------------------------- |
| `basename`   | Extract filename from path      |
| `dirname`    | Extract directory from path     |
| `exists`     | Check if path exists            |
| `del`        | Delete path, return value       |
| `get`        | Get value at path **(F)**       |
| `set`        | Set value at path **(F)**       |
| `remove`     | Remove value at path **(F)**    |
| `split_path` | Split file path into components |

## Random Functions

| Function       | Description                     |
| -------------- | ------------------------------- |
| `random_bool`  | Random boolean                  |
| `random_bytes` | Random byte string **(F)**      |
| `random_float` | Random float in range           |
| `random_int`   | Random integer in range         |
| `uuid_v4`      | Generate UUID v4                |
| `uuid_v7`      | Generate UUID v7 (time-ordered) |

```coffee
.request_id = uuid_v4()
.sample = random_float(0.0, 1.0)
```

## String Functions

| Function                  | Description                         |
| ------------------------- | ----------------------------------- |
| `camelcase`               | Convert to camelCase                |
| `capitalize`              | Capitalize first letter             |
| `contains`                | Check substring presence            |
| `downcase`                | Convert to lowercase                |
| `ends_with`               | Check string suffix                 |
| `find`                    | Find index of substring/regex       |
| `join`                    | Join array into string              |
| `kebabcase`               | Convert to kebab-case               |
| `match`                   | Match regex against string          |
| `match_any`               | Match any regex in array            |
| `pascalcase`              | Convert to PascalCase               |
| `replace`                 | Replace substring/regex             |
| `replace_with`            | Replace with closure                |
| `screamingsnakecase`      | Convert to SCREAMING_SNAKE_CASE     |
| `sieve`                   | Filter string characters by pattern |
| `slice`                   | Extract substring by index          |
| `snakecase`               | Convert to snake_case               |
| `split`                   | Split string by delimiter           |
| `starts_with`             | Check string prefix                 |
| `strip_ansi_escape_codes` | Remove ANSI codes                   |
| `strip_whitespace`        | Trim whitespace                     |
| `strlen`                  | String length in bytes              |
| `truncate`                | Truncate to length                  |
| `upcase`                  | Convert to uppercase                |

```coffee
.message = downcase!(.message)
.parts = split(.message, " ")
.clean = strip_whitespace!(.raw)
.masked = replace(.ssn, r'\d{3}-\d{2}', "XXX-XX")
if starts_with(.path, "/api/") { .type = "api" }
.field_name = snakecase(.rawFieldName)
```

## System Functions

| Function            | Description                      |
| ------------------- | -------------------------------- |
| `get_env_var`       | Get environment variable **(F)** |
| `get_hostname`      | Get host's hostname              |
| `get_timezone_name` | Get configured timezone name     |
| `now`               | Current timestamp                |

```coffee
.processed_at = now()
.host = get_hostname()
.api_key = get_env_var!("API_KEY")
.tz = get_timezone_name()
```

## Timestamp Functions

| Function              | Description                 |
| --------------------- | --------------------------- |
| `format_timestamp`    | Timestamp to string         |
| `from_unix_timestamp` | Unix epoch to timestamp     |
| `now`                 | Current timestamp           |
| `parse_timestamp`     | String to timestamp **(F)** |
| `to_unix_timestamp`   | Timestamp to epoch integer  |

```coffee
.ts = parse_timestamp!(.raw_ts, format: "%Y-%m-%d %H:%M:%S")
.formatted = format_timestamp!(.ts, format: "%+")  # RFC 3339
.epoch = to_unix_timestamp(.ts)
.epoch_ms = to_unix_timestamp(.ts, unit: "milliseconds")
.ts = from_unix_timestamp!(1609459200)
```

## Type Functions

| Function               | Description                         |
| ---------------------- | ----------------------------------- |
| `array`                | Assert value is array **(F)**       |
| `bool`                 | Assert value is boolean **(F)**     |
| `float`                | Assert value is float **(F)**       |
| `int`                  | Assert value is integer **(F)**     |
| `is_array`             | Check if array                      |
| `is_boolean`           | Check if boolean                    |
| `is_empty`             | Check if empty string/array/object  |
| `is_float`             | Check if float                      |
| `is_integer`           | Check if integer                    |
| `is_json`              | Check if valid JSON string          |
| `is_null`              | Check if null                       |
| `is_nullish`           | Check if null, empty string, or `-` |
| `is_object`            | Check if object                     |
| `is_regex`             | Check if regex                      |
| `is_string`            | Check if string                     |
| `is_timestamp`         | Check if timestamp                  |
| `kind`                 | Get type name as string             |
| `object`               | Assert value is object **(F)**      |
| `string`               | Assert value is string **(F)**      |
| `tag_types_externally` | Add type metadata to values         |
| `timestamp`            | Assert value is timestamp **(F)**   |
| `type_def`             | Get type definition                 |

```coffee
if is_string(.value) {
    .value = parse_json!(.value)
} else if is_null(.value) {
    .value = {}
}

# kind returns: "string", "integer", "float", "boolean", "array", "object", "timestamp", "regex", "null"
.value_type = kind(.value)
```

## Network Functions

| Function       | Description                            |
| -------------- | -------------------------------------- |
| `community_id` | Compute Community ID flow hash **(F)** |
| `dns_lookup`   | DNS lookup **(F)**                     |
| `reverse_dns`  | Reverse DNS lookup **(F)**             |
| `http_request` | Make HTTP request **(F)**              |
| `haversine`    | Calculate distance between coordinates |

### `http_request` — Full Signature

```
http_request(
  url: string,
  method: string = "get",       # GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
  headers: object = {},         # HTTP headers to include
  body: string = "",            # request body content
  http_proxy: string,           # optional HTTP proxy URL
  https_proxy: string,          # optional HTTPS proxy URL
  redact_headers: boolean = true  # redact sensitive header values in error messages
) -> string  (F)
```

> **Note**: `http_request` is synchronous/blocking and not recommended for performance-critical or
> high-frequency workflows due to potential network-related delays.
>
> **Not supported in WASM** — aborts at runtime.

```coffee
# GET request, parse JSON response
. = parse_json!(http_request!("https://api.example.com/data"))

# POST with body and auth header
response = http_request!(
    "https://api.example.com/ingest",
    method: "post",
    headers: {"Authorization": "Bearer " + get_env_var!("API_TOKEN"), "Content-Type": "application/json"},
    body: encode_json(.)
)

# With proxy
result = http_request!("https://example.com", http_proxy: "http://proxy:8080")
```

## Validation Functions

| Function               | Description                                |
| ---------------------- | ------------------------------------------ |
| `validate_json_schema` | Validate value against JSON Schema **(F)** |

## Entropy Functions

| Function          | Description                         |
| ----------------- | ----------------------------------- |
| `shannon_entropy` | Calculate Shannon entropy of string |

## UUID Functions

| Function                | Description                         |
| ----------------------- | ----------------------------------- |
| `uuid_v4`               | Generate random UUID v4             |
| `uuid_v7`               | Generate time-ordered UUID v7       |
| `uuid_from_friendly_id` | Convert friendly ID to UUID **(F)** |

## Redact Function (Data Privacy)

```coffee
# Redact patterns
.message = redact(.message, filters: ["pattern"])

# Redact with custom replacer
.email = redact(.email, filters: [r'\S+@\S+'], redactor: {"type": "text", "replacement": "[REDACTED]"})

# Redact known PII types
.message = redact(.message, filters: ["us_social_security_number"])
```

## Function Call Conventions

### Named Arguments

```coffee
parse_timestamp!(.ts, format: "%Y-%m-%d")
split(.msg, pattern: ",", limit: 3)
log("debug", level: "info")
```

### Closures

Some functions accept closures for transformation:

```coffee
filter(.tags) -> |_index, value| { value != "debug" }
map_values(.headers) -> |value| { downcase!(value) }
for_each(.items) -> |index, item| { log(item) }
```

### Chaining Pattern

VRL doesn't have method chaining — use variable assignment:

```coffee
# Step-by-step transformation
msg = downcase!(.message)
msg = replace(msg, "error", "ERROR")
msg = strip_whitespace!(msg)
.message = msg
```
