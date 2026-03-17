


# TMC2209: Guía

Esta guía detalla el funcionamiento físico de los motores paso a paso y cómo el driver TMC2209 abstrae y controla estos procesos mecánicos y eléctricos a través de su arquitectura de registros por interfaz UART.

---

## 1. Funcionamiento de un Motor Paso a Paso

### 1.1. Electromagnetismo y Movimiento Básico
Un motor paso a paso (stepper) transforma pulsos eléctricos en movimientos mecánicos discretos (pasos). Consta de un rotor magnético dentado y un estator con bobinas. Al energizar secuencialmente las bobinas del estator, se genera un campo magnético que atrae los dientes del rotor, forzándolo a alinearse y produciendo la rotación.

### 1.2. Fases y Bobinas
Un motor bifásico estándar posee dos conjuntos de bobinas: Fase A y Fase B. 
Para generar un paso completo ("Full Step"), se aplican ondas de corriente cuadradas desfasadas 90° entre ambas fases. La alternancia de polaridad en estas dos fases crea un campo magnético rotativo que el rotor sigue.

### 1.3. Bipolares (4 pines) vs Unipolares (6 pines)
*   **Unipolares (6 pines):** Poseen una derivación central en cada bobina. Simplifican el circuito de control (requieren solo transistores simples) porque la corriente siempre fluye en la misma dirección hacia tierra, alternando qué mitad de la bobina se energiza. Utilizan solo la mitad del devanado a la vez, entregando menos torque.
*   **Bipolares (4 pines):** Utilizan la bobina completa, entregando mayor torque. Requieren invertir la polaridad de la corriente en la misma bobina, lo que exige un circuito tipo Puente H (H-Bridge).
*   **Aplicación:** El TMC2209 integra dos Puentes H y está diseñado para controlar motores **bipolares de 4 pines**.

---

## 2. El Rol del Driver TMC2209

### 2.1. El Puente H (H-Bridge)
El driver contiene internamente puentes compuestos por transistores MOSFET. Al conmutar los transistores opuestos en diagonal, el driver puede invertir el sentido de la corriente en la Fase A o la Fase B sin necesidad de cables adicionales.

### 2.2. Microstepping (MicroPlyer™)
Las ondas cuadradas generan movimientos bruscos, resonancia y ruido. El microstepping divide cada paso completo en pasos más pequeños inyectando una onda senoidal escalonada. 
*   **Implementación interna:** El TMC2209 posee una tabla senoidal interna de 1024 posiciones (equivalente a 4 pasos completos o un ciclo eléctrico). Mediante la tecnología MicroPlyer, interpola señales de paso de baja resolución hasta alcanzar **256 micropasos** por cada paso completo.
*   **Registros de lectura:**
    *   `MSCNT` (0-1023): Indica la posición actual exacta del rotor dentro de la tabla senoidal.
    *   `MSCURACT`: Muestra la corriente actual inyectada en la Fase A y Fase B, derivada de la posición en la tabla.

### 2.3. Control de Corriente (Chopping)
Los motores son cargas inductivas: la corriente tarda en subir. Para alcanzar altas velocidades, se alimenta el motor con voltajes mucho mayores al nominal (ej. 24V para un motor de 3V). Para no quemar la bobina, el driver enciende y apaga los MOSFETs a alta frecuencia (PWM) limitando la corriente a un valor máximo configurado. Este proceso se denomina *chopping*.
*   **Registros de control:**
    *   `IRUN` (0-31): Escala la corriente de trabajo (RMS) del motor.
    *   `IHOLD` (0-31): Establece una corriente reducida cuando el motor está en reposo para evitar sobrecalentamiento.
    *   `IHOLDDELAY`: Configura el tiempo de transición suave entre `IRUN` e `IHOLD`.

---

## 3. SpreadCycle™: Control de Corriente de Precisión

### 3.1. El Problema Clásico (Mixed Decay)
En drivers antiguos, la corriente no sigue de manera perfecta la onda senoidal ideal, especialmente durante el cruce por cero (cambio de polaridad de la bobina). Esto genera una "zona muerta" o meseta en la gráfica de corriente, provocando vibración mecánica y pérdida de torque.

### 3.2. Solución SpreadCycle
SpreadCycle es un algoritmo de chopper de control de corriente ciclo a ciclo (cycle-by-cycle). Mide la corriente a través de las resistencias de sensado (`RSENSE` o medición interna de RDSon) y ajusta dinámicamente las duraciones de decaimiento rápido (fast decay) y lento (slow decay). Esto garantiza una onda senoidal limpia y sin distorsión en el cruce por cero, ideal para altas velocidades y dinámicas de alta aceleración.

### 3.3. Registros de Control
SpreadCycle se habilita mediante el registro `GCONF`, bit `en_spreadCycle = 1`. Se afina usando el registro **`CHOPCONF`**:
*   `TOFF`: Tiempo de apagado (slow decay). Determina la frecuencia base del chopper (valores recomendados: 3, 4 o 5). Si `TOFF = 0`, el driver se desactiva.
*   `TBL`: Blank time. Tiempo que el comparador ignora los picos de voltaje residual tras conmutar los MOSFETs.
*   `HSTRT` y `HEND`: Controlan el valor de inicio y fin de la histéresis del chopper. Regulan el "ripple" o rizado de la corriente.

