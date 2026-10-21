import os
from datetime import datetime
from getpass import getpass

from conexion import conexiondb
from modelos import (Administrador, Gerente, EmpleadoComun, Departamento, Proyecto,
                     RegistroEmpleados, Credenciales, PDF, Excel)

# Lectura de datos con validacion .
def leer_entero(mensaje):
    while True:
        try:
            return int(input(mensaje))
        except ValueError:
            print(" Debes ingresar un numero entero.")

def leer_fecha(mensaje):
    while True:
        try:
            return datetime.strptime(input(mensaje + " (AAAA-MM-DD): "), "%Y-%m-%d")
        except ValueError:
            print("--Fecha invalida.--")

def pedir_empleado(tipo):
#Pide los datos y crea el objeto. Si un setter falla (ValueError),vuelve a pedir.
    while True:
        try:
            datos = (None, input("Nombre: "), input("Direccion: "), input("Fono: "),
                     input("Email: "), leer_fecha("Inicio de contrato:"),
                     leer_entero("Salario: "), input("RUT (12345678-9): "))
            if tipo == "1":
                return Administrador(*datos)
            if tipo == "2":
                return Gerente(*datos, dep_asignado=leer_entero("Numero de depto que dirige: "))
            return EmpleadoComun(*datos, area_de_trabajo=input("Area de trabajo: "))
        except ValueError as error:
            print(f" Dato invalido: {error}. Intenta de nuevo.")

def registrar_empleado(registro):
    tipo = input("Tipo (1=Administrador, 2=Gerente, 3=Empleado comun): ")
    if tipo not in ("1", "2", "3"):
        print("--Tipo no valido.--")
        return
    empleado = pedir_empleado(tipo)
    usuario = input("Usuario de acceso: ")
    clave = getpass("clave (min. 6 caracteres): ")
    if len(clave) < 6:
        print("--La clave es muy corta.--")
        return
    registro.registrar_empleado(empleado, usuario, clave)
    print(f"Empleado registrado con ID {empleado.id_empleado}")

def listar_empleados(registro):
    empleados = registro.listar()
    for emp in empleados:
        print(" ", emp)
    print(f"Total: {registro.total_empleados}.")

def buscar_empleado(registro):
    emp = registro.buscar_empleado(leer_entero("ID del empleado: "))
    print(" ", emp if emp else "No existe ese empleado.")

def actualizar_empleado(registro):
    emp = registro.buscar_empleado(leer_entero("ID del empleado: "))
    if emp is None:
        print("  No existe ese empleado.")
        return
    print("  (Enter para dejar el valor actual)")
    try:
        emp.nombre = input(f"Nombre [{emp.nombre}]: ") or emp.nombre
        emp.direccion = input(f"Direccion [{emp.direccion}]: ") or emp.direccion
        emp.fono = input(f"Fono [{emp.fono}]: ") or emp.fono
        emp.email = input(f"Email [{emp.email}]: ") or emp.email
        sueldo = input(f"Salario [{emp.salario}]: ")
        emp.salario = int(sueldo) if sueldo else emp.salario
        registro.actualizar_empleado(emp)
        print("  Empleado actualizado.")
    except ValueError as error:
        print(f"--No se actualizan: {error}--")

def eliminar_empleado(registro):
    id_emp = leer_entero("ID del empleado a eliminar: ")
    if input("Esta Seguro? (s/n): ").lower() == "s":
        registro.dar_de_baja_empleado(id_emp)
        print("--Empleado eliminado.--")


