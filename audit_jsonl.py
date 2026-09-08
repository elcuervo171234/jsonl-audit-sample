"""Read-only JSON Lines audit. No third-party dependencies."""
import argparse
import decimal
import json
import sys

LIMIT = 1024 * 1024  # Includes the line terminator, if present.

def reject_constant(value):
    raise ValueError('nonstandard number')

def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate object key')
        result[key] = value
    return result

def audit(source, report, max_bytes=LIMIT):
    if max_bytes < 1:
        raise ValueError('max_bytes must be positive')
    lines = rejected = 0
    while chunk := source.readline(max_bytes + 1):
        lines += 1
        reason = None
        if len(chunk) > max_bytes:
            reason = 'line_too_large'
            while chunk and not chunk.endswith(b'\n'):
                chunk = source.readline(max_bytes + 1)
        else:
            try:
                text = chunk.decode('utf-8')
                json.loads(text, parse_constant=reject_constant,
                           parse_float=decimal.Decimal,
                           object_pairs_hook=unique_object)
            except UnicodeDecodeError:
                reason = 'invalid_utf8'
            except (ValueError, RecursionError, decimal.InvalidOperation):
                reason = 'invalid_or_unsupported_json'
        if reason:
            rejected += 1
            print(json.dumps({'line': lines, 'reason': reason}), file=report)
    return {'lines': lines, 'valid': lines - rejected, 'rejected': rejected}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', help='JSONL file to read; never modified')
    args = parser.parse_args()
    try:
        with open(args.input, 'rb') as source:
            result = audit(source, sys.stdout)
        print(json.dumps(result), file=sys.stderr)
    except OSError:
        print('Input/output failure; report may be incomplete.', file=sys.stderr)
        return 2
    return 1 if result['rejected'] else 0

if __name__ == '__main__':
    raise SystemExit(main())
