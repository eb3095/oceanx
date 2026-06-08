from __future__ import annotations

import numpy as np

from oceanx.dsp.gmsk_demodulator import GMSKDemodulator


def test_crc16_roundtrip():
    demod = GMSKDemodulator()
    data = b"\x01\x02\x03\x04"
    crc = demod._crc16_ccitt(data)
    assert isinstance(crc, int)
    assert 0 <= crc <= 0xFFFF


def test_bit_unstuff_removes_stuffed_zero():
    demod = GMSKDemodulator()
    stuffed = [1, 1, 1, 1, 1, 0, 0, 1]
    out = demod._bit_unstuff(stuffed)
    assert out[:5] == [1, 1, 1, 1, 1]
    assert len(out) == len(stuffed) - 1


def test_nrzi_decode_changes():
    demod = GMSKDemodulator()
    levels = [1, 1, 0, 0, 1]
    bits = demod._nrzi_decode(levels)
    assert bits == [1, 1, 0, 1, 0]


def test_to_nmea_shape():
    demod = GMSKDemodulator()
    line = demod.to_nmea(b"\x01\x02\x03", fill_bits=0, channel="A")
    assert line.startswith("!AIVDM,1,1,,A,")
    assert "*" in line


def test_decode_channel_small_input():
    demod = GMSKDemodulator()
    iq = np.zeros(4, dtype=np.complex64)
    assert demod.decode_channel(iq, offset_hz=0.0) == []
