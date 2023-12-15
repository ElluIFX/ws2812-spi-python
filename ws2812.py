from typing import Iterator, List, Optional, Tuple, Union


def calc_timing(
    spi_clock_hz: int,
    t0h: int = 350,
    t0l: int = 800,
    t1h: int = 700,
    t1l: int = 600,
    allow_error: int = 150,
) -> List[Tuple[int, int, int, int, int, int, int, int, int]]:
    def calc(th, tl, bit_len):
        len_h, len_l = 0, 0
        while len_h + len_l != bit_len:
            err_h = len_h * spi_ns - th
            err_l = len_l * spi_ns - tl
            if err_h < err_l and err_h <= allow_error:
                len_h += 1
            elif err_l <= allow_error:
                len_l += 1
            else:
                raise ValueError
        for _ in range(4):
            err_h = len_h * spi_ns - th
            err_l = len_l * spi_ns - tl
            if err_h < -allow_error:
                len_h += 1
                len_l -= 1
            elif err_l < -allow_error:
                len_h -= 1
                len_l += 1
            else:
                break
        else:
            raise ValueError
        err_h = len_h * spi_ns - th
        err_l = len_l * spi_ns - tl
        if abs(err_h) > allow_error or abs(err_l) > allow_error:
            raise ValueError
        return len_h, len_l, err_h, err_l

    spi_ns = 1_000_000_000 // spi_clock_hz
    result = []
    for bit_len in range(1, 255):
        if (t0h + t0l - allow_error * 2) >= spi_ns * bit_len or (
            t1h + t1l - allow_error * 2
        ) >= spi_ns * bit_len:
            continue
        if (t0h + t0l + allow_error * 2) <= spi_ns * bit_len or (
            t1h + t1l + allow_error * 2
        ) <= spi_ns * bit_len:
            break
        try:
            t0h_l, t0l_l, t0h_e, t0l_e = calc(t0h, t0l, bit_len)
            t1h_l, t1l_l, t1h_e, t1l_e = calc(t1h, t1l, bit_len)
        except ValueError:
            continue
        result.append((bit_len, t0h_l, t0l_l, t1h_l, t1l_l, t0h_e, t0l_e, t1h_e, t1l_e))
    return result


def timing_calculator(
    spi_clock_hz: int,
    t0h: int = 350,
    t0l: int = 800,
    t1h: int = 700,
    t1l: int = 600,
    allow_error: int = 150,
) -> None:
    """
    Calculate WS2812 simulation parameters,
    You should get timing requirements from LED datasheet

    Args:
        spi_clock_hz: SPI clock speed you want to use (Hz)
        t0h: T0H time from LED datasheet (ns)
        t0l: T0L time from LED datasheet (ns)
        t1h: T1H time from LED datasheet (ns)
        t1l: T1L time from LED datasheet (ns)
        allow_error: Allow error for timing (ns)
    """
    spi_ns = 1_000_000_000 // spi_clock_hz
    print("-" * 30)
    print(f"SPI bit-period: {spi_ns}ns")
    print(f"Allow error: {allow_error}ns")
    print("-" * 30)
    result = calc_timing(spi_clock_hz, t0h, t0l, t1h, t1l, allow_error)
    if not result:
        print("No Solution Found !!")
        print("Increase SPI speed or try higher allow_error")
        print("-" * 30)
    else:
        for bit_len, t0h_l, t0l_l, t1h_l, t1l_l, t0h_e, t0l_e, t1h_e, t1l_e in result:
            print("- Possible setting:")
            print(f"bit_length: {bit_len}")
            print(f"bit0: 0b{'1' * t0h_l + '0' * t0l_l}")
            print(f"bit1: 0b{'1' * t1h_l + '0' * t1l_l}")
            print("- Timing error:")
            print(f"T0H: {t0h_l * spi_ns}ns ({t0h_e:+}ns)")
            print(f"T0L: {t0l_l * spi_ns}ns ({t0l_e:+}ns)")
            print(f"T1H: {t1h_l * spi_ns}ns ({t1h_e:+}ns)")
            print(f"T1L: {t1l_l * spi_ns}ns ({t1l_e:+}ns)")
            print("-" * 30)


