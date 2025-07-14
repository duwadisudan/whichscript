import json
import os
import shutil
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


if __name__ == '__main__':
    unittest.main()
