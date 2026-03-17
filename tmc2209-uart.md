# Guía Definitiva: Interfaz UART del TMC2209
El TMC2209 es un driver de altas prestaciones si se lo configura correctamente a través de su interfaz UART. En esta guía se abordará esta interfaz desde el punto de vista de funcionamiento del protocolo UART en términos de datagramas y la API que otorga el fabricante mediante registros.

El TMC2209 utiliza un bus UART de un solo hilo (Single Wire UART). Esto significa que la transmisión (TX) y recepción (RX) ocurren por el mismo cable físico (`PDN_UART`). Para evitar colisiones en la capa física, el bus es de tipo "Controlador-Periférico", donde la PC/Microcontrolador (Controlador) siempre inicia la comunicación y el TMC2209 (Periférico) solo responde cuando se le habla.

## Protocolo de Comunicación UART
El chip tiene un sistema de **Auto-Baud**. No se necesita configurar la velocidad internamente; el chip calcula su *Baud Rate* midiendo la duración del primer byte de cada mensaje (el *Sync Byte*).

### 1.1 Datagrama de Escritura (Write Access)
Para modificar un registro, el Maestro envía un paquete de **8 bytes**.

***Nota:** Para escribir, se debe sumar `0x80` a la dirección del registro. (Ej: `GCONF` es `0x00`, para escribirle se envía `0x80`).*

| Byte 0 | Byte 1 | Byte 2 | Byte 3 | Byte 4 | Byte 5 | Byte 6 | Byte 7 |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0x05** | **Dirección** | **Registro + 0x80** | **Data 3** | **Data 2** | **Data 1** | **Data 0** | **CRC** |
| Sync | Esclavo (0 a 3) | Reg. de Escritura | MSB | ... | ... | LSB | CRC8-ATM |

*Nota: El TMC2209 no responde a los comandos de escritura, simplemente los ejecuta. Se sabrá que funcionó leyendo el registro inmediatamente después.*

### 1.2 Datagrama de Petición de Lectura (Read Access Request)
Para consultar el estado, el Maestro envía un paquete corto de **4 bytes**.

| Byte 0 | Byte 1 | Byte 2 | Byte 3 |
| :---: | :---: | :---: | :---: |
| **0x05** | **Dirección** | **Registro** | **CRC** |
| Sync | Esclavo (0 a 3) | Dir. del Registro | CRC8-ATM |

### 1.3 Datagrama de Respuesta (Read Access Reply)
Tras recibir una petición de lectura, el TMC2209 procesa y responde enviando **8 bytes**.

| Byte 0 | Byte 1 | Byte 2 | Byte 3 | Byte 4 | Byte 5 | Byte 6 | Byte 7 |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0x05** | **0xFF** | **Registro** | **Data 3** | **Data 2** | **Data 1** | **Data 0** | **CRC** |
| Sync | Maestro | Registro Leído | MSB | ... | ... | LSB | CRC del chip |

*(Nota: El Esclavo siempre envía `0xFF` en el Byte 1 para indicar que este mensaje va dirigido al Maestro).*

---

## Mapa de Registros (La API del Driver)

Se puede dividir los registros en categorías lógicas de operación.

