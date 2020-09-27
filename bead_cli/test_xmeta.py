from bead.archive import Archive
from bead.tech.fs import read_file, write_file
from bead.test import TestCase
import bead.zipopener

from . import test_fixtures as fixtures


class Test_xmeta(TestCase, fixtures.RobotAndBeads):

    def test_meta_attributes_are_available_without_reading_the_archive(
        self, robot, bead_with_inputs, beads
    ):
        archive = beads[bead_with_inputs]
        archive_filename = archive.archive_filename

        def get_meta(a: Archive):
            return {
                'meta_version': a.meta_version,
                'content_id': a.content_id,
                'kind': a.kind,
                'timestamp_str': a.timestamp_str,
                'inputs': a.inputs,
                'input_map': a.input_map,
            }

        archive_attributes = get_meta(archive)

        robot.cli('xmeta', archive_filename)
        # damage the archive, so that all data must come from the xmeta file
        with robot.environment:
            write_file(archive_filename, '')
            assert read_file(archive_filename) == ''

        # invalidate zip file cache - keeps zip files open, even after they are removed
        bead.zipopener.close_all()

        xmeta_archive = Archive(archive_filename)
        assert archive_attributes == get_meta(xmeta_archive)
