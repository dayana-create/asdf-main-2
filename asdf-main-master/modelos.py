from abc import ABC, abstractmethod
from datetime import datetime

import bcrypt

class Empleado():
    def __init__(self, id_empleado, nombre, direccion, fono, email, f_inicio_contrato,
                 salario, rut):
        self.id_empleado = id_empleado
        self.nombre = nombre
        self.direccion = direccion
        self.fono = fono
        self.email = email
        self.f_inicio_contrato = f_inicio_contrato
        self.salario = salario
        self.rut = rut
        self._credenciales = None             
        self._departamento = None                  
        self._proyectos = []
        self._registros = []
#-------------------------------------------------------------------
class Credenciales:
    def __init__(self, usuario):
        self.__usuario = usuario
        self.__salt = None
        self.__hash_contrasena = None

    def validar_contrasena(self, contrasena):
        return bcrypt.checkpw(contrasena.encode(), self.__hash_contrasena)
#--------------------------------------------------------------------------
class Departamento:
    def __init__(self, num_dep, nombre_dep, gerente_asociado, tipo_dep):
        self.num_dep = num_dep
        self.nombre_dep = nombre_dep
        self.gerente_asociado = gerente_asociado
        self.tipo_dep = tipo_dep
        self.__empleados = [] 

#-----------------------------------------------------------------------------
class Proyecto:
    def __init__(self, nombre_proyecto, descripcion, fecha_inicio):
        self.nombre_proyecto = nombre_proyecto
        self.descripcion = descripcion
        self.fecha_inicio = fecha_inicio
        self.__empleados = []   
#--------------------------------------------------------------------------
class RegistroTiempo:
    def __init__(self, fecha, horas_trabajadas, descr_tareas):
        self.fecha = fecha
        self.horas_trabajadas = horas_trabajadas
        self.descr_tareas = descr_tareas
        self.__aprobado = False

    @property
    def horas_trabajadas(self):
        return self.__horas

    @horas_trabajadas.setter
    def horas_trabajadas(self, valor):
        if not 0 < valor <= 24:
            raise ValueError("Las horas deben estar entre 0 y 24.")
        self.__horas = valor

    @property
    def aprobado(self):
        return self.__aprobado

    def registrar_horas(self):
        return f"{self.horas_trabajadas} hrs registradas el {self.fecha:%Y-%m-%d}"

    def agregar_comentario(self, comentario):
        self.descr_tareas += f" | {comentario}"

    def aprobar(self):
        self.__aprobado = True

    def __str__(self):
        estado = "aprobado" if self.__aprobado else "pendiente"
        return f"{self.fecha:%Y-%m-%d} - {self.horas_trabajadas} h - {self.descr_tareas} ({estado})"
#--------------------------------------------------------------------------------------

class administrador:
    def __init__(self, *datos, nivel_de_permisos="TOTAL"):
        super().__init__(*datos)
        self.nivel_de_permisos = nivel_de_permisos

    def tipo(self):
        return "ADMINISTRADOR"

    def asignar_dep(self, empleado, departamento):
        departamento.asig_dep_empleado(empleado)

    def des_asignar_dep(self, empleado):
        if empleado.departamento:
            empleado.departamento.rem_dep_empleado(empleado)

    def redactar_informe(self, informe, encabezados, filas):
        informe.recopilar(encabezados, filas)
        return informe.generar_informe()

    def anular_contrato(self, empleado, registro):
        registro.dar_de_baja_empleado(empleado.id_empleado)
#----------------------------------------------------------------------------------
class Gerente(Empleado):
    def __init__(self, *datos, dep_asignado=None):
        super().__init__(*datos)
        self.dep_asignado = dep_asignado

    def tipo(self):
        return "GERENTE"

    def calcular_remu(self):
        return round(self.salario * 1.10)     # salario + 10 % de bono

    def mostrar_datos(self):                  # polimorfismo
        return super().mostrar_datos() + f" | Dep. a cargo: {self.dep_asignado}"
