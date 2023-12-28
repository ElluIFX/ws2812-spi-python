# STM32 C Code for WS2812B LED Strip

Code is different from python version, but the idea is the same.

LED Buffer is dynamically allocated, note your heap size.

> BUFFER_SIZE = (BIT_LEN x 3 x LED_NUM) bytes

Configure SPI parameters and enable DMA TX in CubeMX.

BIT_LEN, BIT1 and BIT0 should be manually set, you can use python script to calculate them.
