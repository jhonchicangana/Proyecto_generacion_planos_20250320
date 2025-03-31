import oracledb
from decouple import config
import datetime
import pandas as pd

 # --- validar el estado cxp_esta ya que pueden estar en estado A , luego revisar en po_corpa con top_codi y cor_nume en 213 

 
 
def process_file(fecha_pago_param, fecha_aut_param,top_codi_param):
    """
    Procesa el archivo subido, ejecuta las consultas y genera el archivo Excel de resultados.
    """
    
    if not fecha_pago_param or not fecha_aut_param or not top_codi_param :
        return None, "❌ Todos los parámetros deben estar definidos."
    
    top_codi_param_str = ",".join(str(x) for x in top_codi_param.split(","))  
    resultado_validacion = validacion(fecha_aut_param, top_codi_param_str)
    
    resultado_validacion = validacion(fecha_aut_param, top_codi_param_str)
    if isinstance(resultado_validacion, str) and "❌" in resultado_validacion:
        return None, resultado_validacion  # No conviertas a int, solo retorna el error
    elif resultado_validacion is None:
        return None, "❌ No se encontraron datos en la validación."
    
    
    top_codi_param_str = ",".join(str(x) for x in top_codi_param.split(","))   
    resultado = insert_gearp_data(fecha_pago_param, fecha_aut_param, top_codi_param_str)
  
    
     # Paso 2: Actualizar GEA_CONT en PO_CXPAG_PLANOS
    resultado_update = update_gea_cont(fecha_aut_param, top_codi_param_str)
    top_codi_param_str = ",".join(str(x) for x in top_codi_param.split(","))   
    if "❌" in resultado_update or "⚠️" in resultado_update:
        return None, resultado_update  # Si hubo error en la actualización, detener ejecución
    
    
   # if "❌" in resultado:  # Si hubo error en la ejecución
    #    return None, resultado

    # Exportar resultados a Excel
    output_file, error = export_plano(fecha_pago_param)

    if error:
        return None, error

    return output_file, None
 
 
  
def test_oracle_connection():
    #oracledb.init_oracle_client(lib_dir=r"C:\instantclient_12_2") 
    """Establece la conexión con Oracle."""   
    try:
        #oracledb.init_oracle_client(lib_dir=r"C:\instantclient_12_2") 
        dsn = f"(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST={config('HOST')})(PORT={config('PORT')}))(CONNECT_DATA=(SID={config('SID')})))"
        connection = oracledb.connect(user=config("USER"), password=config("PASS"), dsn=dsn)
        print("✅ Conexión exitosa a la base de datos.")
        return connection
    except oracledb.DatabaseError as e:
        print(f"❌ Error de conexión a la base de datos: {e}")
        return None
       