### Registros de Configuración General
#### 1. GCONF (0x00)
| Bit | Descripción del Registro GCONF |
| :---: | :--- |
| **0** | **i_scale_analog**: <br>&nbsp;&nbsp;&nbsp;0: Se saltea referencia externa de voltaje.<br>&nbsp;&nbsp;&nbsp;1: Usa voltaje de referencia (potenciómetro del módulo).<br>*Nota*: Ver sección de control de corriente de los motores. |
| **1** | **internal_Rsense**: <br>&nbsp;&nbsp;&nbsp;0: Opera con resistores sense externos.<br>&nbsp;&nbsp;&nbsp;1: Opera con resistores sense internos.<br>*Nota*: Ver sección de control de corriente de los motores. |
| **2** | **en_SpreadCycle**: <br>&nbsp;&nbsp;&nbsp;0: Modo PWM StealthChop habilitado.<br>&nbsp;&nbsp;&nbsp;1: Modo SpreadCycle habilitado. |
| **3** | **shaft**: <br>&nbsp;&nbsp;&nbsp;0: Dirección de giro del motor estándar.<br>&nbsp;&nbsp;&nbsp;1: Dirección inversa de giro del motor. |
| **4** | **index_otpw**: <br>&nbsp;&nbsp;&nbsp;0: Pin INDEX muestra la primera posición de micropaso del secuenciador.<br>&nbsp;&nbsp;&nbsp;1: Pin INDEX muestra la precaución de sobrecalentamiento.<br>*Nota*: Ver index_step, INDEX tiene lógica de decisión “en serie”. |
| **5** | **index_step**: <br>&nbsp;&nbsp;&nbsp;0: Pin INDEX usa la salida de index_otpw.<br>&nbsp;&nbsp;&nbsp;1: Pin INDEX conmuta cada vez que se genere un paso en el generador de pasos interno. |
| **6** | **pdn_disable**: <br>&nbsp;&nbsp;&nbsp;0: Pin PDN_UART controla ahorro de corriente en reposo.<br>&nbsp;&nbsp;&nbsp;1: Pin PDN_UART funciona como interfaz UART. |
| **7** | **mstep_reg_select**: <br>&nbsp;&nbsp;&nbsp;0: Pines MS1 y MS2 eligen resolución de micropaso.<br>&nbsp;&nbsp;&nbsp;1: Registro MSTEP elige resolución de micropaso. |
| **8** | **multistep_filt**: <br>&nbsp;&nbsp;&nbsp;0: Deshabilita optimización de procesamiento de pasos.<br>&nbsp;&nbsp;&nbsp;1: Habilita un algoritmo que promedia el tiempo entre pasos y los predice. |
| **9** | **test_mode**: <br>&nbsp;&nbsp;&nbsp;0: Operación Normal.<br>&nbsp;&nbsp;&nbsp;1: Pin ENN se trata como probe analogico, configurable según IHOLD. No es para el usuario final. |

#### 2. GSTAT (0x01. Kinda R-Only)
| Bit | Descripción del Registro GSTAT |
| :---: | :--- |
| **0** | **reset**: <br>&nbsp;&nbsp;&nbsp;1: Indica que el IC ha sido reiniciado desde la última lectura. Todos los registros han vuelto a valores por defecto.<br>*Nota*: Se limpia escribiendo un '1' en este bit. |
| **1** | **drv_err**: <br>&nbsp;&nbsp;&nbsp;1: Indica que el driver se detuvo por sobrecalentamiento o cortocircuito desde la última lectura.<br>*Nota*: Ver DRV_STATUS para detalles. Se limpia escribiendo un '1'. |
| **2** | **uv_cp**: <br>&nbsp;&nbsp;&nbsp;1: Indica una condición de baja tensión (undervoltage) en la bomba de carga.<br>*Nota*: El driver se deshabilita en este caso. No es latched (no requiere limpieza manual). |

#### 3. IFCNT (0x02. R-Only)
| Bit | Descripción del Registro IFCNT |
| :---: | :--- |
| **7..0** | **interface_transmission_counter**: <br>&nbsp;&nbsp;&nbsp;Este registro se incrementa con cada escritura exitosa vía UART.<br>*Nota*: Útil para verificar si hubo pérdida de datos en la transmisión serial. |

#### 4. SLAVECONF (0x03)
| Bit | Descripción del Registro SLAVECONF |
| :---: | :--- |
| **11..8** | **SENDDELAY**: <br>&nbsp;&nbsp;&nbsp;Configura el tiempo de espera antes de que el driver envíe una respuesta vía UART:<br>&nbsp;&nbsp;&nbsp;0, 1: 8 bit times<br>&nbsp;&nbsp;&nbsp;2, 3: 3*8 bit times<br>&nbsp;&nbsp;&nbsp;... (incrementos de 2 en 2 hasta 15)<br>&nbsp;&nbsp;&nbsp;14, 15: 15*8 bit times |

