import streamlit as st
import pandas as pd
from .Procesamiento import process_file, validacion  # Importamos la función del otro archivo
#from Procesamiento import validacion


# PROFESIONAL EN ANALÍTICA DE DATOS
# st.write(f"📌 Procesando archivo para el proceso: {proceso_param} y tipo de giro: {tipo_giro_param}")
# Aplicar estilos en línea con st.markdown



if "fecha_pago_param" not in st.session_state:
    st.session_state.fecha_pago_param = "DD/MM/YYYY"
if "fecha_aut_param" not in st.session_state:
    st.session_state.fecha_aut_param = "DD/MM/YYYY"
if  "top_codi_param" not in st.session_state:
    st.session_state.top_codi_param = "TO"
if "validacion_exitosa" not in st.session_state:
    st.session_state.validacion_exitosa = False  # Controla si la validación fue correcta
if "output_file" not in st.session_state:
    st.session_state.output_file = None  # Guarda el archivo generado
      

def limpiar_datos():
    st.session_state.fecha_pago_param = "DD/MM/YYYY"
    st.session_state.fecha_aut_param = "DD/MM/YYYY"
    st.session_state.top_codi_param = "TO"
    st.session_state.validacion_exitosa = False  # Reiniciar validación
    st.session_state.output_file = None  # Limpiar archivo generado
    st.rerun()  #🚀 Refresca la página sin que el usuario tenga que hacerlo

