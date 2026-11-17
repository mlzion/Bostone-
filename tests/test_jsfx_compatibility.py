"""Conservative source lint, NOT an EEL2 compiler or host integration test."""
import re
import unittest
from pathlib import Path


def compatibility_errors(source):
    # Preserve line numbers while ignoring comments and quoted text. Scan every
    # executable section, including future @block/@serialize/@gfx additions.
    ignored = re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"')
    source = ignored.sub(lambda m: re.sub(r'[^\n]', ' ', m.group()), source)
    errors = []
    stack = []
    section = None
    for number, line in enumerate(source.splitlines(), 1):
        if line.lstrip().startswith('@'):
            section = line.strip().split()[0]
        if section is None:
            continue
        for match in re.finditer(r'(?<![\w.])(?:\d+(?:\.\d*)?|\.\d+)[eE][+-]?\d+', line):
            errors.append(f'{number}: scientific literal {match.group()}; use decimal notation')
        if '^' in line:
            errors.append(f'{number}: caret operator prohibited; use pow() for powers')
        for char in line:
            if char in '([':
                stack.append((char, number))
            elif char in ')]':
                if not stack or stack[-1][0] != {')':'(', ']':'['}[char]:
                    errors.append(f'{number}: unmatched {char}')
                else:
                    stack.pop()
    errors.extend(f'{line}: unclosed {char}' for char,line in stack)
    # EEL2 names are case-insensitive, unlike the Python numerical model.
    for match in re.finditer(r'\b(?:local|instance)\(([^)]*)\)', source):
        names = [x.strip().lower() for x in match[1].split(',') if x.strip()]
        if len(names) != len(set(names)):
            errors.append('duplicate case-insensitive local/instance identifier')
    return errors


class CompatibilityTests(unittest.TestCase):
    def test_actual_production_source(self):
        root = Path(__file__).parents[1]
        files = sorted((root/'jsfx').rglob('*.jsfx'))
        self.assertTrue(files)
        for path in files:
            self.assertEqual(compatibility_errors(path.read_text()), [], str(path))

    def test_scientific_literals_in_every_processing_section(self):
        for section in ('init','slider','block','sample'):
            for literal in ('1e12','1e-30','1E+12','.5e2','1.e-3'):
                self.assertTrue(compatibility_errors(f'@{section}\nx={literal};'))

    def test_decimal_replacements_and_pow(self):
        self.assertEqual(compatibility_errors(
            '@sample\nx=1000000000000; y=0.000000000000000000000000000001; z=pow(2,3);'), [])
        self.assertEqual(float('1000000000000'), 1e12)
        self.assertEqual(float('0.000000000000000000000000000001'), 1e-30)

    def test_caret_in_executable_source(self):
        self.assertTrue(compatibility_errors('@block\nx=2^3;'))
        self.assertEqual(compatibility_errors('@init\n// 1e12 ^\n/* 1e-30 */\nx=pow(2,3);'), [])

    def test_structure_and_case_collisions(self):
        self.assertTrue(compatibility_errors('@init\nx=(1+2;'))
        self.assertTrue(compatibility_errors('@init\nfunction f() local(a,A) (0;);'))