#### 5. OTP_PROG (0x04)
| Bit | Descripción del Registro OTP_PROG |
| :---: | :--- |
| **2..0** | **OTPBIT**: <br>&nbsp;&nbsp;&nbsp;Selección del bit OTP a programar (0..7) en la ubicación seleccionada. |
| **5..4** | **OTPBYTE**: <br>&nbsp;&nbsp;&nbsp;Selección de la ubicación de memoria OTP (Byte 0, 1 o 2). |
| **15..8** | **OTPMAGIC**: <br>&nbsp;&nbsp;&nbsp;Debe establecerse en 0xbd para habilitar la programación OTP. |

***NOTA**: No se desarrollará este registro ya que OTP es para configurar estáticamente y las aplicaciones a llevar a cabo configurarán regularmente al driver.*

#### 6. OTP_READ (0x05)
| Bit | Descripción del Registro OTP_READ |
| :---: | :--- |
| **7..0** | **OTP0**: <br>&nbsp;&nbsp;&nbsp;Lectura de los datos almacenados en el Byte 0 de la memoria OTP. |
| **15..8** | **OTP1**: <br>&nbsp;&nbsp;&nbsp;Lectura de los datos almacenados en el Byte 1 de la memoria OTP. |
| **23..16** | **OTP2**: <br>&nbsp;&nbsp;&nbsp;Lectura de los datos almacenados en el Byte 2 de la memoria OTP. |

***NOTA**: No se desarrollará este registro ya que OTP es para configurar estáticamente y las aplicaciones a llevar a cabo configurarán regularmente al driver.*

#### 7. IOIN (0x06. R-Only)
| Bit | Descripción del Registro IOIN (Estado de los Pines) |
| :---: | :--- |
| **0** | **ENN**: <br>&nbsp;&nbsp;&nbsp;Lee el estado lógico del pin físico Enable (activo en bajo). |
| **2** | **MS1**: <br>&nbsp;&nbsp;&nbsp;Lee el estado lógico del pin selector de configuración 1. |
| **3** | **MS2**: <br>&nbsp;&nbsp;&nbsp;Lee el estado lógico del pin selector de configuración 2. |
| **4** | **DIAG**: <br>&nbsp;&nbsp;&nbsp;Lee el estado del pin de diagnóstico. |
| **6** | **PDN_UART**: <br>&nbsp;&nbsp;&nbsp;Lee el estado del pin PDN_UART. |
| **7** | **STEP**: <br>&nbsp;&nbsp;&nbsp;Lee el estado actual del pin de entrada de pasos. |
| **8** | **SPREAD_EN**: <br>&nbsp;&nbsp;&nbsp;Lee el estado del pin selector de SpreadCycle/StealthChop. |
| **9** | **DIR**: <br>&nbsp;&nbsp;&nbsp;Lee el estado del pin de dirección. |
| **31..24** | **VERSION**: <br>&nbsp;&nbsp;&nbsp;Muestra la versión del IC (0x21 para la primera versión). |

#### 8. FACTORY_CONF (0x07)
| Bit | Descripción del Registro FACTORY_CONF |
| :---: | :--- |
| **4..0** | **FCLKTRIM**: <br>&nbsp;&nbsp;&nbsp;Ajuste de frecuencia del reloj interno (0 a 31).<br>*Nota*: Los dispositivos vienen preajustados de fábrica a 12MHz. |
| **9..8** | **OTTRIM**: <br>&nbsp;&nbsp;&nbsp;Configura los umbrales de temperatura de advertencia (OTPW) y apagado (OT):<br>&nbsp;&nbsp;&nbsp;0b00: OT=143°C, OTPW=120°C<br>&nbsp;&nbsp;&nbsp;0b01: OT=150°C, OTPW=120°C<br>&nbsp;&nbsp;&nbsp;0b10: OT=150°C, OTPW=143°C<br>&nbsp;&nbsp;&nbsp;0b11: OT=157°C, OTPW=143°C |
### Registros de Control dependientes de la Velocidad

