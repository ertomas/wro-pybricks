from pybricks.hubs import PrimeHub
from pybricks.messaging import AppData
from pybricks.tools import wait

hub = PrimeHub()

# 3 bytes en el modo 0: tono (0-179), saturacion (0-100), brillo (0-100)
app = AppData([(0, 3)])

def nombre_color(h, s, v):
    hue = h * 2  # el telefono manda el tono dividido en 2
    if v < 15:
        return "negro"
    if s < 25:
        return "blanco" if v > 60 else "gris"
    if hue < 20 or hue >= 340:
        return "rojo"
    if hue < 45:
        return "naranja"
    if hue < 70:
        return "amarillo"
    if hue < 170:
        return "verde"
    if hue < 255:
        return "azul"
    if hue < 290:
        return "violeta"
    return "rosa"

while True:
    h, s, v = app.get_bytes(mode=0)
    color = nombre_color(h, s, v)
    hub.display.text(color[0].upper())
    print(color, "  H", h * 2, "S", s, "V", v)
    wait(100)
