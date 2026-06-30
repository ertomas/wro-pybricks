# explorador.py
# ---------------------------------------------------------------------------
# ROBOT EXPLORADOR
#
# Usa el telefono como camara (pagina /deteccion-objeto con Teachable Machine).
# El telefono manda 4 bytes por AppData:  [clase, confianza, cx, area]
#   clase     -> indice de categoria del modelo (0 = primera clase)
#   confianza -> 0..100 (% de certeza)
#   cx        -> 0..100 (centro horizontal del objeto; 50 = centrado)
#   area      -> 0..100 (tamano relativo del objeto = proxi de distancia)
#
# El explorador: (1) busca girando, (2) centra el objeto con la camara,
# (3) se acerca, (4) calcula la posicion (x, y) con su propia odometria y la
# TRANSMITE por BLE al recuperador.
#
# Origen acordado: ambos robots arrancan en (0, 0) mirando hacia +x (0 grados).
# Ajusta wheel_diameter y axle_track segun TU robot (ver challenge 02).
# ---------------------------------------------------------------------------

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction
from pybricks.robotics import DriveBase
from pybricks.messaging import AppData
from pybricks.tools import wait
from umath import sin, cos, radians

# --- Configuracion (ajustar a la mision) ---
CLASE_OBJETIVO = 1     # que clase del modelo buscamos
CONFIANZA_MIN = 70     # % minimo para creerle a la prediccion
CX_CENTRO = 50         # objetivo de centrado (50 = centro de la imagen)
CX_TOLERANCIA = 8      # margen aceptable alrededor del centro
AREA_CERCA = 45        # area a la que consideramos "ya estoy cerca"
OFFSET_OBJETO = 60     # mm extra delante del robot donde esta el objeto

# El canal (1) tiene que ser el mismo que escucha el recuperador.
hub = PrimeHub(broadcast_channel=1)

motor_izq = Motor(Port.A, Direction.COUNTERCLOCKWISE)
motor_der = Motor(Port.B)
robot = DriveBase(motor_izq, motor_der, wheel_diameter=56, axle_track=112)

# Buffer de la camara del telefono: 4 bytes en el modo 0.
app = AppData([(0, 4)])

# --- Pose propia: x, y en mm; el rumbo lo da robot.angle() en grados ---
x = 0.0
y = 0.0
robot.reset()
_d_prev = 0


def actualizar_pose():
    """Integra el avance reciente en la posicion (x, y). Devuelve el rumbo."""
    global x, y, _d_prev
    d = robot.distance()
    rumbo = robot.angle()
    paso = d - _d_prev
    x += paso * cos(radians(rumbo))
    y += paso * sin(radians(rumbo))
    _d_prev = d
    return rumbo


def leer_camara():
    """Devuelve (clase, confianza, cx, area) que manda el telefono."""
    clase, conf, cx, area = app.get_bytes(mode=0)
    return clase, conf, cx, area


# --- 1. Buscar el objeto girando despacio ---
hub.display.char("B")
robot.drive(0, 30)  # girar en el lugar a 30 deg/s
while True:
    clase, conf, cx, area = leer_camara()
    actualizar_pose()
    if clase == CLASE_OBJETIVO and conf >= CONFIANZA_MIN:
        break
    wait(20)
robot.stop()

# --- 2. Centrar el objeto en la camara (centrado visual) ---
hub.display.char("C")
while True:
    clase, conf, cx, area = leer_camara()
    actualizar_pose()
    if clase == CLASE_OBJETIVO and conf >= CONFIANZA_MIN:
        error = cx - CX_CENTRO  # >0 = objeto a la derecha
        if abs(error) <= CX_TOLERANCIA:
            robot.stop()
            break
        robot.drive(0, error * 1.5)  # girar proporcional al error
    else:
        robot.drive(0, 30)  # se perdio: seguir buscando
    wait(20)

# --- 3. Acercarse hasta tener el objeto bien grande (cerca) ---
hub.display.char("A")
while True:
    clase, conf, cx, area = leer_camara()
    actualizar_pose()
    if area >= AREA_CERCA:
        robot.stop()
        break
    error = cx - CX_CENTRO
    robot.drive(120, error * 1.0)  # avanzar corrigiendo el rumbo
    wait(20)

# --- 4. Fijar la posicion del objeto y transmitirla ---
rumbo = actualizar_pose()
# El objeto esta justo delante; sumamos un offset en la direccion del rumbo.
obj_x = int(x + OFFSET_OBJETO * cos(radians(rumbo)))
obj_y = int(y + OFFSET_OBJETO * sin(radians(rumbo)))

hub.display.char("T")
hub.speaker.beep()

# Transmitir varias veces (~5 s) para asegurar que el recuperador lo reciba.
for _ in range(50):
    hub.ble.broadcast((obj_x, obj_y, CLASE_OBJETIVO))
    wait(100)

hub.display.char("F")
