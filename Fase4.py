# -*- coding: utf-8 -*-
"""
Software FJ - Sistema integral de gestión de clientes, servicios y reservas (archivo único).
UNAD - Programación  - Fase 4
Juan David Narvaz Arias
Cristian David Moncada
"""

#Libreria para escribir mensajes en un archivo de registro
import logging
# Libreria para trabajar con rutas y carpetas del sistema operativo
import os
# Libreria de expreciones regulares, se usa para validar el formato del correo
import re
# ABC me permite crear clases abstractas; abstactmethod marca metodos que las hijas deben implementar
from abc import ABC, abstractmethod

# ======================================================================
# EXCEPCIONES PERSONALIZADAS
# ======================================================================
"""Excepciones personalizadas del sistema Software FJ."""


class ErrorSoftwareFJ(Exception):
    """Excepción base: todas las excepciones del sistema heredan de ella."""
# Al heredar todas de esta clase, se puede capturar cualquier error del sistema con un solo except


# Se lanza cuando un dato tiene formato o valor incorrecto 
class DatoInvalidoError(ErrorSoftwareFJ):
    """Se recibió un dato con formato o valor incorrecto."""

# Se lanza cuando falta un dato obligatorio 
class ParametroFaltanteError(ErrorSoftwareFJ):
    """Falta un parámetro obligatorio (None o vacío)."""


# Se lanza cuando se intenta una accion que el estado actual no le permite 
class OperacionNoPermitidaError(ErrorSoftwareFJ):
    """La operación no es válida para el estado actual del objeto."""


# Se lanza cuando se reserva un servicio marcado como no disponible 
class ServicioNoDisponibleError(ErrorSoftwareFJ):
    """El servicio solicitado no está disponible."""


# Se lanz cuando una reserva no se puede crear o procesar 
class ReservaInvalidaError(ErrorSoftwareFJ):
    """La reserva no pudo crearse o procesarse correctamente."""


# Se lanza cuando el calculo de costos da un resultado que no tiene sentido 
class CalculoInconsistenteError(ErrorSoftwareFJ):
    """El cálculo de costos produjo un resultado inconsistente."""


# ======================================================================
# REGISTRO DE LOGS
# ======================================================================
"""Configuración del archivo de logs (único uso de archivos del sistema)."""


# El log se guarda junto al código, en la carpeta logs/
RUTA_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "logs", "software_fj.log")


# Funcion que prepara el logger, el objeto que escribe los mensajes en el archivo  
def configurar_logger():
    """Crea (una sola vez) el logger que escribe errores y eventos."""
    # Crea la carpeta logs/ si no existe; exist_ok=True evita el error si ya existe
    os.makedirs(os.path.dirname(RUTA_LOG), exist_ok=True)
    # Crea el logger llamado ''software_fj''
    log = logging.getLogger("software_fj")
    if not log.handlers:  # evita duplicar handlers si se importa varias veces
        log.setLevel(logging.INFO)
        manejador = logging.FileHandler(RUTA_LOG, encoding="utf-8")
        manejador.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s"))
        log.addHandler(manejador)
    return log


logger = configurar_logger()


# ======================================================================
# ENTIDAD BASE Y CLIENTE
# ======================================================================
"""Clase abstracta base y clase Cliente (encapsulación + validaciones)."""




class Entidad(ABC):
    """Clase abstracta que representa cualquier entidad general del sistema."""

    _contador = 0  # contador compartido para generar identificadores únicos

    def __init__(self):
        Entidad._contador += 1
        self._id = Entidad._contador

    @property
    def id(self):
        """Identificador de solo lectura."""
        return self._id

    @abstractmethod
    def describir(self):
        """Cada entidad devuelve su propia descripción (polimorfismo)."""


