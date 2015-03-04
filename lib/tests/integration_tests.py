import os
from scripttest import TestFileEnvironment

import fixtures
from testtools import TestCase


class Test_command_line(TestCase):

    def test_package_operations(self):
        home_dir = fixtures.TempHomeDir()
        self.useFixture(home_dir)
        env = TestFileEnvironment(os.path.join(home_dir.path, 'scripttest'))

        new_result = env.run('ws', 'new', 'something')
        self.assertEqual(0, new_result.returncode)
        self.assertIn('something', new_result.files_created)

        status_result = env.run('ws', 'status', cwd=env.cwd + '/something')
        self.assertIn('no defined inputs', status_result.stdout)
        self.assertEqual(0, status_result.returncode)

        pack_result = env.run('ws', 'pack', cwd=env.cwd + '/something')
        self.assertEqual(0, pack_result.returncode)

        package, = pack_result.files_created.keys()

        develop_result = env.run('ws', 'develop', 'something-develop', package)
        self.assertIn('something-develop', develop_result.files_created)
        self.assertEqual(0, develop_result.returncode)

        mount_result = env.run(
            'ws', 'mount', os.path.join('..', package), 'older-self',
            cwd=os.path.join(env.cwd, 'something-develop'))
        self.assertEqual(0, mount_result.returncode)

        nuke_result = env.run('ws', 'nuke', 'something')
        self.assertEqual(0, nuke_result.returncode)
        nuke_result = env.run('ws', 'nuke', 'something-develop')
        self.assertEqual(0, nuke_result.returncode)