#### 1. IHOLD_IRUN (0x10)
| Bit | Descripción del Registro IHOLD_IRUN |
| :---: | :--- |
| **4..0** | **IHOLD**: <br>&nbsp;&nbsp;&nbsp;0: Corriente de reposo mínima (1/32).<br>&nbsp;&nbsp;&nbsp;1..31: Escala de corriente desde 2/32 hasta 32/32.<br>*Nota*: En StealthChop, IHOLD=0 permite elegir entre freewheeling o frenado pasivo. |
| **12..8** | **IRUN**: <br>&nbsp;&nbsp;&nbsp;0..31: Corriente del motor en movimiento (1/32 a 32/32).<br>*Nota*: Se recomienda un valor entre 16 y 31 para obtener la mejor resolución de micropasos. |
| **19..16** | **IHOLDDELAY**: <br>&nbsp;&nbsp;&nbsp;0: Reducción de corriente instantánea.<br>&nbsp;&nbsp;&nbsp;1..15: Retraso por cada paso de reducción de corriente en múltiplos de 2^18 ciclos de reloj.<br>*Nota*: Suaviza la transición al reposo para evitar tirones (jerks). |

#### 2. TPOWERDOWN (0x11)
| Bit | Descripción del Registro TPOWERDOWN |
| :---: | :--- |
| **7..0** | **TPOWERDOWN**: <br>&nbsp;&nbsp;&nbsp;0..255: Establece el tiempo de espera desde que se detecta el reposo hasta la reducción de corriente (0 a 5.6s aproximadamente).<br>*Nota*: Se requiere un ajuste mínimo de 2 para permitir el auto-tuning de StealthChop. |

#### 3. TSTEP (0x12)
| Bit | Descripción del Registro TSTEP |
| :---: | :--- |
| **19..0** | **TSTEP**: <br>&nbsp;&nbsp;&nbsp;Mide el tiempo actual entre dos micropasos de 1/256 en unidades de 1/fCLK.<br>*Nota*: En caso de reposo o desbordamiento, el valor es (2^20)-1. Incluye histéresis de 1/16 para compensar el jitter. |

#### 4. TPWMTHRS (0x13)
| Bit | Descripción del Registro TPWMTHRS |
| :---: | :--- |
| **19..0** | **TPWMTHRS**: <br>&nbsp;&nbsp;&nbsp;0: Deshabilitado.<br>&nbsp;&nbsp;&nbsp;>0: Establece el umbral de velocidad superior para el modo StealthChop.<br>*Nota*: Si TSTEP ≥ TPWMTHRS, StealthChop está activo. Si la velocidad supera este límite, el driver cambia a SpreadCycle. |

#### 5. VACTUAL (0x22)
| Bit | Descripción del Registro VACTUAL |
| :---: | :--- |
| **23..0** | **VACTUAL**: <br>&nbsp;&nbsp;&nbsp;0: Operación normal. El driver reacciona a los pulsos del pin STEP.<br>&nbsp;&nbsp;&nbsp;!=0: El motor se mueve a la velocidad dictada por este registro vía UART (+-2^23-1 [μsteps / t]).<br>*Nota*: El signo de VACTUAL controla la dirección. Útil para prescindir de un generador de pulsos externo. |

