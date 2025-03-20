import oracledb
from decouple import config
import sys




def test_oracle_connection(username, password, host, port, sid):

 

    #Verifica la conexión a una base de datos Oracle 11.2 usando oracledb.


    try:

        # Configuración específica para Oracle 11.2

        oracledb.init_oracle_client()



        # Construir el DSN al estilo antiguo para compatibilidad

        dsn = f"(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST={host})(PORT={port}))(CONNECT_DATA=(SID={sid})))"



        # Intentar conexión

        connection = oracledb.connect(

            user=username,

            password=password,

            dsn=dsn,

        )



        # Verificar versión

        print(f"Conexión exitosa - Versión: {connection.version}")



        # Verificar que podemos ejecutar una consulta simple

        with connection.cursor() as cursor:

           cursor.execute("""
               select * from po_factu
               where rownum <10
               """)
           filas = cursor.fetchall()
        for fila in filas:
            print(fila)

        #connection.commit()
        # cursor.close()

        connection.close()

        return None



    except oracledb.DatabaseError as e:

        return f"Error de base de datos: {str(e)}"

    except Exception as e:

        return f"Error inesperado: {str(e)}"





if __name__ == "__main__":

    # Ejemplo de uso

    config = {

        "username": config("USER"),

        "password": config("PASS"),

        "host": config("HOST"),

        "port": config("PORT"),

        "sid": config("SID")

    }



    error = test_oracle_connection(**config)

    if error:

        print(f"Error de conexión: {error}")

        sys.exit(1)

    else:

        print("Conexión verificada correctamente")
         