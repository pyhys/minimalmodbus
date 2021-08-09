from typing import Optional, Union

VERSION: str
PARITY_EVEN: str
PARITY_MARK: str
PARITY_NONE: str
PARITY_ODD: str
PARITY_SPACE: str
FIVEBITS: int
SIXBITS: int
SEVENBITS: int
EIGHTBITS: int
STOPBITS_ONE: int
STOPBITS_ONE_POINT_FIVE: float
STOPBITS_TWO: int
XOFF: bytes
XON: bytes

class Serial:
    port: Optional[str]
    baudrate: int
    timeout: Optional[float]
    _last_written_data: bytes
    def __init__(
        self,
        port: Optional[str] = None,
        baudrate: int = 9600,
        bytesize: int = 8,
        parity: str = "N",
        stopbits: Union[int, float] = 1,
        timeout: Optional[float] = None,
        xonxoff: bool = False,
        rtscts: bool = False,
        write_timeout: Optional[float] = None,
        dsrdtr: bool = False,
        inter_byte_timeout: Optional[float] = None,
    ) -> None: ...
    def __repr__(self) -> str: ...
    def open(self) -> None: ...
    def close(self) -> None: ...
    @property
    def is_open(self) -> bool: ...
    def read(self, size: int = 1) -> bytes: ...
    def write(self, inputdata: bytes) -> int: ...
    def flush(self) -> None: ...
    def reset_input_buffer(self) -> None: ...
    def reset_output_buffer(self) -> None: ...
    def _clean_mock_data(self) -> None: ...
