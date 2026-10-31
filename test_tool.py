import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from tool import analyze

ROOT = Path(__file__).resolve().parent
SAMPLE = json.loads((ROOT / 'examples/sample.json').read_text())
EXPECTED = json.loads((ROOT / 'examples/expected.json').read_text())


class AnalysisTests(unittest.TestCase):
    def test_documented_example(self):
        self.assertEqual(analyze(copy.deepcopy(SAMPLE)), EXPECTED)

    def test_changed_workload(self):
        data = copy.deepcopy(SAMPLE)
        data['new_cpu'] = 40
        result = analyze(data)
        for key, expected in {'fits': False}.items():
            self.assertEqual(result[key], expected)

    def test_missing_field(self):
        data = copy.deepcopy(SAMPLE)
        del data[next(iter(data))]
        with self.assertRaises(ValueError): analyze(data)

    def test_invalid_type(self):
        with self.assertRaises(ValueError): analyze([])

    def test_no_input_mutation(self):
        data = copy.deepcopy(SAMPLE)
        analyze(data)
        self.assertEqual(data, SAMPLE)

    def test_cli(self):
        result = subprocess.run([sys.executable, str(ROOT / 'tool.py'), str(ROOT / 'examples/sample.json')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), EXPECTED)

    def test_missing_input_file(self):
        result = subprocess.run([sys.executable, str(ROOT / 'tool.py'), str(ROOT / 'does-not-exist.json')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('Input error:', result.stderr)


if __name__ == '__main__':
    unittest.main()
