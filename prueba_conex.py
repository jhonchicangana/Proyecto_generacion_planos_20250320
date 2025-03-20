import oracledb
from decouple import config


def test_oracle_connection():
    try:
        oracledb.init_oracle_client(lib_dir=r"C:\instantclient_12_2") 
        dsn = f"(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST={config('HOST')})(PORT={config('PORT')}))(CONNECT_DATA=(SID={config('SID')})))"
        connection = oracledb.connect(user=config("USER"), password=config("PASS"), dsn=dsn)
        print("✅ Conexión exitosa a la base de datos.")
        return connection  # Ahora devuelve la conexión
    except oracledb.DatabaseError as e:
        print(f"❌ Error de conexión a la base de datos: {e}")
        return None  # Si falla, retorna None


def validacion():
    connection = test_oracle_connection()
    if not connection:
        return "❌ Error de conexión a la base de datos."

    cursor = None
    try:
        cursor = connection.cursor()
        #top_codi_list = [int(x) for x in top_codi_param_str.split(",")]
        #top_codi_placeholders = ', '.join([':top_codi' + str(i) for i in range(len(top_codi_list))])
        
        validacion_total = '''SELECT SUM(CX.CXP_PAGO)
FROM PO_CORPA CO
INNER JOIN PO_DECOR DE ON CO.COR_CONT = DE.COR_CONT AND CO.EMP_CODI = DE.EMP_CODI 
INNER JOIN PO_CXPAG CX ON DE.CXP_CONT = CX.CXP_CONT AND DE.EMP_CODI = CX.EMP_CODI
INNER JOIN PO_FACTU FA ON CX.FAC_CONT = FA.FAC_CONT AND CX.EMP_CODI = FA.EMP_CODI
INNER JOIN PO_PVDOR PV ON CX.PVD_CODI = PV.PVD_CODI AND CX.EMP_CODI = PV.EMP_CODI
LEFT JOIN BI_TIPOS_OPERACION_TODOS BI ON CX.TOP_CODI = BI.TOP_CODI
WHERE CO.COR_FECH = '02/03/2025'
AND CO.TOP_CODI IN (3402,3400,3409,3065,3066,3404,3407)
    AND   CO.COR_ESTA = 2
    AND   CX.CXP_PAGO > 0    
    AND   CX.COR_CONT > 0
    AND   CX.CXP_ESTA = 'G'
'''
    
        #params = {'fecha_aut_param': fecha_aut_param}
        #params.update({f'top_codi{i}': value for i, value in enumerate(top_codi_list)})    
        
        cursor.execute(validacion_total)#,params) 
        result = cursor.fetchone()# solo una fila
        
        if not result or result[0] is None:
            print("No hay datos.")
        else:
            print(f"La suma total del plano es: {result[0]}")  # Formato con miles y dos decimales
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
validacion()