### Registro del Chopper
#### 1. CHOPCONF (0x6C)
| Bit | Descripción del Registro CHOPCONF |
| :---: | :--- |
| **3..0** | **toff**: <br>&nbsp;&nbsp;&nbsp;0: Driver deshabilitado, todos los puentes apagados.<br>&nbsp;&nbsp;&nbsp;1..15: Tiempo de apagado (slow decay).<br>*Nota*: Requerido para habilitar el motor. En StealthChop cualquier valor >0 funciona. |
| **6..4** | **hstrt**: <br>&nbsp;&nbsp;&nbsp;0..7: Valor de inicio de la histéresis añadido a HEND (suma 1, 2, ..., 8).<br>*Nota*: El decremento de histéresis ocurre cada 16 ciclos de reloj. |
| **10..7** | **hend**: <br>&nbsp;&nbsp;&nbsp;0..15: Valor bajo de histéresis u offset de la onda senoidal (de -3 a 12).<br>*Nota*: Este es el valor base utilizado por el chopper de histéresis. |
| **16..15** | **tbl**: <br>&nbsp;&nbsp;&nbsp;%00..%11: Selección del tiempo de blanking del comparador (16, 24, 32 o 40 ciclos).<br>*Nota*: Se recomiendan los valores %00 o %01 para la mayoría de las aplicaciones. |
| **17** | **vsense**: <br>&nbsp;&nbsp;&nbsp;0: Baja sensibilidad (voltaje en R_SENSE de 0.325V).<br>&nbsp;&nbsp;&nbsp;1: Alta sensibilidad (voltaje en R_SENSE de 0.180V). |
| **27..24** | **mres**: <br>&nbsp;&nbsp;&nbsp;%0000..%1000: Resolución de micropasos (256, 128, ..., hasta FULLSTEP).<br>*Nota*: Define el número de entradas de micropasos por cuarto de onda senoidal. |
| **28** | **intpol**: <br>&nbsp;&nbsp;&nbsp;0: Sin interpolación.<br>&nbsp;&nbsp;&nbsp;1: La resolución de micropasos actual se extrapola a 256 para mayor suavidad. |
| **29** | **dedge**: <br>&nbsp;&nbsp;&nbsp;0: Operación normal de pin STEP.<br>&nbsp;&nbsp;&nbsp;1: Habilita pulso de paso en cada flanco (subida y bajada) para reducir la frecuencia requerida. |
| **30** | **diss2g**: <br>&nbsp;&nbsp;&nbsp;0: Protección contra cortocircuito a tierra activa.<br>&nbsp;&nbsp;&nbsp;1: Protección contra cortocircuito a tierra deshabilitada. |
| **31** | **diss2vs**: <br>&nbsp;&nbsp;&nbsp;0: Protección contra cortocircuito en el lado bajo activa.<br>&nbsp;&nbsp;&nbsp;1: Protección contra cortocircuito en el lado bajo deshabilitada. |

#### 2. PWM_SCALE (0x70. R-Only)
| Bit | Descripción del Registro PWM_SCALE |
| :---: | :--- |
| **7..0** | **PWM_SCALE_SUM**: <br>&nbsp;&nbsp;&nbsp;Ciclo de trabajo actual del PWM (0 a 255).<br>*Nota*: Se usa para escalar los valores de corriente leídos de la tabla senoidal. |
| **24..16** | **PWM_SCALE_AUTO**: <br>&nbsp;&nbsp;&nbsp;Offset con signo (-255 a +255) añadido al ciclo de trabajo calculado.<br>*Nota*: Resultado de la regulación automática de amplitud basada en corriente. |

#### 3. PWM_AUTO (0x72. R-Only)
| Bit | Descripción del Registro PWM_AUTO |
| :---: | :--- |
| **7..0** | **PWM_OFS_AUTO**: <br>&nbsp;&nbsp;&nbsp;Valor de offset determinado automáticamente por el driver (0 a 255).<br>*Nota*: Útil para determinar valores por defecto de encendido para PWM_OFS. |
| **23..16** | **PWM_GRAD_AUTO**: <br>&nbsp;&nbsp;&nbsp;Valor de gradiente determinado automáticamente por el driver (0 a 255).<br>*Nota*: Útil para determinar valores por defecto de encendido para PWM_GRAD. |