def validacion(fecha_aut_param, top_codi_param_str):
    connection = test_oracle_connection()
    if not connection:
        return "❌ Error de conexión a la base de datos."

    cursor = None
    try:
        cursor = connection.cursor()
        #top_codi_list = list(map(int, top_codi_param_str.split(",")))
        top_codi_list = [int(x) for x in top_codi_param_str.split(",")]
        top_codi_placeholders = ', '.join([':top_codi' + str(i) for i in range(len(top_codi_list))])
        
        validacion_total = f'''SELECT SUM(CX.CXP_SALD)
FROM PO_CORPA CO
INNER JOIN PO_DECOR DE ON CO.COR_CONT = DE.COR_CONT AND CO.EMP_CODI = DE.EMP_CODI 
INNER JOIN PO_CXPAG CX ON DE.CXP_CONT = CX.CXP_CONT AND DE.EMP_CODI = CX.EMP_CODI
INNER JOIN PO_FACTU FA ON CX.FAC_CONT = FA.FAC_CONT AND CX.EMP_CODI = FA.EMP_CODI
INNER JOIN PO_PVDOR PV ON CX.PVD_CODI = PV.PVD_CODI AND CX.EMP_CODI = PV.EMP_CODI
LEFT JOIN BI_TIPOS_OPERACION_TODOS BI ON CX.TOP_CODI = BI.TOP_CODI
WHERE CO.COR_FECH = TO_DATE(:fecha_aut_param, 'DD/MM/YYYY') 
    AND   CO.TOP_CODI IN ({top_codi_placeholders})
    AND   CO.COR_ESTA = 2
    AND   CX.CXP_SALD > 0    
    AND   CX.COR_CONT > 0
    AND   CX.CXP_ESTA = 'B'
    AND   CX.GEA_CONT IS NULL
   
'''
    #  AND   CX.GEA_CONT IS NULL
        
        params = {'fecha_aut_param': fecha_aut_param}
        params.update({f'top_codi{i}': value for i, value in enumerate(top_codi_list)})    
        
        cursor.execute(validacion_total,params)#,params) 
        result = cursor.fetchone()# solo una fila
        
        if not result or result[0] is None:
            return "❌ No se encontraron datos válidos."
        else:
            return result[0]
            #print(f"La suma total del plano es: {result[0]}")  # Formato con miles y dos decimales
            #for row in result: 
                #print(row)  # Imprimir cada fila    
        #rows_updated = cursor.rowcount  # Número de filas insertadas
        #connection.commit()
    except Exception as e:
        return f"❌ Error en la ejecución: {str(e)}"
    finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()   



def insert_gearp_data(fecha_pago_param, fecha_aut_param, top_codi_param_str):
    """Ejecuta el script SQL para insertar datos en TS_GEARP_PLANOS."""
    connection = test_oracle_connection()
    if not connection:
        return "❌ Error de conexión a la base de datos."

    cursor = None       
    try:
            cursor = connection.cursor()
            #top_codi_list = list(map(int, top_codi_param_str.split(",")))
            top_codi_list = [int(x) for x in top_codi_param_str.split(",")]
            top_codi_placeholders = ', '.join([':top_codi' + str(i) for i in range(len(top_codi_list))])
            insert_gearp =  f"""
                INSERT INTO TS_GEARP
                SELECT  'A' AS AUD_ESTA,
                        'ADMINSEVEN1' AS AUD_USUA,
                        SYSDATE AS AUD_UFAC,
                        40 AS EMP_CODI,
                        ROWNUM + (SELECT NVL(MAX(GEA_CONT), 0) FROM TS_GEARP) AS GEA_CONT,
                        888 AS BAN_CODI,
                        1 AS SUB_CODI,
                        '111005010201' AS CUB_NUME,
                        SYSDATE AS GEA_FECH,       
                        'AP:'||(ROWNUM + (SELECT NVL(MAX(GEA_CONT), 0) FROM TS_GEARP))||
                        ' - GIRO REG CONTRIBUTIVO '||TRIM(TO_CHAR(COR_FECH, 'MONTH'))||' '||
                        TO_CHAR(COR_FECH, 'YYYY')||', PROCESO:'||TO_CHAR(COR_FECH, 'YYYYMMDD')||', '||
                        DEPARTAMENTO||' TO.'||TOP_CODI AS GEA_DESC,
                        'N' AS GEA_APLI,
                        'B' AS GEA_ESTA,
                        1 AS MON_CODI,
                        TO_DATE(:fecha_pago_param, 'DD/MM/YYYY') AS GEA_FETA, 
                        1 AS GEA_VATA,
                        'C:\\PLANOS_TESORERIA\\40_'||(ROWNUM + (SELECT NVL(MAX(GEA_CONT), 0) FROM TS_GEARP))||'_RS_GIRODIR_TXT' AS GEA_ARCH,
                        'N' AS GEA_CORR,
                        0 AS TER_CODI
                FROM 
                (
                    SELECT  CO.TOP_CODI,
                            CO.COR_FECH,
                            BI.DEPARTAMENTO
                    FROM PO_CORPA CO
                    INNER JOIN PO_DECOR DE ON CO.COR_CONT = DE.COR_CONT AND CO.EMP_CODI = DE.EMP_CODI 
                    INNER JOIN PO_CXPAG CX ON DE.CXP_CONT = CX.CXP_CONT AND DE.EMP_CODI = CX.EMP_CODI
                    INNER JOIN PO_FACTU FA ON CX.FAC_CONT = FA.FAC_CONT AND CX.EMP_CODI = FA.EMP_CODI
                    INNER JOIN PO_PVDOR PV ON CX.PVD_CODI = PV.PVD_CODI AND CX.EMP_CODI = PV.EMP_CODI
                    LEFT JOIN BI_TIPOS_OPERACION_TODOS BI ON CX.TOP_CODI = BI.TOP_CODI
                    WHERE CO.COR_FECH = TO_DATE(:fecha_aut_param, 'DD/MM/YYYY') 
                    AND CO.TOP_CODI IN ({top_codi_placeholders})
                    AND   CO.COR_ESTA = 2
                    AND   CX.CXP_SALD > 0    
                    AND   CX.COR_CONT > 0
                    AND   CX.CXP_ESTA = 'B'
                    AND   CX.GEA_CONT IS NULL
                   
                    
                    GROUP BY CO.TOP_CODI, CO.COR_FECH, BI.DEPARTAMENTO
                )
            """
            # Crear diccionario de parámetros dinámico
            params = {'fecha_pago_param': fecha_pago_param, 'fecha_aut_param': fecha_aut_param}
            params.update({f'top_codi{i}': value for i, value in enumerate(top_codi_list)})
                
            cursor.execute(insert_gearp,params)
            rows_inserted = cursor.rowcount  # Número de filas insertadas
            connection.commit()
            return "✅ Inserción exitosa en TS_GEARP_PLANOS."

            '''if rows_inserted == 0:
                raise Exception("⚠️ No se insertaron datos. Revisa la subconsulta si trae Datos")
        
            print(f"✅ Inserción exitosa. {rows_inserted} filas insertadas en TS_GEARP_PLANOS.")
                
                 # 🔍 Consultar los datos insertados
            cursor.execute("SELECT * FROM TS_GEARP_PLANOS ORDER BY GEA_CONT DESC FETCH FIRST :num ROWS ONLY", {'num': rows_inserted})
            inserted_data = cursor.fetchall()

            if inserted_data:
                print("\n🔹 Datos Insertados:")'''
    except Exception as e:
       return f"❌ Error en la ejecución: {str(e)}"
    finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
        
