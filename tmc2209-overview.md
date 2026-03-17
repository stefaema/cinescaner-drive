



# Manual de Inicio Rápido: Módulo de Control TMC2209

## 1. El Circuito Integrado TMC2209

El núcleo de este sistema es el chip **TMC2209** diseñado por Trinamic, un controlador de motores paso a paso bifásicos (bipolar) que destaca por su funcionamiento ultra silencioso y alta eficiencia energética.

*   **Capacidades de Potencia:** El circuito integrado es capaz de manejar corrientes de hasta **2A RMS** continuos por bobina, soportando picos de hasta **2.8A**.
*   **Rangos de Voltaje:** 
    *   **Voltaje Lógico (VCC_IO o 5VOUT):** Funciona en el rango estándar de **3.3V a 5V**, haciéndolo compatible tanto con microcontroladores modernos (ESP32, STM32) como tradicionales (Arduino Uno).
    *   **Suministro del Motor (MOT_VCC / VS):** Soporta desde **5.5V hasta 28V** (con un límite absoluto de 29V). Es altamente recomendable usar voltajes altos (ej. 24V en lugar de 12V) para reducir el ruido y permitir mayores velocidades, ya que supera mejor la fuerza contraelectromotriz (Back EMF) generada por el motor.
*   **Requisitos de Seguridad:** Es **estrictamente necesario** colocar un capacitor electrolítico de al menos **100µF** (recomendable de bajo ESR) en la línea de alimentación del motor, lo más cerca posible del pin de voltaje, para absorber los picos provocados por el encendido y apagado de las bobinas (chopping).
*   **Tecnologías Clave Exclusivas:**
    *   **StealthChop2™:** Garantiza un funcionamiento y un reposo inaudibles.
    *   **SpreadCycle™:** Proporciona un control de corriente ciclo a ciclo para movimientos de alta dinámica y velocidad.
    *   **StallGuard4™:** Mide la carga mecánica en el eje del motor sin necesidad de sensores externos. Permite hacer *Sensorless Homing* (encontrar el tope físico sin un final de carrera).
    *   **CoolStep™:** Trabaja junto a StallGuard para reducir la corriente dinámicamente según la carga, ahorrando hasta un 75% de energía.

## 2. El Módulo de Control TMC2209

Integrar el chip TMC2209 desde cero en una placa requiere lidiar con soldaduras de montaje superficial (paquete QFN diminuto), ruteo de pistas de alta potencia y disipación térmica compleja. El **Módulo TMC2209** nos facilita la vida al abstraer todos estos problemas físicos en una pequeña placa "Plug & Play".

**¿De qué cosas nos libera el módulo?**
*   **Electrónica de soporte:** Ya integra los capacitores cerámicos de filtrado lógico, las resistencias *pull-up/pull-down* necesarias y un potenciómetro accesible para calibración manual.
*   **Resistencias de Sensado (Sense Resistors):** El control de corriente por hardware requiere resistencias de altísima precisión. El módulo ya trae integradas las resistencias SMD (generalmente de 110 mΩ) conectadas correctamente a masa.
*   **Gestión Térmica Inicial:** El PCB del módulo usa múltiples capas de cobre para disipar calor e incluye un disipador de aluminio adhesivo que se coloca directamente sobre el chip, protegiendo los MOSFETs internos.

**Interfaz de Conexión Rápida (Pinout Esencial):**
*   **GND / VMOT:** Entrada de potencia para los motores.
*   **VIO / GND:** Entrada de voltaje lógico (3.3V o 5V).
*   **A1, A2, B1, B2:** Salidas directas hacia las dos bobinas del motor paso a paso.
*   **STEP, DIR:** Entradas clásicas para recibir pulsos de paso y señales de dirección desde el microcontrolador.
*   **EN (Enable):** Activo en estado BAJO. Apaga la etapa de potencia si se pone en ALTO.
*   **MS1, MS2:** Pines para configurar la resolución de micropasos o establecer la dirección UART.
*   **PDN_UART:** Pin multifunción. Por defecto activa el ahorro de energía en reposo (conectado a GND), pero su magia radica en que funciona como el pin de datos bidireccional para comunicación serial (UART).
*   **DIAG / INDEX:** Salidas hacia el microcontrolador. `DIAG` emite alertas (como pérdida de pasos por StallGuard) e `INDEX` emite un pulso cada vez que el motor completa una rotación eléctrica.

