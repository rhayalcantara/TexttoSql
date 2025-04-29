## Reglas para la Generacion de Consulta en Mysql Aurora Aws
0-  la mas importante todas las consulta seran para mysql solo usa fuciones de mysql
1-  Siempre los nombre de tablas estaran rodeados de el caracter `
    ejemplo: SQL``` select * from `FBS_NOMINAS.EMPLEADO` ``` este es un buen ejemplo de como debes realizar la consulta
    ejemplo de como no debes realizar la consulta: SQL``` select * from FBS_NOMINAS.EMPLEADO ```, aqui otro ejemplo de como
    no debes realizar la consulta SQL``` select * from `FBS_NOMINAS`.`EMPLEADO` ``` asi que evitas estas dos forma y utiliza
    el primer ejemplo por favor
2-  Se considera socio al cliente que tiene una cuenta activa de Aportes
3-  Se considera socio activo para la gerencia general aquel que ha tenido movimiento al menos en los ultimos dos años
4-  Se considera Cartera activa para los prestamos que cumpla con el siguiente criterio:    CODIGOESTADOPRESTAMO NOT IN ('G','Z')
    explicacion del criterio: los codigo de estado prestamo G:Castigados y Z:Total Cobrado o Terminados no se incluyen en la cartera activa
    una consulta basica de prestamo activos seria: SQL``` select NUMEROPRESTAMO,SALDOACTUAL FROM `FBS_CARTERA.PRESTAMOMAESTRO` ```
5- Se considera Empleado activo a los empleado que en el campo codigoestado es igual a 'A'
6- La tabla que tiene la oficina,el departamentos de los empleados es FBS_NOMINA.EMPLEADO_COMPLEMENTO el campo para la oficina es SECUENCIALOFICINA y para el departamento es SECUENCIALDEPARTAMENTO
7- Los nombre de las oficina (Sucursal) se consiguen en la tabla FBS_GENERALES.DIVISION y el nombre se obtiene del campo NOMBRE, las tablas realacionadas tiene el campo secuencialoficina
8- el sexo de una persona esta en la tabla FBS_PERSONAS.PERSONA_NATURAL y el campo sexo es el campo ESMASCULINO que cuando es masculino es true y cuando es femenino es false
se relaciona con la tabla FBS_PERSONAS.PERSONA por el campo SECUENCIALPERSONA 
no todas las personas aparecen en esta tabla ya que las empresas estan en persona pero no estan en FBS_PERSONAS.PERSONA_NATURAL si no que estan en FBS_PERSONAS.ORGANIZACION
9- La tabla de FBS_CARTERA.PRESTAMOMAESTRO se relaciona con FBS_PERSONAS.PERSONA atraves de FBS_CLIENTES.CLIENTE  primero se hace un inner join con el campo SECUENCIALCLIENTEPRINCIPAL con el SECUENCIAL de cliente luego haces un inner join con FBS_PERSONAS.PERSONA con el SECUENCIALPERSONA de la tabla FBS_CLIENTES.CLIENTE
con el campo SECUENCIAL DE FBS_PERSONAS.PERSONA 
10- los prestamo se consideran desembolsado o formalizados cuando en la tabla FBS_CARTERA.PRESTAMOMAESTRO el campo FECHAADJUDICACION no es nula
11- se considera que un prestamo no ha pagado la primera cuota cuando pasado 30 dias de su fecha de adjudicioncion el saldoactual y deudainicial son iguales en la tabla 
FBS_CARTERA.PRESTAMOMAESTRO
12- cuando se pide el monto desembolsado el campo a trabajar es el de DEUDAINICIAL