def update_gea_cont(fecha_aut_param, top_codi_param_str):
    
    connection = test_oracle_connection()
    if not connection:
        return "❌ Error de conexión a la base de datos."            
           # --- ACTUALIZACIÓN DE GEA_CONT ---
    cursor = None       
    try:
            cursor = connection.cursor()
            top_codi_list = [int(x) for x in top_codi_param_str.split(",")]
            top_codi_placeholders = ', '.join([':top_codi' + str(i) for i in range(len(top_codi_list))])
            update_gea_cont = f'''
                MERGE INTO PO_CXPAG CX
                USING
                (
                    SELECT FA.CXP_CONT,
                        GE.GEA_CONT
                    FROM
                    (
                        SELECT CXP_CONT,
                            'GIRO REG CONTRIBUTIVO '||TRIM(TO_CHAR(COR_FECH, 'MONTH'))||' '||TO_CHAR(COR_FECH, 'YYYY')||', PROCESO:'||TO_CHAR(COR_FECH, 'YYYYMMDD')||', '||DEPARTAMENTO||' TO.'||TOP_CODI AS DESCRIPCION_PLANO
                        FROM
                        (
                            SELECT  CX.CXP_CONT
                                ,CO.COR_FECH
                                ,CO.TOP_CODI
                                ,BI.DEPARTAMENTO
                                ,CX.CXP_SALD  
                                ,CO.COR_NUME
                                ,CX.FAC_NFAP
                                ,CX.CXP_PAGO
                            FROM PO_CORPA CO
                            INNER JOIN PO_DECOR DE ON CO.EMP_CODI = DE.EMP_CODI AND CO.COR_CONT = DE.COR_CONT
                            INNER JOIN PO_CXPAG CX ON DE.EMP_CODI = CX.EMP_CODI AND DE.CXP_CONT = CX.CXP_CONT
                            INNER JOIN PO_FACTU FA ON CX.EMP_CODI = FA.EMP_CODI AND CX.FAC_CONT = FA.FAC_CONT
                            INNER JOIN PO_PVDOR PV ON CX.EMP_CODI = PV.EMP_CODI AND CX.PVD_CODI = PV.PVD_CODI
                            LEFT JOIN BI_TIPOS_OPERACION_TODOS BI ON CX.TOP_CODI = BI.TOP_CODI
                            WHERE CO.COR_FECH = TO_DATE(:fecha_aut_param, 'DD/MM/YYYY')
                            AND CO.TOP_CODI IN ({top_codi_placeholders})
                            AND   CO.COR_ESTA = 2
                            AND   CX.CXP_SALD > 0    
                            AND   CX.COR_CONT > 0
                            AND   CX.CXP_ESTA = 'B'
                            AND   CX.GEA_CONT IS NULL
                            
                            
                        ) 
                    ) FA
                    INNER JOIN TS_GEARP GE ON FA.DESCRIPCION_PLANO = REGEXP_SUBSTR (GE.GEA_DESC, 'G[^-]*')
                ) TMP 
                ON (CX.CXP_CONT = TMP.CXP_CONT)
                WHEN MATCHED THEN 
                UPDATE SET CX.GEA_CONT = TMP.GEA_CONT
        
        ''' 
            params = {'fecha_aut_param': fecha_aut_param}
            params.update({f'top_codi{i}': value for i, value in enumerate(top_codi_list)})    
            
            cursor.execute(update_gea_cont,params) 
            rows_updated = cursor.rowcount  # Número de filas insertadas
            connection.commit()
            
            print(f"✅ {rows_updated} registros actualizados en PO_CXPAG_PLANOS.")
            
            if rows_updated == 0:
                 return "⚠️ No se actualizaron registros. Revisa los datos en la base."

            return f"✅ {rows_updated} registros actualizados correctamente."

            
          

    except Exception as e:
        return f"❌ Error en la ejecución: {str(e)}"
    finally:
        if cursor:
            cursor.close()  # Cierra el cursor si está abierto
        if connection:
            connection.close()  # Cierra la conexiónsi está abierta
        
