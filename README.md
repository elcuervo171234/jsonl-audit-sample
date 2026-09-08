# JSON Lines audit sample

A small read-only Python command-line tool that reports rejected physical lines without printing their contents. This is a personal portfolio sample, not a production client case study.

## Run

No third-party dependencies. Tested with Python 3.14.6 on Linux.

```sh
python3 audit_jsonl.py input.jsonl
python3 -m unittest -v test_audit_jsonl.py
```

The source file is opened in binary read-only mode. Rejected lines are emitted as JSON objects to stdout with their physical line number and reason. A summary is emitted to stderr. Exit status is 0 when all lines pass, 1 when at least one line is rejected, and 2 for an input/output failure. An I/O failure may leave a partial report.

## Rules and limits

- UTF-8 only; each physical line must contain one JSON value.
- JSON scalars are permitted; blank lines, a UTF-8 BOM, duplicate object keys and nonstandard NaN/Infinity values are rejected.
- Physical lines are limited to 1 MiB, including the line terminator when present. Oversized lines are drained before continuing with the next record.
- Decimal parsing allows large finite decimal values without silently converting them to floating-point infinity.
- Validation does not modify the input and does not validate a business schema, repair data, deduplicate records or guarantee semantic correctness.
- This is not a sandbox for hostile data. The physical-line limit does not establish a universal CPU-time limit. Parser recursion limits can reject deeply nested JSON.

## Tests

The eight tests exercise scalars, CRLF and a missing final newline; continued processing after a malformed record; duplicate keys, BOM and nonstandard numbers; oversized lines including an unterminated final line; invalid UTF-8 and exact size boundaries; empty input and large finite numbers; and CLI exit codes, separate output streams and unchanged source bytes.

## Article

[One bad JSON line should not hide the next record](https://ko-fi.com/post/One-bad-JSON-line-should-not-hide-the-next-record-O8I126M9YF)

[Personal portfolio and contact](https://ko-fi.com/guanelfipuntocom)