def app():
    st.markdown("""
        <style>
            /* Color de fondo */
            .stApp {
                background-color: #0F9588;
                max-height: 4900px !important; /* Limita la altura */
            }
        </style>
    """,  unsafe_allow_html=True)# Estilo de fondo
                    
    ################# INTERFAZ ############################
    #st.image("logo3.png", width=100)        
    # # Mostrar imagen centrada (usa una imagen en la carpeta del proyecto)
    # Mostrar título centrado
    st.markdown(
        """
        <h2 style="text-align: center; 
        font-size: 30px; 
        font-weight: bold; 
        color: white;
        margin: 8px auto !important;">
            Gestión De Archivos Planos 
        </h2>
        """,
        unsafe_allow_html=True
    )

    # --- INTERFAZ EN STREAMLIT ---
    #st.image("logo.png", width=150)
    #st.title("Procesamiento De Facturas")

    # Aplicar estilos al texto del file_uploader

    st.markdown(
        """
        <style>
            div.stFileUploader > label {
                font-size: 40px !important;  /* Cambia el tamaño del texto */
                font-weight: bold;           /* Texto en negrita */
                color: white;      /* Cambia el color del texto */
            
            }
            
            div.stTextInput > label {
                font-size: 40px !important;  /* Cambia el tamaño del texto */
                font-weight: bold;           /* Texto en negrita */
                color: white;      /* Cambia el color del texto */
            }
            
            div.stNumberInput > label {
                font-size: 40px !important;  /* Cambia el tamaño del texto */
                font-weight: bold;           /* Texto en negrita */
                color: white;      /* Cambia el color del texto */
            }
            
            div.stSelectbox > label {
                font-size: 40px !important;  /* Cambia el tamaño del texto */
                font-weight: bold;           /* Texto en negrita */
                color: black;      /* Cambia el color del texto */
            }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Inicializa variables en session_state si no existen
    for key, default in [
        ("fecha_pago_param", "DD/MM/YYYY"),
        ("fecha_aut_param", "DD/MM/YYYY"),
        ("top_codi_param", "TO"),
        ("validacion_exitosa", False),
        ("output_file", None),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default
    
    
    
    # 📌 **Ingresar parámetros (Siempre visibles, pero reiniciables)**

    valor_ingresado = int(st.number_input("Ingrese valor total de autorización sin puntos ni comas", min_value=0.0, format="%.0f"))
    st.session_state.fecha_pago_param = st.text_input("Ingrese la Fecha de Pago (DD/MM/YYYY)", value= st.session_state.get("fecha_pago_param", "DD/MM/YYYY"))
    st.session_state.fecha_aut_param  = st.text_input("Ingrese la Fecha de Autorización (DD/MM/YYYY)", value= st.session_state.get("fecha_aut_param","DD/MM/YYYY"))
    st.session_state.top_codi_param  = st.text_input("Ingrese Tipos De Operacion",value= st.session_state.get("top_codi_param", "TO"))

    # Botón para ejecutar la validación
    if st.button("Validar"):
        if not st.session_state.fecha_aut_param or not st.session_state.top_codi_param:
            st.error("❌ Error: Todos los campos deben estar llenos antes de validar.")
            st.session_state.validacion_exitosa = False
        else:
            resultado_validacion = validacion(st.session_state.fecha_aut_param, st.session_state.top_codi_param)
            
            #st.write(f"Valor ingresado: {valor_ingresado} ({type(valor_ingresado)})")
            #st.write(f"Resultado validación: {resultado_validacion} ({type(resultado_validacion)})")
            
            
            if isinstance(resultado_validacion, str) and "❌" in resultado_validacion:
                st.error(resultado_validacion)  # Mensaje de error si la validación falla
            elif resultado_validacion is None:
                st.error("❌ NO HAY DATOS, POR FAVOR VALIDAR.")
                st.session_state.validacion_exitosa = False
            else:
                try:
                    total_validado = int(float(resultado_validacion))  # Convertir a número
                    valor_ingresado_entero = int(float(valor_ingresado))  # Convertir también el valor ingresado
                    if valor_ingresado != total_validado:
                        st.error(f"❌ Error: El valor ingresado ({valor_ingresado:,.2f}) no coincide con el total calculado ({total_validado:,.2f}).")
                    else:
                        st.success("✅ Validación correcta. Iniciando el procesamiento...")
                        st.session_state.validacion_exitosa = True  # Permitir continuar con la ejecución
                except (ValueError, TypeError):
                    st.error(f"❌ Error: No se pudo convertir el resultado de validación '{resultado_validacion}' a un número.")
                    st.session_state.validacion_exitosa = False

    # 🗑 **Botón para limpiar los datos y resetear el file_uploader**
    if st.button("Borrar Datos Ingresados"):
        limpiar_datos()


    #fecha_pago_param = st.text_input("Ingrese la Fecha de Pago (DD/MM/YYYY)", "")
    #fecha_aut_param = st.text_input("Ingrese la Fecha de Autorización (DD/MM/YYYY)", "")
    #top_codi_param = st.text_input("Ingrese Tipos De Operacion", "")
    #descripcion_param = st.text_area("Ingrese la Descripción")

    # 📂 **Mostrar botón de "Generar y Descargar Excel" solo si la validación es exitosa**
    if st.session_state.validacion_exitosa:
        if st.button("Generar y Descargar Excel"):
            with st.spinner("Generando archivo..."):
                top_codi_param_list = st.session_state.top_codi_param.split(",")  
                top_codi_param_str = ",".join(map(str, top_codi_param_list))
                output_file, error = process_file(st.session_state.fecha_pago_param, st.session_state.fecha_aut_param, st.session_state.top_codi_param)
            
            if error:
                st.error(error)
            else:
                st.session_state.output_file = output_file  # Guardar el archivo generado

    # 📥 **Mostrar botón de descarga solo si el archivo ha sido generado**
    if st.session_state.output_file:
        with open(st.session_state.output_file, "rb") as file:
            st.download_button(
                label="📥 Descargar archivo procesado",
                data=file,
                file_name=st.session_state.output_file,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        st.success("✅ El archivo ha sido procesado y está listo para descargar.")

if __name__ == "__main__":
    app()
   
    #if st.button("Cancelar"):


    #'''if st.button("Generar y Descargar Excel"):
    #   with st.spinner("Generando archivo..."):
    ##     top_codi_param_list = st.session_state.top_codi_param.split(",")  
        #    top_codi_param_str = ",".join(map(str, top_codi_param_list))
        #   output_file, error = process_file(st.session_state.fecha_pago_param, st.session_state.fecha_aut_param, st.session_state.top_codi_param)
        
        
            
        #if error:
        #    st.error(error)
        #else:
        #   with open(output_file, "rb") as file:
        #      st.download_button(
        #         label="Descargar archivo procesado",
            #        data=file,
            #       file_name=output_file,
            #      mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            # )
        # st.success("El archivo ha sido procesado y está listo para descargar.")'''