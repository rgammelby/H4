# 1602A

https://www.instructables.com/LCD-1602-With-Arduino-Uno-R3/

VSS = GND
VDD = 5V
VO = contrast
RW = Read/Write (select mode 0/1)
E = Enable, read when 1.
Backlight:
A -> 3.3V
K -> GND

# Termosensor:

https://arduinogetstarted.com/tutorials/arduino-temperature-sensor

RED = VCC
YELLOW = DATA (digital) 
BLACK = GND

# Build:

Formålet med denne maskine er at måle og vise temperaturen i gulvhøjde, for at vurdere virkningen af min gulvvarme.

Maskinen vil køre periodically i diverse rum i min lejlighed over tid, for at se hvor meget temperaturen varierer, og hvornår. 

## ARDINO:
* 5V -> [+ RAIL0]
* GND -> [- RAIL0]

(per sensor)
* Dn -> BREADBOARD

## SENSOR:
1
* VCC -> [+ RAIL1]
* GND -> [- RAIL1]

2
* VCC -> [+ RAIL2]
* GND -> [- RAIL2]

3
* VCC -> [+ RAIL3]
* GND -> [- RAIL3]

* [+ RAIL] -> 4,7KΩ RESISTOR -> DATA[SENSOR 1], DATA[SENSOR 2], DATA[SENSOR 3], BREADBOARD -> D0

## DISPLAY:

* VCC -> [+ RAIL4]
* GND -> [- RAIL4]
* SDA (DATA) -> BREADBOARD (DATA ROW)