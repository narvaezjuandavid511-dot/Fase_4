# -*- coding: utf-8 -*-
"""
Software FJ - Sistema integral de gestión de clientes, servicios y reservas (archivo único).
UNAD - Programación 213023 - Fase 4
"""

import logging
import os
import re
from abc import ABC, abstractmethod

# ======================================================================
# EXCEPCIONES PERSONALIZADAS
# ======================================================================
"""Excepciones personalizadas del sistema Software FJ."""


class ErrorSoftwareFJ(Exception):
    """Excepción base: todas las excepciones del sistema heredan de ella."""


class DatoInvalidoError(ErrorSoftwareFJ):
    """Se recibió un dato con formato o valor incorrecto."""


class ParametroFaltanteError(ErrorSoftwareFJ):
    """Falta un parámetro obligatorio (None o vacío)."""


class OperacionNoPermitidaError(ErrorSoftwareFJ):
    """La operación no es válida para el estado actual del objeto."""


class ServicioNoDisponibleError(ErrorSoftwareFJ):
    """El servicio solicitado no está disponible."""


class ReservaInvalidaError(ErrorSoftwareFJ):
    """La reserva no pudo crearse o procesarse correctamente."""


class CalculoInconsistenteError(ErrorSoftwareFJ):
    """El cálculo de costos produjo un resultado inconsistente."""


# ======================================================================
# REGISTRO DE LOGS
# ======================================================================
"""Configuración del archivo de logs (único uso de archivos del sistema)."""


# El log se guarda junto al código, en la carpeta logs/
RUTA_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "logs", "software_fj.log")


def configurar_logger():
    """Crea (una sola vez) el logger que escribe errores y eventos."""
    os.makedirs(os.path.dirname(RUTA_LOG), exist_ok=True)
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