#### 4. DRV_STATUS (0x6F. R-Only)
| Bit | Descripción del Registro DRV_STATUS |
| :---: | :--- |
| **31** | **stst**: <br>&nbsp;&nbsp;&nbsp;1: Indica que el motor está en reposo (standstill).<br>*Nota*: Ocurre 2^20 ciclos de reloj después del último pulso de paso. |
| **30** | **stealth**: <br>&nbsp;&nbsp;&nbsp;0: El driver opera en modo SpreadCycle.<br>&nbsp;&nbsp;&nbsp;1: El driver opera en modo StealthChop. |
| **20..16** | **CS_ACTUAL**: <br>&nbsp;&nbsp;&nbsp;Valor actual de la escala de corriente (0 a 31).<br>*Nota*: Se utiliza para monitorear la regulación automática de corriente. |
| **11** | **t157**: <br>&nbsp;&nbsp;&nbsp;1: Se ha superado el umbral de temperatura de 157°C. |
| **10** | **t150**: <br>&nbsp;&nbsp;&nbsp;1: Se ha superado el umbral de temperatura de 150°C. |
| **9** | **t143**: <br>&nbsp;&nbsp;&nbsp;1: Se ha superado el umbral de temperatura de 143°C. |
| **8** | **t120**: <br>&nbsp;&nbsp;&nbsp;1: Se ha superado el umbral de temperatura de 120°C. |
| **7** | **olb**: <br>&nbsp;&nbsp;&nbsp;1: Carga abierta (open load) detectada en la fase B.<br>*Nota*: Indicador informativo. Pueden ocurrir falsos positivos a altas velocidades o en reposo. Evaluar solo a baja velocidad. |
| **6** | **ola**: <br>&nbsp;&nbsp;&nbsp;1: Carga abierta (open load) detectada en la fase A. |
| **5** | **s2vsb**: <br>&nbsp;&nbsp;&nbsp;1: Cortocircuito en el MOSFET de lado bajo detectado en la fase B.<br>*Nota*: El driver se deshabilita. El flag se mantiene activo hasta deshabilitar el driver por software (TOFF=0) o hardware (ENN). |
| **4** | **s2vsa**: <br>&nbsp;&nbsp;&nbsp;1: Cortocircuito en el MOSFET de lado bajo detectado en la fase A. |
| **3** | **s2gb**: <br>&nbsp;&nbsp;&nbsp;1: Cortocircuito a GND detectado en la fase B.<br>*Nota*: El driver se deshabilita. El flag se mantiene activo hasta deshabilitar el driver por software (TOFF=0) o hardware (ENN). |
| **2** | **s2ga**: <br>&nbsp;&nbsp;&nbsp;1: Cortocircuito a GND detectado en la fase A. |
| **1** | **ot**: <br>&nbsp;&nbsp;&nbsp;1: Flag de sobretemperatura. Límite alcanzado.<br>*Nota*: Los puentes se deshabilitan hasta que el IC se enfríe y también se limpie el flag otpw. |
| **0** | **otpw**: <br>&nbsp;&nbsp;&nbsp;1: Flag de pre-advertencia de sobretemperatura. Límite excedido. |

### Monitoreo del Secuenciador y Estado de la Onda Eléctrica

#### 1. MSCNT (0x6A. Read-Only)
| Bit | Descripción del Registro MSCNT |
| :---: | :--- |
| **9..0** | **MSCNT**: <br>&nbsp;&nbsp;&nbsp;Indica la posición actual en la tabla de micropasos para la Fase A.<br>*Nota*: El valor oscila entre 0 y 1023. CUR_B utiliza automáticamente un desfase de 256. Permite conocer la posición exacta del motor dentro de la onda eléctrica. |

