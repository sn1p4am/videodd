#!/usr/bin/env python3

# Allow direct execution
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import contextlib
import subprocess
import tempfile

from yt_dlp.utils import Popen

rootDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAZY_EXTRACTORS = 'yt_dlp/extractor/lazy_extractors.py'


class TestExecution(unittest.TestCase):
    def read_repo_file(self, *path_parts):
        with open(os.path.join(rootDir, *path_parts), encoding='utf-8') as file:
            return file.read()

    def run_yt_dlp(self, exe=(sys.executable, 'yt_dlp/__main__.py'), opts=('--version', )):
        stdout, stderr, returncode = Popen.run(
            [*exe, '--ignore-config', *opts], cwd=rootDir, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(stderr, file=sys.stderr)
        self.assertEqual(returncode, 0)
        return stdout.strip(), stderr.strip()

    def test_main_exec(self):
        self.run_yt_dlp()

    def test_import(self):
        self.run_yt_dlp(exe=(sys.executable, '-c', 'import yt_dlp'))

    def test_module_exec(self):
        self.run_yt_dlp(exe=(sys.executable, '-m', 'yt_dlp'))

    def test_cmdline_umlauts(self):
        _, stderr = self.run_yt_dlp(opts=('ä', '--version'))
        self.assertFalse(stderr)

    def test_lazy_extractors(self):
        try:
            subprocess.check_call([sys.executable, 'devscripts/make_lazy_extractors.py', LAZY_EXTRACTORS],
                                  cwd=rootDir, stdout=subprocess.DEVNULL)
            self.assertTrue(os.path.exists(LAZY_EXTRACTORS))

            _, stderr = self.run_yt_dlp(opts=('-s', 'test:'))
            if stderr and stderr.startswith('Deprecated Feature: Support for Python'):
                stderr = ''
            self.assertFalse(stderr)

            subprocess.check_call([sys.executable, 'test/test_all_urls.py'], cwd=rootDir, stdout=subprocess.DEVNULL)
        finally:
            with contextlib.suppress(OSError):
                os.remove(LAZY_EXTRACTORS)

    def test_make_completions(self):
        stdout, stderr, returncode = Popen.run(
            ['make', '-n', 'completions'], cwd=rootDir, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(stdout)
        print(stderr, file=sys.stderr)
        self.assertEqual(returncode, 0)
        self.assertIn('devscripts/bash-completion.py', stdout)
        self.assertIn('devscripts/fish-completion.py', stdout)
        self.assertIn('devscripts/zsh-completion.py', stdout)

    def test_release_files_link_points_to_existing_readme_anchor(self):
        readme = self.read_repo_file('README.md')
        workflow = self.read_repo_file('.github', 'workflows', 'release.yml')
        if 'https://github.com/${REPOSITORY}#release-files' in workflow:
            self.assertRegex(readme, r'(?mi)^##?\s+Release Files\s*$')

    def test_make_readme_writes_generated_file_without_overwriting_template(self):
        source_readme = self.read_repo_file('README.md')
        help_text = '''Usage: yt-dlp [OPTIONS] URL [URL...]

  General Options:
    -h, --help                               Print this help text and exit
    -U, --update                             Check if updates are available. You cannot update when
                                             running from source code; Use git to pull the latest
                                             changes
See full documentation
'''
        with tempfile.TemporaryDirectory() as tmpdir:
            template = os.path.join(tmpdir, 'README.md')
            generated = os.path.join(tmpdir, 'README.generated.md')
            with open(template, 'w', encoding='utf-8') as file:
                file.write(source_readme)
            subprocess.run(
                [sys.executable, os.path.join(rootDir, 'devscripts', 'make_readme.py'), template, generated],
                cwd=tmpdir,
                input=help_text,
                text=True,
                stdout=subprocess.DEVNULL,
                check=True)
            with open(template, encoding='utf-8') as file:
                self.assertEqual(file.read(), source_readme)
            with open(generated, encoding='utf-8') as file:
                generated_readme = file.read()
            self.assertIn('# yt-dlp + Web UI', generated_readme)
            self.assertIn('## General Options:\n', generated_readme)
            self.assertNotIn('Use the upstream docs for the exhaustive option list:', generated_readme)
            self.assertIn('# CONFIGURATION', generated_readme)

    def test_makefile_doc_targets_generate_from_generated_readme(self):
        makefile = self.read_repo_file('Makefile')
        self.assertIn('doc: README.txt yt-dlp.1 CONTRIBUTING.md CONTRIBUTORS issuetemplates supportedsites', makefile)
        self.assertIn('README.generated.md: $(PY_CODE_FILES) devscripts/make_readme.py README.md', makefile)
        self.assertIn('README.txt: README.generated.md', makefile)
        self.assertIn('yt-dlp.1: README.generated.md devscripts/prepare_manpage.py', makefile)
        self.assertIn('$(PYTHON) devscripts/prepare_manpage.py README.generated.md yt-dlp.1.temp.md', makefile)

    def test_pyproject_includes_web_app_and_respects_vcs_ignores(self):
        pyproject = self.read_repo_file('pyproject.toml')
        self.assertIn('    "/web_app",', pyproject)
        self.assertRegex(pyproject, r'(?s)\[tool\.hatch\.build\.targets\.wheel\].*?packages\s*=\s*\[\s*"yt_dlp",\s*"web_app",\s*\]')
        self.assertNotRegex(pyproject, r'(?m)^ignore-vcs\s*=\s*true\s*$')

    def test_makefile_tar_includes_web_app_but_excludes_runtime_artifacts(self):
        makefile = self.read_repo_file('Makefile')
        self.assertIn("--exclude 'web_app/downloads'", makefile)
        self.assertIn("--exclude 'web_app/*.db'", makefile)
        self.assertIn("--exclude 'web_app/.env'", makefile)
        self.assertIn("--exclude 'web_app/*.log'", makefile)
        self.assertIn('yt-dlp yt_dlp pyproject.toml devscripts test web_app', makefile)

        gitignore = self.read_repo_file('.gitignore')
        for entry in ('web_app/downloads/', 'web_app/*.db', 'web_app/.env', 'web_app/*.log'):
            self.assertIn(entry, gitignore)


if __name__ == '__main__':
    unittest.main()
