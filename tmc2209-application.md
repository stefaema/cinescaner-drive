# Especificaciones para la Aplicación de actuador rotacional en sistema de Telecine
## 1. Configuración de Hardware
Para la aplicación de crear un actuador rotacional en un telecine, como parte del takeup reel, roller y feed reel, se arranca con los siguientes materiales:

1. Una fuente Switching que entregue 24V a partir de 220V, y que además pueda proveer una corriente suficiente para el sistema (e.g. 4.2A)
2. Un módulo FTDI-USB a 3.3V para poder comunicar el driver con la computadora host que ejecutará el sistema.
3. Un módulo Driver apto para comunicación UART, compatible con los niveles de voltaje del FTDI (3.3V) y los requerimientos del motor y la fuente switching. El driver elegido es el TMC2209.
4. Un motor paso a paso NEMA 17 de 1.5A.
5. Perfboard, soldador, cables, accesoris.
### 1.2. Interconexiones
1. Se conecta la fuente switching al tomacorriente de la instalación y se configura el potenciómetro para que entregue un voltaje adecuado (se ha decidido un valor de 24V). Luego se encastra y suelda una bornera en el perfboard para poder hacer más práctico el mantenimiento y reusabilidad del proyecto.
2. Se encastran 6 pines hembra en la placa para poder conectar a estos un FTDI-USB y asi comunicar al driver. Se sueldan los pines y se decide utilizar un modelo USB-C. Luego se encastra tiras hembra para el driver. El modelo usado en este caso posee 18 pines.
3. Se hace una puesta en común de los pines GND (Ambos GND del driver, GND del FTDI y GND de la fuente Switching)
4. Se conecta VCC y GND a los pines de alimentación del driver que van al motor al pin + y - respectivamente de la bornera de la fuente switching. En paralelo se conecta un capacitor de 100uF de 50V.
5. Se conecta VCC del FTDI al VCC de IO del driver.
6. Se conecta Rx de FTDI al puerto PDN_UART. Tx también por medio de una resistencia de 1KOhm. DTR se conecta al EN del driver por seguridad.
7. Finalmente se conecta los 4 pines del motor al driver. Se utilizan tiras hembra de la misma forma para que sea hot swapable el asunto.

## 2. Configuración de Software
