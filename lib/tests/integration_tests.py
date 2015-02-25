from scripttest import TestFileEnvironment

import fixtures
from testtools import TestCase


class Test_command_line(TestCase):

    def test_package_operations(self):
        self.useFixture(fixtures.TempHomeDir())
        env = TestFileEnvironment()
        result = env.run('ws', 'new', 'something')

        self.assertIn('something', result.files_created)

        mounts_list = env.run('ws', 'status', cwd=env.cwd + '/something')
        self.assertIn('no defined inputs', mounts_list.stdout)

        pack_result = env.run('ws', 'pack', cwd=env.cwd + '/something')

        package, = pack_result.files_created.keys()

        result = env.run('ws', 'develop', 'something-develop', package)

        self.assertIn('something-develop', result.files_created)