class Cliente(Entidad):
    """Cliente con datos personales encapsulados y validados."""

    _PATRON_CORREO = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]+$")

    def __init__(self, nombre, correo, telefono):
        # Las asignaciones pasan por los setters, que validan cada dato
        self.nombre = nombre
        self.correo = correo
        self.telefono = telefono
        super().__init__()  # el id solo se genera si los datos son válidos

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        if valor is None or not str(valor).strip():
            raise ParametroFaltanteError("El nombre del cliente es obligatorio.")
        if not isinstance(valor, str) or len(valor.strip()) < 3 \
                or any(c.isdigit() for c in valor):
            raise DatoInvalidoError(f"Nombre inválido: {valor!r}.")
        self._nombre = valor.strip().title()

    @property
    def correo(self):
        return self._correo

    @correo.setter
    def correo(self, valor):
        if valor is None or not str(valor).strip():
            raise ParametroFaltanteError("El correo del cliente es obligatorio.")
        if not self._PATRON_CORREO.match(str(valor).strip()):
            raise DatoInvalidoError(f"Correo inválido: {valor!r}.")
        self._correo = str(valor).strip().lower()

    @property
    def telefono(self):
        return self._telefono

    @telefono.setter
    def telefono(self, valor):
        if valor is None or not str(valor).strip():
            raise ParametroFaltanteError("El teléfono del cliente es obligatorio.")
        digitos = str(valor).replace(" ", "")
        if not digitos.isdigit() or not 7 <= len(digitos) <= 10:
            raise DatoInvalidoError(f"Teléfono inválido: {valor!r}.")
        self._telefono = digitos

    def describir(self):
        return f"Cliente #{self.id}: {self._nombre} <{self._correo}> Tel. {self._telefono}"


# ======================================================================
# SERVICIOS
# ======================================================================
"""Clase abstracta Servicio y tres servicios especializados."""




class Servicio(Entidad, ABC):
    """Servicio genérico: define el contrato que cumplen todos los servicios."""

    def __init__(self, nombre, tarifa_hora, disponible=True):
        if nombre is None or not str(nombre).strip():
            raise ParametroFaltanteError("El nombre del servicio es obligatorio.")
        if isinstance(tarifa_hora, bool) or not isinstance(tarifa_hora, (int, float)) \
                or tarifa_hora <= 0:
            raise DatoInvalidoError(f"Tarifa por hora inválida: {tarifa_hora!r}.")
        self._nombre = str(nombre).strip()
        self._tarifa_hora = float(tarifa_hora)
        self._disponible = bool(disponible)
        super().__init__()

    @property
    def nombre(self):
        return self._nombre

    @property
    def disponible(self):
        return self._disponible

    @disponible.setter
    def disponible(self, valor):
        self._disponible = bool(valor)

    @abstractmethod
    def validar_parametros(self, horas):
        """Valida la duración según las reglas de cada servicio."""

    @abstractmethod
    def calcular_costo_base(self, horas):
        """Costo sin impuestos ni descuentos (cada servicio lo calcula distinto)."""

    def calcular_costo(self, horas, impuesto=0.0, descuento=0.0):
        """
        SOBRECARGA mediante parámetros opcionales:
          calcular_costo(horas)                        -> costo base
          calcular_costo(horas, impuesto)              -> base + impuesto
          calcular_costo(horas, impuesto, descuento)   -> base - descuento + impuesto
        """
        self.validar_parametros(horas)
        if not 0 <= impuesto <= 1:
            raise DatoInvalidoError(f"Impuesto fuera de rango: {impuesto!r}.")
        if not 0 <= descuento <= 0.5:
            raise DatoInvalidoError(f"Descuento fuera de rango (0 a 0.5): {descuento!r}.")
        base = self.calcular_costo_base(horas)
        total = base * (1 - descuento) * (1 + impuesto)
        if total <= 0:
            raise CalculoInconsistenteError(f"Costo no positivo para {self._nombre}.")
        return round(total, 2)


