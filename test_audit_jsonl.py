import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from audit_jsonl import audit

class AuditTests(unittest.TestCase):
    def check_audit(self, data, expected, errors, limit=1024):
        output = io.StringIO()
        self.assertEqual(audit(io.BytesIO(data), output, limit), expected)
        self.assertEqual([json.loads(line) for line in output.getvalue().splitlines()], errors)

    def test_values_crlf_and_no_final_newline(self):
        self.check_audit('{"city":"Santo Domingo"}\r\nnull\n[1,2]\n"café"'.encode(),
                         {'lines':4,'valid':4,'rejected':0}, [])

    def test_invalid_line_does_not_hide_later_valid_line(self):
        self.check_audit(b'{broken}\n{"ok":true}\n',
                         {'lines':2,'valid':1,'rejected':1},
                         [{'line':1,'reason':'invalid_or_unsupported_json'}])

    def test_nonstandard_values_duplicate_keys_and_bom(self):
        data = b'NaN\nInfinity\n{"x":1,"x":2}\n\xef\xbb\xbf{}\n\n'
        self.check_audit(data, {'lines':5,'valid':0,'rejected':5},
                         [{'line':n,'reason':'invalid_or_unsupported_json'} for n in range(1,6)])

    def test_oversize_is_one_line_and_next_line_survives(self):
        self.check_audit(b'"' + b'a'*50 + b'"\n{}\n',
                         {'lines':2,'valid':1,'rejected':1},
                         [{'line':1,'reason':'line_too_large'}], limit=8)

    def test_oversize_final_line_without_terminator(self):
        self.check_audit(b'x'*24, {'lines':1,'valid':0,'rejected':1},
                         [{'line':1,'reason':'line_too_large'}], limit=8)

    def test_utf8_failure_and_byte_boundary(self):
        self.check_audit(b'"\xff"\n{}\n', {'lines':2,'valid':1,'rejected':1},
                         [{'line':1,'reason':'invalid_utf8'}], limit=4)
        self.check_audit(b'{}\n', {'lines':1,'valid':1,'rejected':0}, [], limit=3)

    def test_empty_and_large_finite_number(self):
        self.check_audit(b'', {'lines':0,'valid':0,'rejected':0}, [])
        self.check_audit(b'1e400', {'lines':1,'valid':1,'rejected':0}, [])

    def test_cli_status_streams_and_source_unchanged(self):
        script = str(Path(__file__).with_name('audit_jsonl.py'))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'input.jsonl'
            data = b'{broken}\n{}\n'
            path.write_bytes(data)
            run = subprocess.run([sys.executable, script, str(path)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 1)
            self.assertEqual(path.read_bytes(), data)
            self.assertEqual(json.loads(run.stdout), {'line':1,'reason':'invalid_or_unsupported_json'})
            self.assertEqual(json.loads(run.stderr), {'lines':2,'valid':1,'rejected':1})
            path.write_bytes(b'{}\n')
            good = subprocess.run([sys.executable, script, str(path)], capture_output=True, text=True)
            self.assertEqual(good.returncode, 0)
            self.assertEqual(good.stdout, '')
            missing = subprocess.run([sys.executable, script, str(Path(folder)/'absent')], capture_output=True, text=True)
            self.assertEqual(missing.returncode, 2)
            self.assertEqual(missing.stdout, '')

if __name__ == '__main__':
    unittest.main(verbosity=2)