def menu_departamentos(bd):
    print(" 1) Crear  2) Listar  3) Editar  4) Eliminar  5) Asignar empleado")
    op = input("Opcion: ")
    if op == "1":
        try:
            dep = Departamento(None, input("Nombre: "), input("Gerente asociado: "), input("Tipo: "))
        except ValueError as error:
            print(f"--{error}--")
            return
        dep.crear_dep(bd)
        print(f"  Departamento creado con Num {dep.num_dep}")
    elif op == "2":
        for dep in bd.listar_departamentos():
            print(" ", dep)
    elif op == "3":
        dep = Departamento.buscar_dep(bd, leer_entero("Num de departamento: "))
        if dep is None:
            print("-- No existe.--")
            return
        dep.nombre_dep = input(f"Nombre [{dep.nombre_dep}]: ") or dep.nombre_dep
        dep.gerente_asociado = input(f"Gerente [{dep.gerente_asociado}]: ") or dep.gerente_asociado
        dep.tipo_dep = input(f"Tipo [{dep.tipo_dep}]: ") or dep.tipo_dep
        dep.editar_dep(bd)
        print("Departamento actualizado.")
    elif op == "4":
        dep = Departamento.buscar_dep(bd, leer_entero("Num de departamento: "))
        if dep is None:
            print("--No existe.--")
            return
        dep.eliminar_dep(bd)
        print("  Departamento eliminado.")
    elif op == "5":
        emp = bd.buscar_empleado(leer_entero("ID del empleado: "))
        dep = Departamento.buscar_dep(bd, leer_entero("Num de departamento: "))
        if emp is None or dep is None:
            print("--El empleado o el departamento no existe.--")
            return
        Administrador(0, "Admin Temporal", "-", "-", "a@a.cl", datetime.now(), 1, "1-1").asignar_dep(emp, dep)   #(UML)
        bd.asignar_departamento(emp.id_empleado, dep.num_dep)   # y se guarda en la BD
        print(f"El {emp.nombre} ahora esta en {dep.nombre_dep}.")

def iniciar_sesion(bd):
    usuario = input("Usuario: ")
    clave = getpass("Clave: ")
    fila = bd.obtener_credenciales(usuario)
    if fila:
        creden = Credenciales(usuario)
        creden.cargar_hash(fila[1])
        if creden.iniciar_sesion(usuario, clave):
            print(f"Bienvenido, {bd.buscar_empleado(int(fila[0])).nombre}.")
            return
    print("Usuario o clave incorrectos.")

def generar_informe(registro):
    admin = Administrador(0, "Admin Temporal", "-", "-", "a@a.cl", datetime.now(), 1, "1-1")
    informe = PDF("Listado de empleados") if input("1=PDF 2=Excel: ") == "1" else Excel("Listado de empleados")
    filas = [[e.id_empleado, e.nombre, e.rut, e.tipo(), e.salario] for e in registro.listar()]
    print(admin.redactar_informe(informe, ["ID", "Nombre", "RUT", "Rol", "Salario"], filas))
    ruta = informe.exportar_como("informe_empleados")  

# Main (Programa principal)

def main():
    print("=== EcoTech Solutions - Gestion de Empleados ===")
    usuario = 
    clave = 
    bd =
    registro = RegistroEmpleados(bd)
    opciones = {"1": lambda: registrar_empleado(registro), 
                "2": lambda: listar_empleados(registro),
                "3": lambda: buscar_empleado(registro), 
                "4": lambda: actualizar_empleado(registro),
                "5": lambda: eliminar_empleado(registro), 
                "6": lambda: menu_departamentos(bd),
                "7": lambda: iniciar_sesion(bd),
                "8": lambda: generar_informe(registro),
                }

    while True:
        print("\n1) Registrar empleado  2) Listar  3) Buscar  4) Actualizar  5) Eliminar"
              "\n6) Departamentos  7) Iniciar sesion  8) Informe  0) Salir")
        opcion = input("Opcion: ").strip()
        if opcion == "0":
            break
        if opcion not in opciones:
            print("--Opcion no valida.--")
            continue
        try:
            opciones[opcion]()
        except (ValueError, RuntimeError, ConnectionError) as error:
            print(f"--Error: {error}--")
        except OSError as error:
            print(f"-No se pudo escribir el archivo: {error}")
        except Exception as error:               # que el programa nunca se caiga
            print(f"--Error inesperado: {error}--")
    print("Hasta luego.")

if __name__ == "__main__":
    main()