#### 2. MSCURACT (0x6B. Read-Only)
| Bit | Descripción del Registro MSCURACT |
| :---: | :--- |
| **8..0** | **CUR_A**: <br>&nbsp;&nbsp;&nbsp;Corriente de micropaso actual para la fase A, leída de la tabla senoidal interna.<br>*Nota*: Valor con signo (+/- 0 a 255). No está escalado por la corriente IRUN/IHOLD. |
| **24..16** | **CUR_B**: <br>&nbsp;&nbsp;&nbsp;Corriente de micropaso actual para la fase B, leída de la tabla senoidal interna.<br>*Nota*: Corresponde al valor de la tabla con un desplazamiento de 90° (256 posiciones) respecto a la fase A. |

### Registros Especiales de Control para StealthChop

#### 1. PWMCONF (0x70)
| Bit | Descripción del Registro PWMCONF |
| :---: | :--- |
| **7..0** | **PWM_OFS**: <br>&nbsp;&nbsp;&nbsp;Offset de amplitud PWM definido por el usuario (0-255).<br>*Nota*: En modo `pwm_autoscale=1`, se usa solo para inicialización. Define la amplitud en reposo. |
| **15..8** | **PWM_GRAD**: <br>&nbsp;&nbsp;&nbsp;Gradiente de amplitud definido por el usuario.<br>&nbsp;&nbsp;&nbsp;Fórmula: PWM_GRAD * 256 / TSTEP.<br>*Nota*: Compensa la fuerza electromotriz inversa (Back-EMF) del motor según la velocidad. |
| **17..16** | **pwm_freq**: <br>&nbsp;&nbsp;&nbsp;Selección de la frecuencia del chopper PWM:<br>&nbsp;&nbsp;&nbsp;%00: fPWM = 2/1024 fCLK<br>&nbsp;&nbsp;&nbsp;%01: fPWM = 2/683 fCLK<br>&nbsp;&nbsp;&nbsp;%10: fPWM = 2/512 fCLK<br>&nbsp;&nbsp;&nbsp;%11: fPWM = 2/410 fCLK |
| **18** | **pwm_autoscale**: <br>&nbsp;&nbsp;&nbsp;0: Amplitud PWM fija (basada en registros).<br>&nbsp;&nbsp;&nbsp;1: Regulación automática de amplitud basada en la corriente medida (Recomendado). |
| **19** | **pwm_autograd**: <br>&nbsp;&nbsp;&nbsp;0: Gradiente fijo (usa el valor de PWM_GRAD).<br>&nbsp;&nbsp;&nbsp;1: Ajuste automático del gradiente para compensar la Back-EMF de forma dinámica. |
| **21..20** | **freewheel**: <br>&nbsp;&nbsp;&nbsp;Configuración de parada cuando IHOLD=0:<br>&nbsp;&nbsp;&nbsp;%00: Normal (Usa corriente de IHOLD).<br>&nbsp;&nbsp;&nbsp;%01: Freewheeling (Bobinas abiertas).<br>&nbsp;&nbsp;&nbsp;%10: Frenado pasivo (Bobinas en corto a GND mediante LS).<br>&nbsp;&nbsp;&nbsp;%11: Frenado pasivo (Bobinas en corto a GND mediante HS). |
| **27..24** | **PWM_REG**: <br>&nbsp;&nbsp;&nbsp;1..15: Gradiente del bucle de regulación.<br>&nbsp;&nbsp;&nbsp;1: Incrementos de 0.5 (regulación más lenta).<br>&nbsp;&nbsp;&nbsp;15: Incrementos de 7.5 (regulación más rápida).<br>*Nota*: Define el cambio máximo de amplitud PWM permitido por cada media onda. |
| **31..28** | **PWM_LIM**: <br>&nbsp;&nbsp;&nbsp;0..15: Límite de amplitud para el escalado automático al conmutar.<br>*Nota*: Limita el "tirón" (jerk) de corriente al volver de SpreadCycle a StealthChop. El valor por defecto es 12. |

