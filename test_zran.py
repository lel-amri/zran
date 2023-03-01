import os
import tempfile
import zlib

import pytest

import zran


def test_index():
    data = os.urandom(2**24)
    compressed = zlib.compress(data, wbits=15 + zlib.MAX_WBITS)
    compressed_file = tempfile.NamedTemporaryFile()
    with open(compressed_file.name, 'wb') as f:
        f.write(compressed)

    index = zran.build_deflate_index(compressed_file.name)
    points = index.points
    assert points[0].outloc == 0
    assert points[0].inloc == 10
    assert points[0].bits == 0
    assert len(points[0].window) == 32768


@pytest.mark.skip(reason="Cannot figure out how to handle errors")
def test_build_deflate_index_fail():
    data = os.urandom(2**24)
    compressed = zlib.compress(data, wbits=15 + zlib.MAX_WBITS)
    compressed_file = tempfile.NamedTemporaryFile()
    with open(compressed_file.name, 'wb') as f:
        # Corrupt data on purpose
        f.write(compressed[:-1])

    with pytest.raises(zran.ZranError):
        index = zran.build_deflate_index(compressed_file.name)


def test_index_to_file():
    data = os.urandom(2**24)
    compressed = zlib.compress(data, wbits=15 + zlib.MAX_WBITS)
    compressed_file = tempfile.NamedTemporaryFile()
    with open(compressed_file.name, 'wb') as f:
        f.write(compressed)

    index = zran.build_deflate_index(compressed_file.name)
    index.to_file('out.dflidx')
    with open('out.dflidx', 'rb') as f:
        dflidx = f.read()
    mode, length, have, points = zran.WrapperDeflateIndex.parse_dflidx(dflidx)
    assert dflidx[0:6] == b'DFLIDX'


def test_create_index_from_file():
    data = os.urandom(2**24)
    compressed = zlib.compress(data, wbits=15 + zlib.MAX_WBITS)
    compressed_file = tempfile.NamedTemporaryFile()
    with open(compressed_file.name, 'wb') as f:
        f.write(compressed)

    index_file = tempfile.NamedTemporaryFile()
    index = zran.build_deflate_index(compressed_file.name)
    index.to_file(index_file.name)
    del index

    new_index = zran.WrapperDeflateIndex.from_file(index_file.name)
    assert new_index.points[0].outloc == 0


def test_extract_data_with_tmp_index():
    start = 100
    length = 1000
    data = os.urandom(2**24)
    compressed = zlib.compress(data, wbits=15 + zlib.MAX_WBITS)
    compressed_file = tempfile.NamedTemporaryFile()
    with open(compressed_file.name, 'wb') as f:
        f.write(compressed)

    test_data = zran.extract_data_with_tmp_index(compressed_file.name, start, length)
    assert data[start : start + length] == test_data


def test_extract_using_index():
    start = 100
    length = 1000

    data = os.urandom(2**24)
    compressed = zlib.compress(data, wbits=15 + zlib.MAX_WBITS)
    compressed_file = tempfile.NamedTemporaryFile()
    with open(compressed_file.name, 'wb') as f:
        f.write(compressed)

    index = zran.build_deflate_index(compressed_file.name)
    index_file = tempfile.NamedTemporaryFile()
    index.to_file(index_file.name)
    del index

    test_data = zran.extract_data(compressed_file.name, index_file.name, start, length)
    assert data[start : start + length] == test_data
