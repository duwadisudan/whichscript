import json
import os
import shutil
import sys
import unittest

from whichscript import enable_auto_logging, disable_auto_logging


class AutoLoggingTests(unittest.TestCase):
    def setUp(self):
        enable_auto_logging()
        os.makedirs('test_output', exist_ok=True)

    def tearDown(self):
        disable_auto_logging()
        shutil.rmtree('test_output', ignore_errors=True)

    def test_metadata_created_on_write(self):
        path = 'test_output/file.txt'
        with open(path, 'w', encoding='utf-8') as f:
            f.write('hello')

        meta_path = path + '.metadata.json'
        script_copy = path + '.script'
        self.assertTrue(os.path.exists(meta_path))
        self.assertTrue(os.path.exists(script_copy))
        with open(meta_path, 'r', encoding='utf-8') as mf:
            data = json.load(mf)
        self.assertIn('script_path', data)

    def test_no_metadata_on_read(self):
        path = 'test_output/file2.txt'
        with open(path, 'w', encoding='utf-8'):
            pass
        meta = path + '.metadata.json'
        os.remove(meta)  # remove metadata created from write
        with open(path, 'r', encoding='utf-8'):
            pass
        self.assertFalse(os.path.exists(meta))

    def test_skip_site_packages_frames(self):
        pkg_root = os.path.abspath('fake_sp/site-packages')
        pkg_dir = os.path.join(pkg_root, 'fakepkg')
        os.makedirs(pkg_dir, exist_ok=True)
        with open(os.path.join(pkg_dir, '__init__.py'), 'w', encoding='utf-8') as f:
            f.write('def write(path):\n'
                    '    with open(path, "w", encoding="utf-8") as fh:\n'
                    '        fh.write("data")\n')

        sys.path.insert(0, pkg_root)
        try:
            import fakepkg  # type: ignore
            path = 'test_output/file3.txt'
            fakepkg.write(path)
        finally:
            sys.path.remove(pkg_root)
            sys.modules.pop('fakepkg', None)
            shutil.rmtree('fake_sp', ignore_errors=True)

        meta_path = path + '.metadata.json'
        with open(meta_path, 'r', encoding='utf-8') as mf:
            data = json.load(mf)
        self.assertTrue(data['script_path'].endswith('tests/test_auto_logging.py'))


if __name__ == '__main__':
    unittest.main()
