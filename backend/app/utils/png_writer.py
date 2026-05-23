import struct
import zlib
from pathlib import Path


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def write_solid_png(path: Path, *, width: int, height: int, color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw_rows = []
    row = bytes(color) * width
    for _ in range(height):
        raw_rows.append(b"\x00" + row)

    payload = b"".join(raw_rows)
    png = b"".join(
        [
            PNG_SIGNATURE,
            _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
            _chunk(b"IDAT", zlib.compress(payload)),
            _chunk(b"IEND", b""),
        ]
    )
    path.write_bytes(png)


def _chunk(chunk_type: bytes, data: bytes) -> bytes:
    checksum = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", checksum)
