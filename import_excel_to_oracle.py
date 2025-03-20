### CREACION FACTURAS PRA ACTICIPOS YEXY #######

import pandas as pd 
import cx_Oracle
from decouple import config
import datetime
#import sys

#sys.modules.clear()
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

proceso_param = 20250201
tipo_giro_param = 'GD_RS'


# Inicializa el cliente Oracle
cx_Oracle.init_oracle_client(lib_dir=r"C:\instantclient_12_2")

def main():
    # Lee los datos de Excel
    nuevo_archivo = r'C:\Users\jhon.chicangana\Documents\RECURSOS_VSC\FACTURAS_CAPITA_PGP_GD-RS.xlsx'
    df = pd.read_excel(nuevo_archivo, engine='openpyxl')
    df = df.where(pd.notnull(df), None)
    print(df)
    # Conexión a la base de datos
    dsn_tns = cx_Oracle.makedsn(config('HOST'), config('PORT'), config('SID'))
    conn = cx_Oracle.connect(config('USER'), config('PASS'), dsn_tns)

    # Crea un cursor
    cursor = conn.cursor()

    # Inserta datos en la tabla
    for index, row in df.iterrows():
        sql = """
            INSERT INTO tmp_facturas_yexy 
            (DEPARTAMENTO, MUNICIPIO, NIT, FECHA_EMISION_FACTURA, CONTRATO, VALOR_FACTURA_GIRO, FORMA_CONTRATACION, CODIGO_ENTIDAD_TERRITORIAL, TIPO_GIRO, PROCESO) 
            VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10)
        """
        cursor.execute(sql, (row['DEPARTAMENTO'], row['MUNICIPIO'], row['NIT'], row['FECHA_EMISION_FACTURA'], row['CONTRATO'], row['VALOR_FACTURA_GIRO'], row['FORMA_CONTRATACION'], row['CODIGO_ENTIDAD_TERRITORIAL'], row['TIPO_GIRO'], row['PROCESO']))

    # Confirma los cambios
    conn.commit()
    
    # Verifica que las filas se hayan insertado correctamente
    cursor.execute("SELECT COUNT(*) FROM tmp_facturas_yexy")
    total_rows = cursor.fetchone()[0]
    print(f"Total de filas insertadas en tmp_facturas_yexy : {total_rows}")

    # Consulta para buscar duplicados VALIDAR REGIMEN Y PROCESO 
    ejecutar_duplicados_sql = """
    SELECT NIT, CONTRATO, FACTURA_PROVEEDOR
    FROM (
        SELECT NIT, CONTRATO, FACTURA_PROVEEDOR,
               ROW_NUMBER() OVER (PARTITION BY NIT, CONTRATO, FACTURA_PROVEEDOR ORDER BY NIT ASC) AS RN
        FROM (
            SELECT PROCESO, PV.PVD_CODA AS NIT, FA.CONTRATO, FA.DEPARTAMENTO,
                   TO_CHAR(SYSDATE, 'YYMMDD') || '-' || SUBSTR(CONTRATO, 0, 3) || 
                   TRIM(REGEXP_REPLACE(REGEXP_SUBSTR(CONTRATO, '[^ ]+', 1, 1), '[^0-9]+', '')) ||
                   LPAD(CODIGO_ENTIDAD_TERRITORIAL, 5, 0) AS FACTURA_PROVEEDOR,
                   CASE WHEN FORMA_CONTRATACION = 1 THEN 'CAPITA'
                        WHEN FORMA_CONTRATACION = 2 THEN 'PGP'
                   END || ' ' || SUBSTR(TO_CHAR(FECHA_EMISION_FACTURA, 'MONTH'), 0, 3) || 
                   TO_CHAR(FECHA_EMISION_FACTURA, 'YY') || ' - ' || FA.DEPARTAMENTO || ' - ' || CONTRATO || ' - ' || TIPO_GIRO AS DESCRIPCION,
                   CODIGO_ENTIDAD_TERRITORIAL
            FROM tmp_facturas_yexy  FA
            INNER JOIN PO_PVDOR PV ON TO_CHAR(FA.NIT) = PV.PVD_CODA
            WHERE FA.PROCESO = :1
            AND TIPO_GIRO = :2
            
        )
    )
    WHERE RN > 1
    """
     
    cursor.execute(ejecutar_duplicados_sql, [proceso_param, tipo_giro_param])
    resultados = cursor.fetchall()
    print("DUPLICADOS:")
    if resultados:
        for fila in resultados:
            print(fila)

    # eliminar duplicados 
    #Elimina los duplicados dejando solo el primero
        eliminar_duplicados_sql = """
        
        
        DELETE FROM tmp_facturas_yexy
            WHERE ROWID IN (
            SELECT rid FROM (
                SELECT ROWID AS rid,
                    ROW_NUMBER() OVER (
                        PARTITION BY 
                            DEPARTAMENTO, MUNICIPIO, NIT, 
                            FECHA_EMISION_FACTURA, CONTRATO, 
                            VALOR_FACTURA_GIRO, FORMA_CONTRATACION, 
                            CODIGO_ENTIDAD_TERRITORIAL, TIPO_GIRO, 
                            PROCESO 
                        ORDER BY ROWID  -- Elige el criterio de orden que prefieras
                    ) AS RN
                FROM tmp_facturas_yexy
            )
            WHERE RN > 1 -- Esto selecciona solo los duplicados
        )
            """
        cursor.execute(eliminar_duplicados_sql)
        conn.commit()
        print("Duplicados eliminados.")
    else:
        print("No se encontraron duplicados.")
    # Cierra el cursor y la conexión
    
    ### ACTUALIZA A.FACTURA_GENERADA 
    try:    
        ejecutar_update_sql ='''UPDATE tmp_facturas_yexy A
        SET A.FACTURA_GENERADA = (
                            SELECT FACTURA_PROVEEDOR
                            FROM
                            (
                                SELECT PROCESO,
                                       PV.PVD_CODA AS NIT,
                                       FA.CONTRATO,
                                       FA.DEPARTAMENTO,
                                       TO_CHAR(SYSDATE, 'YYMMDD')||'-'||       
                                       SUBSTR(CONTRATO, 0,3)||TRIM(REGEXP_REPLACE(REGEXP_SUBSTR(CONTRATO, '[^ ]+', 1, 1), '[^0-9]+','' ))||
                                       LPAD( CODIGO_ENTIDAD_TERRITORIAL, 5, 0) AS FACTURA_PROVEEDOR,       
                                       CASE 
                                            WHEN FORMA_CONTRATACION = 1 THEN 'CAPITA'
                                            WHEN FORMA_CONTRATACION = 2 THEN 'PGP'
                                       END||' '||SUBSTR(TO_CHAR(FECHA_EMISION_FACTURA, 'MONTH'), 0,3)||TO_CHAR(FECHA_EMISION_FACTURA, 'YY')||' - '||FA.DEPARTAMENTO||' - '||CONTRATO||' - '||TIPO_GIRO AS DESCRIPCION,
                                       CODIGO_ENTIDAD_TERRITORIAL
                                FROM tmp_facturas_yexy FA
                                INNER JOIN PO_PVDOR PV ON TO_CHAR(FA.NIT) = PV.PVD_CODA
                                WHERE FA.PROCESO = :1
                                AND   FA.TIPO_GIRO = :2
                                AND   FACTURA_GENERADA IS NULL
                              
                            ) B
                            WHERE A.PROCESO = B.PROCESO
                            AND   A.NIT = B.NIT
                            AND   A.DEPARTAMENTO = B.DEPARTAMENTO
                            AND   A.CONTRATO = B.CONTRATO
                            AND   A.CODIGO_ENTIDAD_TERRITORIAL = B.CODIGO_ENTIDAD_TERRITORIAL
        )
        WHERE A.PROCESO = :1
        AND   A.TIPO_GIRO = :2
        AND   FACTURA_GENERADA IS NULL
        '''
        cursor.execute(ejecutar_update_sql, [proceso_param, tipo_giro_param])
        conn.commit()
        print("datos actualizados FACTURA_GENERADA")   
    except Exception as e:
        print(f"Ocurrió un error: {e}")
        conn.rollback()
    
    ###  ACTUALIZA DESCRIPICON_FACTURA 
    try:
        ejecutar_update_sql ='''UPDATE tmp_facturas_yexy  A
            SET  A.DESCRIPICON_FACTURA = ( 
                                    SELECT CASE 
                                                WHEN FORMA_CONTRATACION = 1 THEN 'CAPITA'
                                                WHEN FORMA_CONTRATACION = 2 THEN 'PGP'
                                        END||' '||SUBSTR(TO_CHAR(FECHA_EMISION_FACTURA, 'MONTH'), 0,3)||TO_CHAR(FECHA_EMISION_FACTURA, 'YY')||' - '||DEPARTAMENTO||' - '||CONTRATO||' - '||TIPO_GIRO
                                    FROM tmp_facturas_yexy B
                                    WHERE A.FACTURA_GENERADA = B.FACTURA_GENERADA
                                    AND   B.PROCESO = :1
                                    AND   B.TIPO_GIRO = :2
                                    AND   DESCRIPICON_FACTURA IS NULL
                                )
                                WHERE A.PROCESO = :1
                                AND   A.TIPO_GIRO = :2
                                AND   DESCRIPICON_FACTURA IS NULL
        '''
        cursor.execute(ejecutar_update_sql, [proceso_param, tipo_giro_param])
        conn.commit()
        print("datos actualizados DESCRIPICON_FACTURA")    
    except Exception as e:
        print(f"Ocurrió un error: {e}")
        conn.rollback() 
     
     
    try:    
        export_query = '''
SELECT NIT,
       PV.PVR_NOCO AS PRESTADOR,
       CASE WHEN FORMA_CONTRATACION = 1 THEN 'CAPITA' ELSE 'PGP' END AS FORMA_CONTRATACION,
       CONTRATO,
       DEPARTAMENTO,
       CODIGO_ENTIDAD_TERRITORIAL,
       FACTURA_GENERADA,
       VALOR_FACTURA_GIRO AS VALOR_AUTORIZADO,
       DESCRIPICON_FACTURA
FROM tmp_facturas_yexy TMP
INNER JOIN PO_PVDOR PV ON TMP.NIT = PV.PVD_CODA
WHERE PROCESO = :1
AND   TIPO_GIRO = :2
'''

    
    # Ejecutar la consulta
        cursor.execute(export_query, [proceso_param, tipo_giro_param])

        # Obtener resultados
        columns = [col[0] for col in cursor.description]
        data = cursor.fetchall()

        # Convertir los resultados en un DataFrame de pandas
        df = pd.DataFrame(data, columns=columns)

        # Exportar a un archivo Excel
        output_file = rf"C:\Users\GASAN\Documents\PROYECTO_PYTHON_GF\export\facturas_{timestamp}.xlsx"
        df.to_excel(output_file, index=False)

        print(f"Exportación completada. Archivo guardado como: {output_file}")
        
    except cx_Oracle.DatabaseError as e:
        print("Error al ejecutar el script:", e)
           
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()