class ReservaSala(Servicio):
    """Reserva de salas por horas, con capacidad máxima."""

    def __init__(self, nombre, tarifa_hora, capacidad, disponible=True):
        if not isinstance(capacidad, int) or capacidad <= 0:
            raise DatoInvalidoError(f"Capacidad inválida: {capacidad!r}.")
        self._capacidad = capacidad
        super().__init__(nombre, tarifa_hora, disponible)

    def validar_parametros(self, horas):
        if not isinstance(horas, (int, float)) or not 1 <= horas <= 8:
            raise DatoInvalidoError("Una sala se reserva entre 1 y 8 horas.")

    def calcular_costo_base(self, horas):
        return self._tarifa_hora * horas

    def describir(self):
        return (f"Sala '{self._nombre}' (capacidad {self._capacidad}) - "
                f"${self._tarifa_hora:,.0f}/hora")


class AlquilerEquipo(Servicio):
    """Alquiler de equipos: tarifa por hora más un depósito fijo."""

    def __init__(self, nombre, tarifa_hora, tipo_equipo, deposito=0, disponible=True):
        if not tipo_equipo or not str(tipo_equipo).strip():
            raise ParametroFaltanteError("El tipo de equipo es obligatorio.")
        if not isinstance(deposito, (int, float)) or deposito < 0:
            raise DatoInvalidoError(f"Depósito inválido: {deposito!r}.")
        self._tipo_equipo = str(tipo_equipo).strip()
        self._deposito = float(deposito)
        super().__init__(nombre, tarifa_hora, disponible)

    def validar_parametros(self, horas):
        if not isinstance(horas, (int, float)) or not 1 <= horas <= 72:
            raise DatoInvalidoError("Un equipo se alquila entre 1 y 72 horas.")

    def calcular_costo_base(self, horas):
        return self._tarifa_hora * horas + self._deposito

    def describir(self):
        return (f"Equipo '{self._nombre}' ({self._tipo_equipo}) - "
                f"${self._tarifa_hora:,.0f}/hora + depósito ${self._deposito:,.0f}")


class AsesoriaEspecializada(Servicio):
    """Asesoría cuyo precio depende del nivel del asesor."""

    _FACTOR_NIVEL = {"junior": 1.0, "senior": 1.5, "experto": 2.0}

    def __init__(self, nombre, tarifa_hora, especialidad, nivel="junior", disponible=True):
        if not especialidad or not str(especialidad).strip():
            raise ParametroFaltanteError("La especialidad es obligatoria.")
        if str(nivel).lower() not in self._FACTOR_NIVEL:
            raise DatoInvalidoError(f"Nivel inválido: {nivel!r}.")
        self._especialidad = str(especialidad).strip()
        self._nivel = str(nivel).lower()
        super().__init__(nombre, tarifa_hora, disponible)

    def validar_parametros(self, horas):
        if not isinstance(horas, (int, float)) or not 1 <= horas <= 6:
            raise DatoInvalidoError("Una asesoría dura entre 1 y 6 horas.")

    def calcular_costo_base(self, horas):
        return self._tarifa_hora * horas * self._FACTOR_NIVEL[self._nivel]

    def describir(self):
        return (f"Asesoría '{self._nombre}' de {self._especialidad} "
                f"(nivel {self._nivel}) - ${self._tarifa_hora:,.0f}/hora")
# ======================================================================
# RESERVA
# ======================================================================
"""Clase Reserva: integra cliente, servicio, duración y estado."""


IMPUESTO_IVA = 0.19


