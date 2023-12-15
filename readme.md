# Controls WS2812B LED strips from any device with a spi, automatically timing calculation

## Features

* Uses SPI MOSI line to simulate WS2812B protocol

* All simulation data are automatically calculated to match the protocol timing

* Supports unlimited number of LEDs (Still have some limitations, see below)

* Change spi to any speed you want, code calculates others for you

## Usage

> sudo pip3 install periphery

And then, see `example.py`

I uses `periphery` to control SPI, you can change it to any other library you want, e.g. `spidev`.

Simply change the `_init_spi` and `_send` of `WS2812` class to switch to other libraries.

## Limitation

This method actually uses multiple spi data bits to simulate the data protocol of ws2812b. Since ws2812b is time-strict, the faster the SPI rate, the more actual data is needed to simulate the data of each led. For most SBC boards, the maximum amount of data sent in a single send is 4095 bytes, and more data will be divided into two packets for transmission, which destroys the protocol. Considering that it takes at least 3 bits (@2.3Mhz, allow_error=200) to simulate 1 bit led data, that is, each lamp needs 9 bytes of data, so at most 4095/9=455 lamps can be controlled. If your SBC board's spi driver supports a larger amount of data sent in a single send, then you can control more lamps.

## About allow_error

WS2812B is a very chaotic product line. Although the packaging, appearance, and model of LEDs produced by different manufacturers are the same, if you check their data sheets, you will find that the time parameters of their data protocols are inconsistent. allow_error is the allowable error between the calculated timing and the target timing. The default value is conservative. In most cases, this value can be set higher to adapt to more SPI rates.

## Custom timing

Change the `t0h`, `t1h`, `t0l`, `t1l` default parameters in `calc_timing`.

Or use `timing_calculator` to check the timing.

## SBC Bugs

In some SBC boards (for example, my Radxa Zero), the actual SPI speed may be different from the set speed, which will cause the calculated timing to be inaccurate. You may need a oscilloscope or logic analyzer to check the actual SPI speed.