## 3. Modos de Operación del Módulo
Existen tres formas de operar el TMC2209, pero nos centraremos en los dos enfoques principales de uso continuo:

### A. Modo Standalone (Legacy / Manual)
Es el reemplazo directo para módulos viejos como el A4988. El microcontrolador solo envía pulsos de movimiento.
*   **La corriente se fija por hardware:** Se debe usar un destornillador de perilla y un multímetro para girar el potenciómetro de la placa (Vref) y fijar el límite máximo de corriente.
*   **Los micropasos se fijan por hardware:** Conectando `MS1` y `MS2` a GND o VCC se eligen resoluciones fijas (8, 16, 32 o 64 micropasos).
*   **Desventaja:** No se puede aprovechar StallGuard, CoolStep ni saber si el driver se está recalentando.

### B. Modo UART
Es el ecosistema recomendado para el TMC2209. Reemplaza la manipulación física por comandos de software a través de un único cable conectado al pin `PDN_UART`.
*   **¿Por qué es superior?:** 
    1.  Permite configurar desde el código la corriente exacta de trabajo (`IRUN`) y establecer una corriente más baja automáticamente cuando el motor se detiene (`IHOLD`), evitando sobrecalentamientos térmicos innecesarios.
    2.  Puedes cambiar la resolución de micropasos hasta 1/256 de forma dinámica.
    3.  Te da acceso a leer diagnósticos detallados: ¿Hay cortocircuito? ¿El chip está a punto de apagarse por temperatura térmica extrema (`otpw`)?
*   **Múltiples motores, un solo puerto:** Usando los pines `MS1` y `MS2` puedes asignarle a cada módulo una dirección (0 a 3). Esto permite controlar y configurar hasta 4 drivers TMC2209 utilizando el mismo bus UART de tu microcontrolador.

*(Nota: Existe un tercer modo llamado "Modo OTP", donde se graba la memoria interna del chip de una sola vez en fábrica para que arranque siempre con configuraciones avanzadas sin necesitar UART en el producto final. Una vez quemada la memoria OTP, no se puede revertir).*


## 4. Mantenimiento y Precauciones Críticas

Para asegurar la supervivencia del módulo y su correcto funcionamiento a largo plazo, respeta estas reglas:

*   **LA REGLA DE ORO (Peligro de Destrucción):** **NUNCA** desconectar el cable del motor paso a paso, ni apagar la fuente de alimentación primaria de 24V mientras el motor esté en movimiento. El motor actuará como un generador (Back EMF) e inyectará un pico de voltaje inverso que destruirá el TMC2209 instantáneamente. Si se necesita apagar el sistema en emergencia, **poner el pin EN en estado ALTO (VIO)** primero, lo que deja flotantes las salidas y permitirá el giro libre (freewheeling) de forma segura.
*   **Gestión Térmica:** La hoja de datos permite 2A RMS, pero el encapsulado QFN se convierte en una estufa. Si la configuración de corriente (Vref o vía UART) supera los **1.2A RMS continuos**, el disipador pasivo ya no es suficiente. Se deberá apuntar un fan directamente a la placa, o el chip entrará en apagado térmico cíclico (thermal shutdown a los 150°C).
*   **Calibración Analógica (Si se usa UART):** Antes de encender el pin EN por primera vez, se debe fijar el Vref midiendo con un multímetro entre GND y la cabeza metálica del potenciómetro. 
    *   Fórmula recomendada (asumiendo las resistencias de 110 mΩ que traen la mayoría de módulos): 
        `Vref = (Corriente_RMS_Deseada * 2.5V) / 1.77A`
    *   *Ejemplo:* Para darle 1A RMS al motor: `(1.0 * 2.5) / 1.77 = 1.41V`. Girar el potenciómetro hasta leer 1.41V.
    *   *Tip:* Empezar siempre con la mitad de la corriente nominal del motor. Solo aumentar de a 0.1V si el motor no tiene fuerza o "pierde pasos" al moverse. Un motor frío y un driver tibio es el escenario ideal.