class Reserva(Entidad):
    PENDIENTE = "PENDIENTE"
    CONFIRMADA = "CONFIRMADA"
    CANCELADA = "CANCELADA"
    FALLIDA = "FALLIDA"

    def _init_(self, cliente, servicio, horas):
        if cliente is None or servicio is None or horas is None:
            raise ParametroFaltanteError("Cliente, servicio y duración son obligatorios.")
        if not isinstance(cliente, Cliente) or not isinstance(servicio, Servicio):
            raise ReservaInvalidaError("Cliente o servicio de tipo incorrecto.")
        self._cliente = cliente
        self._servicio = servicio
        self._horas = horas
        self._estado = Reserva.PENDIENTE
        self._costo = None
        super()._init_()

    @property
    def estado(self):
        return self._estado

    @property
    def costo(self):
        return self._costo

    def confirmar(self, descuento=0.0):
        """Confirma la reserva usando try/except/else/finally y encadenamiento."""
        if self._estado != Reserva.PENDIENTE:
            raise OperacionNoPermitidaError(
                f"No se puede confirmar una reserva en estado {self._estado}.")
        try:
            if not self._servicio.disponible:
                raise ServicioNoDisponibleError(
                    f"El servicio '{self._servicio.nombre}' no está disponible.")
            costo = self._servicio.calcular_costo(self._horas, IMPUESTO_IVA, descuento)
        except ErrorSoftwareFJ as causa:
            self._estado = Reserva.FALLIDA
            # Encadenamiento: la causa original queda enlazada con "from"
            raise ReservaInvalidaError(
                f"No se pudo confirmar la reserva #{self.id}.") from causa
        else:
            # Solo se ejecuta si no hubo excepción
            self._costo = costo
            self._estado = Reserva.CONFIRMADA
            logger.info("Reserva #%s confirmada. Costo total: $%s", self.id, f"{costo:,.2f}")
        finally:
            # Se ejecuta siempre, haya o no error
            logger.info("Fin del intento de confirmación de la reserva #%s (estado: %s)",
                        self.id, self._estado)

    def cancelar(self):
        if self._estado in (Reserva.CANCELADA, Reserva.FALLIDA):
            raise OperacionNoPermitidaError(
                f"No se puede cancelar una reserva en estado {self._estado}.")
        self._estado = Reserva.CANCELADA
        logger.info("Reserva #%s cancelada.", self.id)

    def describir(self):
        costo = f"${self._costo:,.2f}" if self._costo is not None else "sin calcular"
        return (f"Reserva #{self.id} [{self._estado}] - {self._cliente.nombre} | "
                f"{self._servicio.nombre} | {self._horas} h | {costo}")


# ======================================================================
# SISTEMA GESTOR
# ======================================================================
"""Gestor central: administra las listas internas y captura los errores."""


TIPOS_SERVICIO = {"sala": ReservaSala, "equipo": AlquilerEquipo,
                  "asesoria": AsesoriaEspecializada}


class SistemaFJ:
    def _init_(self):
        # Listas internas: el sistema no usa base de datos
        self.clientes, self.servicios, self.reservas = [], [], []

    def _ejecutar(self, descripcion, funcion):
        """
        Ejecuta una operación y garantiza que el programa NUNCA se detenga:
        los errores se registran en el log y se informa en pantalla.
        """
        try:
            resultado = funcion()
        except ErrorSoftwareFJ as error:
            causa = f" | causa: {error._cause}" if error.cause_ else ""
            logger.error("%s -> %s: %s%s", descripcion, type(error)._name_, error, causa)
            print(f"  [ERROR] {descripcion}: {error}{causa}")
            return None
        except Exception as error:  # cualquier error inesperado
            logger.critical("%s -> error inesperado %s: %s",
                            descripcion, type(error)._name_, error)
            print(f"  [ERROR INESPERADO] {descripcion}: {error}")
            return None
        else:
            logger.info("%s -> OK", descripcion)
            print(f"  [OK] {descripcion}")
            return resultado
        finally:
            logger.info("Operación finalizada: %s", descripcion)

    def registrar_cliente(self, nombre, correo, telefono):
        def operacion():
            cliente = Cliente(nombre, correo, telefono)
            self.clientes.append(cliente)
            return cliente
        return self._ejecutar(f"Registrar cliente {nombre!r}", operacion)

    def crear_servicio(self, tipo, **datos):
        def operacion():
            clase = TIPOS_SERVICIO.get(tipo)
            if clase is None:
                raise ReservaInvalidaError(f"Tipo de servicio desconocido: {tipo!r}.")
            servicio = clase(**datos)
            self.servicios.append(servicio)
            return servicio
        return self._ejecutar(f"Crear servicio tipo {tipo!r}", operacion)

    def crear_reserva(self, cliente, servicio, horas, descuento=0.0):
        def operacion():
            reserva = Reserva(cliente, servicio, horas)
            self.reservas.append(reserva)
            reserva.confirmar(descuento)
            return reserva
        nombre = getattr(servicio, "nombre", servicio)
        return self._ejecutar(f"Crear reserva de {nombre!r} por {horas} h", operacion)

    def cancelar_reserva(self, reserva):
        return self._ejecutar(
            f"Cancelar reserva #{getattr(reserva, 'id', '?')}", reserva.cancelar)

    def resumen(self):
        print("\n=== RESUMEN FINAL ===")
        print(f"Clientes registrados : {len(self.clientes)}")
        print(f"Servicios creados    : {len(self.servicios)}")
        print(f"Reservas             : {len(self.reservas)}")
        for r in self.reservas:
            print("  -", r.describir())


