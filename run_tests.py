"""Run independent plugin suites and existing shared JSFX compatibility checks."""
import argparse
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plugin', choices=('Plexi', 'Preamp'))
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    projects = [args.plugin] if args.plugin else ['Plexi', 'Preamp']
    failed = False
    for directory in [root/'plugins'/p/'tests' for p in projects] + [root/'shared/tests']:
        print(f'Running {directory.relative_to(root)}', flush=True)
        result = subprocess.run([sys.executable, '-m', 'unittest', 'discover',
                                 '-s', str(directory), '-v'], cwd=root)
        failed = failed or result.returncode != 0
    return int(failed)


if __name__ == '__main__':
    sys.exit(main())
