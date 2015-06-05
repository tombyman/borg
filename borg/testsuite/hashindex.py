import hashlib
import os
import tempfile

from ..hashindex import NSIndex, ChunkIndex
from . import BaseTestCase


class HashIndexTestCase(BaseTestCase):

    def _generic_test(self, cls, make_value, sha):
        idx = cls(key_size=32)
        self.assert_equal(len(idx), 0)
        # Test set
        for x in range(100):
            idx[bytes('%-32d' % x, 'ascii')] = make_value(x)
        self.assert_equal(len(idx), 100)
        for x in range(100):
            self.assert_equal(idx[bytes('%-32d' % x, 'ascii')], make_value(x))
        # Test update
        for x in range(100):
            idx[bytes('%-32d' % x, 'ascii')] = make_value(x * 2)
        self.assert_equal(len(idx), 100)
        for x in range(100):
            self.assert_equal(idx[bytes('%-32d' % x, 'ascii')], make_value(x * 2))
        # Test delete
        for x in range(50):
            del idx[bytes('%-32d' % x, 'ascii')]
        self.assert_equal(len(idx), 50)
        idx_name = tempfile.NamedTemporaryFile()
        idx.write(idx_name.name)
        del idx
        # Verify file contents
        with open(idx_name.name, 'rb') as fd:
            self.assert_equal(hashlib.sha256(fd.read()).hexdigest(), sha)
        # Make sure we can open the file
        idx = cls.read(idx_name.name, key_size=32)
        self.assert_equal(len(idx), 50)
        for x in range(50, 100):
            self.assert_equal(idx[bytes('%-32d' % x, 'ascii')], make_value(x * 2))
        idx.clear()
        self.assert_equal(len(idx), 0)
        idx.write(idx_name.name)
        del idx
        self.assert_equal(len(cls.read(idx_name.name, key_size=32)), 0)

    def test_nsindex(self):
        self._generic_test(NSIndex, lambda x: (x, x),
                           '861d6d60069ea45e39d36bed2bdc1d0c07981e0641955f897ac6848be429abac')

    def test_chunkindex(self):
        self._generic_test(ChunkIndex, lambda x: (x, x, x),
                           '69464bd0ebbc5866b9f95d838bc48617d21bfe3dcf294682a5c21a2ef6b9dc0b')

    def test_resize(self):
        n = 2000  # Must be >= MIN_BUCKETS
        idx_name = tempfile.NamedTemporaryFile()
        idx = NSIndex(key_size=32)
        idx.write(idx_name.name)
        initial_size = os.path.getsize(idx_name.name)
        self.assert_equal(len(idx), 0)
        for x in range(n):
            idx[bytes('%-32d' % x, 'ascii')] = x, x
        idx.write(idx_name.name)
        self.assert_true(initial_size < os.path.getsize(idx_name.name))
        for x in range(n):
            del idx[bytes('%-32d' % x, 'ascii')]
        self.assert_equal(len(idx), 0)
        idx.write(idx_name.name)
        self.assert_equal(initial_size, os.path.getsize(idx_name.name))

    def test_iteritems(self):
        idx = NSIndex(key_size=32)
        for x in range(100):
            idx[bytes('%-0.32d' % x, 'ascii')] = x, x
        all = list(idx.iteritems())
        self.assert_equal(len(all), 100)
        second_half = list(idx.iteritems(marker=all[49][0]))
        self.assert_equal(len(second_half), 50)
        self.assert_equal(second_half, all[50:])