---

## 4. StealthChop2™: Operación Silenciosa

### 4.1. Origen del Ruido
El ruido del motor es producto de la magnetostricción (vibración del estator causada por el rizado agresivo de la corriente en choppers tradicionales) y de la frecuencia audible del PWM de regulación.

### 4.2. Funcionamiento de StealthChop2
StealthChop no usa control ciclo a ciclo basado en la corriente, sino que se basa en regulación de **voltaje (Voltage-mode PWM)**. Genera una modulación de voltaje senoidal extremadamente pura, eliminando el rizado de corriente y el ruido audible casi por completo a bajas y medias velocidades.

### 4.3. Auto-Tuning
Para que StealthChop entregue la corriente correcta regulando solo voltaje, necesita conocer la resistencia de la bobina y la fuerza contraelectromotriz (Back-EMF). Realiza un auto-ajuste en dos fases:
*   **AT#1 (En reposo):** Evalúa la resistencia del motor inyectando voltaje sin movimiento.
*   **AT#2 (En movimiento):** Evalúa la Back-EMF a medida que el motor gira (típicamente entre 60 y 300 RPM).

### 4.4. Registros y Transición
StealthChop se habilita por defecto (o con `GCONF.en_spreadCycle = 0`). Se configura en el registro **`PWMCONF`**:
*   `pwm_autoscale = 1` y `pwm_autograd = 1`: Habilitan el auto-tuning.
*   `PWM_OFS_AUTO` / `PWM_GRAD_AUTO`: Registros de solo lectura donde el driver guarda los resultados del tuning.

**Transición Híbrida (`TPWMTHRS`):**
StealthChop pierde torque y precisión a altas velocidades donde la Back-EMF es casi igual al voltaje de fuente. 
El TMC2209 permite un cambio al vuelo:
*   `TPWMTHRS`: Se configura con el valor del intervalo de tiempo entre pasos (`TSTEP`) que representa el umbral de velocidad. Si el motor supera esta velocidad (`TSTEP < TPWMTHRS`), el driver desactiva StealthChop y cambia automáticamente a SpreadCycle.

---

## 5. StallGuard4™: Sensorless Homing y Carga Mecánica

### 5.1. Back-EMF y Carga Mecánica
Un motor en movimiento actúa como un generador, creando un voltaje inverso (Back-EMF). Cuando la carga mecánica en el eje aumenta (ej. al taladrar, cortar o chocar contra un tope), el rotor se retrasa respecto al campo magnético del estator (aumenta el ángulo de carga). Esto reduce la Back-EMF generada.

### 5.2. StallGuard4
StallGuard4 mide internamente estas sutiles reducciones de Back-EMF sin necesidad de hardware adicional ni sensores de fin de carrera. Está optimizado específicamente para operar en conjunto con StealthChop2.

### 5.3. Registros de Detección
*   **`SG_RESULT`** (0-510): Registro de solo lectura actualizado en cada paso completo. Un valor alto indica que el motor gira libre. Un valor cercano a 0 indica carga máxima o bloqueo inminente.
*   **`SGTHRS`** (0-255): Registro de escritura. Define el umbral de choque. Si `SG_RESULT` cae por debajo de `SGTHRS * 2`, el driver asume un bloqueo (Stall) y emite una señal alta en el pin de hardware `DIAG`.
*   **`TCOOLTHRS`**: La medición de StallGuard requiere una velocidad mínima (Back-EMF suficiente). StallGuard solo funciona si la velocidad es mayor a la definida en este registro (`TSTEP < TCOOLTHRS`).

---

## 6. CoolStep™: Eficiencia Energética Adaptativa

### 6.1. El Problema del Lazo Abierto
En un sistema estándar, la corriente del motor se ajusta (`IRUN`) para el peor escenario (la mayor carga que vaya a soportar). Si el motor gira libremente el 90% del tiempo, usar la corriente máxima genera calor excesivo en los MOSFETs y el motor, desperdiciando energía.

### 6.2. Regulación Dinámica CoolStep
CoolStep lee el nivel de carga mecánica reportado por StallGuard4 y ajusta la corriente del motor al vuelo.
Si la carga aumenta (ej. la herramienta toca el material), CoolStep incrementa la corriente instantáneamente para evitar perder pasos. Si la carga desaparece, disminuye la corriente para ahorrar hasta un 75% de energía.

### 6.3. Sintonización mediante Registros
Se configura usando el registro **`COOLCONF`**:
*   `SEMIN`: Umbral inferior. Si `SG_RESULT` cae por debajo de este valor, hay mucha carga y CoolStep aumentará la corriente.
*   `SEMAX`: Umbral superior. Si `SG_RESULT` supera este valor, hay poca carga y CoolStep reducirá la corriente.
*   `SEUP`: Define el tamaño del salto de corriente hacia arriba (reacción rápida para no perder pasos).
*   `SEDN`: Define el tamaño del escalón hacia abajo (reacción lenta para bajar temperatura).

**Monitoreo:**
*   **`CSACTUAL`** (0-31): Registro de lectura que muestra la corriente real escalada que CoolStep está entregando en este preciso momento. Este valor oscila de manera automática entre una fracción configurada y el límite superior dictado por `IRUN`.

