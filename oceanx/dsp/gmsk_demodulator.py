"""Numpy AIS GMSK demodulator with HDLC deframing."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List

import numpy as np

from oceanx.config import AIS_BAUD, SAMPLE_RATE


@dataclass
class DecodedFrame:
    payload: bytes
    fill_bits: int


class GMSKDemodulator:
    def __init__(self, sample_rate: int = SAMPLE_RATE, baud: int = AIS_BAUD) -> None:
        self.sample_rate = sample_rate
        self.baud = baud
        self.samples_per_symbol = self.sample_rate / float(self.baud)

    def decode_channel(self, iq: np.ndarray, offset_hz: float) -> List[DecodedFrame]:
        if iq.size < 8:
            return []
        mixed = self._mix_to_offset(iq, offset_hz)
        demod = self._quadrature_demod(mixed)
        filt = self._smooth(demod, taps=7)
        symbols = self._sample_symbols(filt)
        nrz_bits = (symbols > 0).astype(np.uint8).tolist()
        hdlc_bits = self._nrzi_decode(nrz_bits)
        frames = self._deframe_hdlc(hdlc_bits)
        decoded: List[DecodedFrame] = []
        for frame in frames:
            if len(frame) < 3:
                continue
            data = frame[:-2]
            rx_crc = int.from_bytes(frame[-2:], "little")
            if self._crc16_ccitt(data) != rx_crc:
                continue
            fill_bits = (6 - ((len(data) * 8) % 6)) % 6
            decoded.append(DecodedFrame(payload=data, fill_bits=fill_bits))
        return decoded

    def to_nmea(self, payload: bytes, fill_bits: int, channel: str = "A") -> str:
        encoded_payload, calc_fill = self._to_sixbit(payload)
        fill = fill_bits if fill_bits >= 0 else calc_fill
        body = f"AIVDM,1,1,,{channel},{encoded_payload},{fill}"
        checksum = 0
        for ch in body:
            checksum ^= ord(ch)
        return f"!{body}*{checksum:02X}"

    def _mix_to_offset(self, iq: np.ndarray, offset_hz: float) -> np.ndarray:
        n = np.arange(iq.size, dtype=np.float64)
        rot = np.exp(-1j * 2.0 * math.pi * offset_hz * n / self.sample_rate)
        return (iq.astype(np.complex64) * rot).astype(np.complex64)

    @staticmethod
    def _quadrature_demod(iq: np.ndarray) -> np.ndarray:
        if iq.size < 2:
            return np.zeros(0, dtype=np.float32)
        prod = iq[1:] * np.conj(iq[:-1])
        return np.angle(prod).astype(np.float32)

    @staticmethod
    def _smooth(samples: np.ndarray, taps: int = 7) -> np.ndarray:
        if samples.size == 0:
            return samples
        kernel = np.ones(max(1, taps), dtype=np.float32) / float(max(1, taps))
        return np.convolve(samples, kernel, mode="same").astype(np.float32)

    def _sample_symbols(self, samples: np.ndarray) -> np.ndarray:
        if samples.size == 0:
            return np.zeros(0, dtype=np.float32)
        sps = max(1, int(round(self.samples_per_symbol)))
        best_start = 0
        best_energy = -1.0
        for start in range(min(sps, samples.size)):
            lane = samples[start::sps]
            energy = float(np.mean(np.abs(lane))) if lane.size else 0.0
            if energy > best_energy:
                best_energy = energy
                best_start = start
        return samples[best_start::sps]

    @staticmethod
    def _nrzi_decode(levels: Iterable[int]) -> List[int]:
        out: List[int] = []
        prev = 1
        for level in levels:
            bit = 1 if level == prev else 0
            out.append(bit)
            prev = level
        return out

    def _deframe_hdlc(self, bits: List[int]) -> List[bytes]:
        flag = [0, 1, 1, 1, 1, 1, 1, 0]
        frames: List[bytes] = []
        i = 0
        while i <= len(bits) - len(flag):
            if bits[i : i + 8] != flag:
                i += 1
                continue
            i += 8
            payload_bits: List[int] = []
            while i <= len(bits) - 8 and bits[i : i + 8] != flag:
                payload_bits.append(bits[i])
                i += 1
            if len(payload_bits) < 16:
                continue
            unstuffed = self._bit_unstuff(payload_bits)
            frames.append(self._bits_to_bytes(unstuffed))
        return frames

    @staticmethod
    def _bit_unstuff(bits: List[int]) -> List[int]:
        out: List[int] = []
        ones = 0
        i = 0
        while i < len(bits):
            bit = bits[i]
            out.append(bit)
            if bit == 1:
                ones += 1
                if ones == 5 and i + 1 < len(bits) and bits[i + 1] == 0:
                    i += 1
                    ones = 0
            else:
                ones = 0
            i += 1
        return out

    @staticmethod
    def _bits_to_bytes(bits: List[int]) -> bytes:
        if not bits:
            return b""
        take = (len(bits) // 8) * 8
        out = bytearray()
        for idx in range(0, take, 8):
            value = 0
            for bit_pos in range(8):
                value |= (bits[idx + bit_pos] & 1) << bit_pos
            out.append(value)
        return bytes(out)

    @staticmethod
    def _crc16_ccitt(data: bytes) -> int:
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0x8408
                else:
                    crc >>= 1
        return crc & 0xFFFF

    @staticmethod
    def _to_sixbit(data: bytes) -> tuple[str, int]:
        try:
            from pyais.util import SixBitNibleEncoder  # type: ignore

            encoder = SixBitNibleEncoder(data)
            payload = getattr(encoder, "payload", None)
            if isinstance(payload, str):
                fill = getattr(encoder, "fill_bits", 0)
                return payload, int(fill)
        except Exception:
            pass

        bits = "".join(f"{b:08b}"[::-1] for b in data)
        fill = (6 - (len(bits) % 6)) % 6
        bits += "0" * fill
        chars: List[str] = []
        for i in range(0, len(bits), 6):
            value = int(bits[i : i + 6][::-1], 2)
            chars.append(chr(value + 48 if value < 40 else value + 56))
        return "".join(chars), fill