class WS2812:

    """
    WS2812 RGB LED driver

    Use SPI to simulate WS2812 protocol
    """

    def _buf_len(self, n: int) -> int:
        return n * self._bit_len * 3

    def __init__(
        self,
        length: int,
        spi_dev_path: str,
        spi_speed: int,
        allow_error: int = 150,
        head_zero: int = 0,
        tail_zero: int = 0,
        auto_send: bool = False,
        grb: bool = True,
        *,
        bit_length: Optional[int] = None,
        bit1: Optional[int] = None,
        bit0: Optional[int] = None,
    ) -> None:
        """
        Init WS2812 driver

        Args:
            length: LED length
            spi_speed: SPI speed (Hz) (Recommend: 4_000_000)
            allow_error: timing allowed error for solution calculation (ns)
            head_zero: head zero for spi data packet
            tail_zero: tail zero for spi data packet
            auto_send: auto refresh LED after set color using __setitem__
            grb: color data order (GRB or RGB), check datasheet for this

        Optional Args:
            bit_length: simulation bit length
            bit1: bit1 simulation data
            bit0: bit0 simulation data

        Note:
            bit_length, bit1 and bit0 is calculated by param_calculator automatically,
            if you want to use your own parameters, you can manually set them.

            head_zero and tail_zero is for device which SPI MOSI line is idle-high,
            and it is not allowed by WS2812 protocol, so we need add some zero to raw data to simulate the RESET timing.
        """
        self._init_spi(spi_dev_path, spi_speed)
        self._length = length
        self._grb = grb
        if bit_length and bit1 and bit0:
            self._bit_len = bit_length
            self._bit1 = bit1
            self._bit0 = bit0
        else:
            result = calc_timing(spi_speed, allow_error=allow_error)
            if not result:
                raise ValueError("No Timing Solution found, try param_calculator")
            bit_len, t0h_l, t0l_l, t1h_l, t1l_l, *_ = result[0]
            self._bit_len = bit_len
            self._bit1 = int("1" * t1h_l + "0" * t1l_l, 2)
            self._bit0 = int("1" * t0h_l + "0" * t0l_l, 2)
            print(
                f"bit_length: {bit_len} bit1: 0b{self._bit1:0{bit_len}b} bit0: 0b{self._bit0:0{bit_len}b}"
            )
        self._head_zero = head_zero
        self._tail_zero = tail_zero
        self._auto_send = auto_send
        self._buf = bytearray(self._buf_len(length) + head_zero + tail_zero)
        self._color = [0] * length
        self.clear()

    def _init_spi(self, spi_dev_path: str, spi_speed: int) -> None:
        from periphery import SPI

        self._spi = SPI(spi_dev_path, 0, spi_speed)

    def _send(self, data: bytes) -> None:
        self._spi.transfer(data)

    def set_color(self, index: int, color: Union[int, Tuple[int, int, int]]) -> None:
        """
        Set one LED color

        Args:
            index: LED index
            color: LED RGB color (0xRRGGBB or (R, G, B))
        """
        assert 0 <= index < self._length
        if isinstance(color, tuple):
            color = (color[0] << 16) | (color[1] << 8) | color[2]
        self._color[index] = color
        if self._grb:
            color = (
                (color & 0x00FF00) << 8 | (color & 0xFF0000) >> 8 | (color & 0x0000FF)
            )
        p = index * self._bit_len * 3 + self._head_zero
        self._buf[p : p + self._bit_len * 3] = bytes(self._bit_len * 3)  # clear
        for bit_offset in range(self._bit_len * 8 * 3):
            if color & (1 << (23 - bit_offset // self._bit_len)):
                self._buf[p + bit_offset // 8] |= (
                    (self._bit1 >> (self._bit_len - 1 - bit_offset % self._bit_len))
                    & 0x01
                ) << (7 - bit_offset % 8)
            else:
                self._buf[p + bit_offset // 8] |= (
                    (self._bit0 >> (self._bit_len - 1 - bit_offset % self._bit_len))
                    & 0x01
                ) << (7 - bit_offset % 8)

    def clear(self) -> None:
        """
        Clear all LED
        """
        for i in range(self._length):
            self.set_color(i, 0)

    def show(self) -> None:
        """
        Show LED
        """
        self._send(self._buf)

    def __len__(self) -> int:
        return self._length

    def __getitem__(self, index: Union[int, slice]) -> Union[int, list[int]]:
        if isinstance(index, int):
            return self._color[index]
        elif isinstance(index, slice):
            return self._color[index.start : index.stop : index.step]
        else:
            raise ValueError

    def __setitem__(
        self,
        index: Union[int, slice],
        value: Union[int, list[int], Tuple[int, int, int]],
    ) -> None:
        if isinstance(index, int) and (not isinstance(value, list)):
            self.set_color(index, value)
        elif isinstance(index, slice):
            start = index.start or 0
            stop = index.stop or self._length
            step = index.step or 1
            if not isinstance(value, list):
                for i in range(start, stop, step):
                    self.set_color(i, value)
            else:
                for i, v in enumerate(value):
                    self.set_color(start + i * step, v)
        else:
            raise ValueError
        if self._auto_send:
            self.show()

    def __iter__(self) -> Iterator[int]:
        return iter(self._color)

    def __list__(self) -> list[int]:
        return list(self._color)

    @staticmethod
    def hsv_to_rgb(
        h: float, s: float, v: float, merge=True
    ) -> Union[int, tuple[int, int, int]]:
        """
        Convert HSV to RGB

        Args:
            h: Hue (0-360)
            s: Saturation (0-255)
            v: Brightness (0-255)
            merge: if True, return 0xRRGGBB, else return (R, G, B)

        Returns:
            RGB color
        """
        max_val = v
        min_val = max_val * (255 - s) / 255
        h %= 360

        adj = (max_val - min_val) * (h % 60) / 60.0
        h_div_60 = int(h / 60)

        if h_div_60 == 0:
            r, g, b = max_val, min_val + adj, min_val
        elif h_div_60 == 1:
            r, g, b = max_val - adj, max_val, min_val
        elif h_div_60 == 2:
            r, g, b = min_val, max_val, min_val + adj
        elif h_div_60 == 3:
            r, g, b = min_val, max_val - adj, max_val
        elif h_div_60 == 4:
            r, g, b = min_val + adj, min_val, max_val
        else:
            r, g, b = max_val, min_val, max_val - adj
        if merge:
            return (int(r) << 16) | (int(g) << 8) | int(b)
        else:
            return int(r), int(g), int(b)