#-------------------------------------------------------------------------
class EmpleadoComun(Empleado):
    def __init__(self, *datos, area_de_trabajo="General"):
        super().__init__(*datos)
        self.area_de_trabajo = area_de_trabajo

    def tipo(self):
        return "COMUN"

    def registrar_hrs_trabajadas(self, fecha, horas, descripcion):
        registro = RegistroTiempo(fecha, horas, descripcion)
        self.registros.append(registro)
        return registro

    def consultar_proy_asig(self):
        return self.proyectos

    def enviar_renuncia(self):
        return f"{self.nombre} envio su carta de renuncia."

    def mostrar_datos(self):
        return super().mostrar_datos() + f" | Area: {self.area_de_trabajo}"
#--------------------------------------------------------------------------------
class RegistroEmpleados:
    def __init__(self, bd):
        self.__bd = bd
        self.lista_empleados = []
        self.fecha_ultima_mod = None

    @property
    def total_empleados(self):
        return len(self.lista_empleados)

    def _actualizar_lista(self):
        self.lista_empleados = self.__bd.listar_empleados()
        self.fecha_ultima_mod = datetime.now()

    def registrar_empleado(self, empleado, usuario, contrasena):
        creden = Credenciales(usuario)
        creden.aplicar_salt()
        creden.aplicar_bcrypt(contrasena)
        empleado.credenciales = creden
        empleado.id_empleado = self.__bd.crear_empleado(empleado)
        self._actualizar_lista()

    def dar_de_baja_empleado(self, id_empleado):
        self.__bd.eliminar_empleado(id_empleado)
        self._actualizar_lista()

    def buscar_empleado(self, id_empleado):
        return self.__bd.buscar_empleado(id_empleado)

    def actualizar_empleado(self, empleado):
        self.__bd.actualizar_empleado(empleado)
        self._actualizar_lista()

    def listar(self):
        self._actualizar_lista()
        return self.lista_empleados
#----------------------------------------------------------------------------------------
class Informe(ABC):
    def __init__(self, descripcion, tipo_de_documento):
        self.descripcion = descripcion
        self.tipo_de_documento = tipo_de_documento
        self.encabezados = []
        self.filas = []

    @property
    def numero_hojas(self):
        return max(1, -(-len(self.filas) // 40))

    def recopilar(self, encabezados, filas):
        self.encabezados = encabezados
        self.filas = filas

    def generar_informe(self):
        lineas = [self.descripcion, " | ".join(map(str, self.encabezados))]
        lineas += [" | ".join(map(str, fila)) for fila in self.filas]
        return "\n".join(lineas)

    @abstractmethod
    def exportar_como(self, nombre):
        """Cada tipo de informe lo exporta a su manera."""
#--------------------------------------------------------------------------------
class PDF(Informe):
    def __init__(self, descripcion):
        super().__init__(descripcion, "PDF")

    def exportar_como(self, nombre):
        ruta = nombre + ".txt"                   # versión de texto (ver README)
        with open(ruta, "w", encoding="utf-8") as archivo:
            archivo.write(self.generar_informe())
        return ruta

    def enviar_impresora(self):
        return "Enviando PDF a la impresora... (simulado)"
#--------------------------------------------------------------------------------------
class Excel(Informe):
    def __init__(self, descripcion):
        super().__init__(descripcion, "Excel")

    def exportar_como(self, nombre):
        ruta = nombre + ".csv"                   # Excel abre archivos CSV
        with open(ruta, "w", encoding="utf-8-sig") as archivo:
            archivo.write(";".join(map(str, self.encabezados)) + "\n")
            for fila in self.filas:
                archivo.write(";".join(map(str, fila)) + "\n")
        return ruta

    def enviar_impresora(self):
        return "Enviando Excel a la impresora... (simulado)"

        