# ======================================================================
# PROGRAMA PRINCIPAL
# ======================================================================
"""
Software FJ - Sistema integral de gestión de clientes, servicios y reservas.
Simula 12 operaciones (válidas e inválidas) para demostrar que el programa
sigue funcionando ante errores. Los errores quedan en logs/software_fj.log
"""



def main():
    fj = SistemaFJ()

    print("--- Clientes ---")
    ana = fj.registrar_cliente("Ana Torres", "ana.torres@correo.com", "3105551234")   # 1 válido
    luis = fj.registrar_cliente("Luis Pérez", "luis@correo.com", "3201112233")        # 2 válido
    fj.registrar_cliente("Pedro", "correo-sin-arroba", "3001234567")                  # 3 inválido: correo
    fj.registrar_cliente("", "vacio@correo.com", "3001234567")                        # 4 inválido: falta nombre

    print("\n--- Servicios ---")
    sala = fj.crear_servicio("sala", nombre="Sala Innovación", tarifa_hora=80000, capacidad=12)       # 5 válido
    equipo = fj.crear_servicio("equipo", nombre="Proyector 4K", tarifa_hora=15000,
                               tipo_equipo="Proyector", deposito=50000)                               # 6 válido
    asesoria = fj.crear_servicio("asesoria", nombre="Asesoría Python", tarifa_hora=120000,
                                 especialidad="Desarrollo", nivel="senior")                           # 7 válido
    fj.crear_servicio("sala", nombre="Sala Fantasma", tarifa_hora=-5, capacidad=10)                   # 8 inválido: tarifa
    fj.crear_servicio("gimnasio", nombre="Gym")                                                       # 9 inválido: tipo

    print("\n--- Reservas ---")
    r1 = fj.crear_reserva(ana, sala, 3)                      # 10 exitosa
    fj.crear_reserva(luis, equipo, 10, descuento=0.10)       # 11 exitosa con descuento
    fj.crear_reserva(luis, asesoria, 20)                     # 12 fallida: duración inválida
    asesoria.disponible = False
    fj.crear_reserva(ana, asesoria, 2)                       # 13 fallida: servicio no disponible
    fj.crear_reserva(None, sala, 2)                          # 14 fallida: falta cliente
    fj.cancelar_reserva(r1)                                  # 15 cancelación válida
    fj.cancelar_reserva(r1)                                  # 16 cancelación repetida (no permitida)

    print("\n--- Sobrecarga de calcular_costo ---")
    print("  Solo base            :", sala.calcular_costo(2))
    print("  Con impuesto 19%     :", sala.calcular_costo(2, 0.19))
    print("  Con impuesto y desc. :", sala.calcular_costo(2, 0.19, 0.10))

    print("\n--- Polimorfismo: describir() ---")
    for entidad in [ana, sala, equipo, asesoria] + fj.reservas[:1]:
        print("  ", entidad.describir())

    fj.resumen()
    print("\nEl programa terminó sin interrupciones. Revise logs/software_fj.log")


if _name_ == "_main_":
    main()
