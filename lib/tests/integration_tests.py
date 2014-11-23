from nose import tools
from scripttest import TestFileEnvironment


def test_package_operations():
    env = TestFileEnvironment()
    result = env.run('ws', 'new', 'something')

    tools.assert_in('something', result.files_created)

    mounts_list = env.run('ws', 'mounts', cwd=env.cwd + '/something')
    tools.assert_in('no defined inputs', mounts_list.stdout)

    pack_result = env.run('ws', 'pack', cwd=env.cwd + '/something')

    package, = pack_result.files_created.keys()

    result = env.run('ws', 'develop', 'something-develop', package)

    tools.assert_in('something-develop', result.files_created)
