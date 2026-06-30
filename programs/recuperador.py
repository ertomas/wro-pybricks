# recuperador.py
# ---------------------------------------------------------------------------
# ROBOT RECUPERADOR
#
# Escucha el canal BLE. Cuando el explorador le transmite la posicion del
# objeto (x, y, clase), navega hasta ahi con su propia odometria, cierra la
# garra para agarrar el objeto y vuelve al origen.
#
# Origen acordado: ambos robots arrancan en (0, 0) mirando hacia +x (0 grados).
# El recuperador tiene que arrancar en el MISMO origen que el explorador para
# que las coordenadas signifiquen lo mismo.
#
# Ajusta wheel_diameter y axle_track segun TU robot (ver challenge 02).
# Puertos: motores de manejo en A/B, garra en C.
# ---------------------------------------------------------------------------

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction
from pybricks.robotics import DriveBase
from pybricks.tools import wait
from umath import atan2, degrees, sqrt

# El canal (1) tiene que ser el mismo que transmite el explorador.
hub = PrimeHub(observe_channels=[1])

motor_izq = Motor(Port.A, Direction.COUNTERCLOCKWISE)
motor_der = Motor(Port.B)
robot = DriveBase(motor_izq, motor_der, wheel_diameter=56, axle_track=112)

# Garra: motor que abre/cierra la pinza.
garra = Motor(Port.C)

hub.display.char("R")  # "R" de Recuperador

# --- 1. Esperar la coordenada del explorador ---
objetivo = None
while objetivo is None:
    objetivo = hub.ble.observe(1)  # None si no oye nada hace ~1 segundo
    wait(50)

tx, ty, clase = objetivo
hub.speaker.beep()

# --- 2. Navegar desde el origen hacia (tx, ty) ---
robot.reset()
rumbo = degrees(atan2(ty, tx))     # angulo hacia el objetivo
distancia = sqrt(tx * tx + ty * ty)
robot.turn(rumbo)
robot.straight(distancia)

# --- 3. Recuperar: cerrar la garra ---
hub.display.char("G")
# run_until_stalled cierra la pinza hasta que encuentra resistencia (el objeto).
garra.run_until_stalled(300, duty_limit=50)
hub.speaker.beep(frequency=880, duration=400)

# --- 4. Volver al origen con el objeto ---
robot.straight(-distancia)
robot.turn(-rumbo)
hub.display.char("F")  # "F" de Fin