### Registros Especiales de Control para StallGuard y CoolStep

#### 1. TCOOLTHRS (0x14)
| Bit | Descripción del Registro TCOOLTHRS |
| :---: | :--- |
| **19..0** | **TCOOLTHRS**: <br>&nbsp;&nbsp;&nbsp;Umbral inferior de velocidad para habilitar CoolStep y la salida de StallGuard en el pin DIAG.<br>*Nota*: Las funciones se activan cuando TCOOLTHRS ≥ TSTEP > TPWMTHRS. Se usa para deshabilitar CoolStep a bajas velocidades donde la medición de carga no es confiable. |

#### 2. SGTHRS (0x40)
| Bit | Descripción del Registro SGTHRS |
| :---: | :--- |
| **7..0** | **SGTHRS**: <br>&nbsp;&nbsp;&nbsp;Umbral de detección de pérdida de pasos (stall).<br>*Nota*: El valor de SG_RESULT se compara con el doble de este umbral. Un "stall" se detecta y señala en el pin DIAG cuando SG_RESULT ≤ SGTHRS * 2. |

#### 3. SG_RESULT (0x41 - R-Only)
| Bit | Descripción del Registro SG_RESULT |
| :---: | :--- |
| **9..0** | **SG_RESULT**: <br>&nbsp;&nbsp;&nbsp;Resultado de la medición de carga de StallGuard4. Valores altos indican menor carga mecánica y más margen de torque.<br>*Nota*: Se actualiza con cada paso completo (fullstep). Los bits 0 y 9 siempre leen 0. Exclusivo del modo StealthChop. |

#### 4. COOLCONF (0x42)
| Bit | Descripción del Registro COOLCONF |
| :---: | :--- |
| **3..0** | **semin**: <br>&nbsp;&nbsp;&nbsp;Umbral inferior de StallGuard para activar el incremento de corriente (CoolStep).<br>&nbsp;&nbsp;&nbsp;%0000: CoolStep desactivado.<br>&nbsp;&nbsp;&nbsp;%0001..%1111: Umbral = SEMIN * 32.<br>*Nota*: Si SG_RESULT cae por debajo de este valor, el motor aumenta la corriente para evitar el stall. |
| **6..5** | **seup**: <br>&nbsp;&nbsp;&nbsp;Ancho del escalón de incremento de corriente por cada medición de StallGuard.<br>&nbsp;&nbsp;&nbsp;%00..%11: Incrementos de 1, 2, 4 u 8 unidades de corriente. |
| **11..8** | **semax**: <br>&nbsp;&nbsp;&nbsp;Umbral superior (histéresis) para reducir la corriente.<br>&nbsp;&nbsp;&nbsp;%0000..%1111: El umbral de reducción es (SEMIN + SEMAX + 1) * 32.<br>*Nota*: Si SG_RESULT alcanza o supera este valor, la corriente disminuye para ahorrar energía. |
| **14..13** | **sedn**: <br>&nbsp;&nbsp;&nbsp;Velocidad de decremento de corriente.<br>&nbsp;&nbsp;&nbsp;%00: Disminuye un nivel por cada 32 lecturas de StallGuard.<br>&nbsp;&nbsp;&nbsp;%01: Disminuye un nivel por cada 8 lecturas.<br>&nbsp;&nbsp;&nbsp;%10: Disminuye un nivel por cada 2 lecturas.<br>&nbsp;&nbsp;&nbsp;%11: Disminuye un nivel por cada lectura. |
| **15** | **seimin**: <br>&nbsp;&nbsp;&nbsp;Límite de reducción de corriente mínima para CoolStep.<br>&nbsp;&nbsp;&nbsp;0: Hasta la mitad (1/2) de la corriente configurada en IRUN.<br>&nbsp;&nbsp;&nbsp;1: Hasta un cuarto (1/4) de la corriente configurada en IRUN. |