def export_plano(fecha_pago_param):
             
        connection = test_oracle_connection()    
        if not connection:
            return None, "❌ Error de conexión a la base de datos."     
        
        cursor = None
        try:
            
            query_export = '''
                 SELECT 
                     GE.GEA_CONT AS NUMERO_PLANO
                    ,GE.GEA_DESC AS DESCRIPCION_PLANO
                    ,COUNT(*) AS CANTIDAD_DE_REGISTROS
                    ,SUM(CX.CXP_SALD) AS VALOR_AUTORIZADO
                FROM PO_CXPAG CX
                INNER JOIN TS_GEARP GE ON CX.GEA_CONT = GE.GEA_CONT
                WHERE CX.CXP_ESTA = 'B'
                AND GEA_FETA = TO_DATE(:fecha_pago_param, 'DD/MM/YYYY')
                AND   CX.GEA_CONT IS NOT NULL
                AND GE.AUD_USUA = 'ADMINSEVEN1'
                GROUP BY GE.GEA_CONT, GE.GEA_DESC
                ORDER BY COUNT(*) ASC
            ''' 
            
            df = pd.read_sql(query_export, connection , params = ({'fecha_pago_param': fecha_pago_param}))
            #connection.close()      
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"Plano_contributivo_{timestamp}.xlsx"
            df.to_excel(output_file, index=False)
        
            return output_file, None
        except Exception as e:
            return f"❌ Error en la consulta: {str(e)}"
        finally:
            if connection:
               connection.close()