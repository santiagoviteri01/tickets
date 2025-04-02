import time
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
# Configuración de usuarios y contraseñas
USUARIOS = {
    "wiga": "contraseña_secreta123",
    "admin": "admin123",
    "dany":"futbol123"
}

# Función de autenticación básica
def autenticacion():
    # Reiniciar estado si viene de logout
    if 'autenticado' not in st.session_state or st.session_state.get('logout'):
        st.session_state.autenticado = False
        st.session_state.logout = False
        
    if not st.session_state.autenticado:
        with st.container():
            st.title("🔒 Inicio de Sesión")
            usuario = st.text_input("Usuario")
            contraseña = st.text_input("Contraseña", type="password")
            
            if st.button("Ingresar"):
                if USUARIOS.get(usuario) == contraseña:
                    st.session_state.autenticado = True
                    st.session_state.logout = False
                    st.session_state.usuario_actual = usuario

                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos")
        return False
    return True
# Función para manejar tickets
def visualizar_tickets():
    if os.path.exists('tickets.txt'):
        # Leer todos los tickets
        with open('tickets.txt', 'r', encoding='utf-8') as f:
            lineas = f.readlines()
        
        # Procesar datos
        tickets = []
        for linea in lineas:
            datos = linea.strip().split('|')
            if len(datos) >= 9:
                tickets.append({
                    'Número': int(datos[0]),
                    'Título': datos[1],
                    'Área': datos[2],
                    'Estado Actual': datos[3],
                    'Última Modificación': datos[7],
                    'Creado por': datos[6],
                    'Modificado por': datos[8],
                    'Días en Estado Actual': datos[9] if len(datos) > 9 else 'N/A'
                })

        if tickets:
            df = pd.DataFrame(tickets)
            
            # Mostrar métricas clave
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Tickets", len(df['Número'].unique()))
            with col2:
                st.metric("Tickets Abiertos", df[df['Estado Actual'] != 'cerrado']['Número'].nunique())
            with col3:
                tickets_cerrados = df[df['Estado Actual'] == 'cerrado']
                try:
                    dias = tickets_cerrados['Días en Estado Actual'].str.extract(r'(\d+)d', expand=False).dropna().astype(float)
                    tiempo_promedio = dias.mean() if not dias.empty else None
                except AttributeError:
                    tiempo_promedio = None
                
                # Y en la métrica:
                st.metric("Tiempo Resolución Promedio", 
                          f"{tiempo_promedio:.1f} días" if tiempo_promedio else "N/A")

            # Filtros
            st.subheader("Filtros")
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filtro_area = st.selectbox("Filtrar por Área", ["Todas"] + list(df['Área'].unique()))
            with col_f2:
                filtro_estado = st.selectbox("Filtrar por Estado", ["Todos"] + list(df['Estado Actual'].unique()))

            # Aplicar filtros
            if filtro_area != "Todas":
                df = df[df['Área'] == filtro_area]
            if filtro_estado != "Todos":
                df = df[df['Estado Actual'] == filtro_estado]

            # Mostrar tabla con los últimos estados
            st.subheader("Todos los Tickets")
            st.dataframe(
                df.sort_values('Última Modificación', ascending=False)
                .drop_duplicates('Número', keep='first')
                .style.applymap(lambda x: 'background-color: #ffcccc' if x == 'cerrado' else '', 
                              subset=['Estado Actual']),
                use_container_width=True,
                height=600
            )
        else:
            st.warning("No hay tickets registrados aún")
    else:
        st.warning("No se ha creado ningún ticket todavía")


def manejar_tickets():
    # Cargar tickets existentes
    if not os.path.exists('tickets.txt'):
        with open('tickets.txt', 'w', encoding='utf-8') as f:
            pass
    
    # Mostrar opciones
    opcion_ticket = st.radio("Seleccione una acción:", ["Crear nuevo ticket", "Modificar ticket existente"])
    
    if opcion_ticket == "Crear nuevo ticket":
        with st.form("nuevo_ticket"):
            st.subheader("📝 Nuevo Ticket")
            titulo = st.text_input("Título del Ticket*")
            area = st.selectbox("Área*", ["crediprime", "generales"])
            estado = st.selectbox("Estado*", ["inicial", "documentacion pendiente", "documentacion enviada", "en reparacion"])
            descripcion = st.text_area("Descripción detallada*")
            
            if st.form_submit_button("Guardar Ticket"):
                if not all([titulo, area, estado, descripcion]):
                    st.error("Todos los campos marcados con * son obligatorios")
                else:
                    # Generar número de ticket
# Por este código:
                    with open('tickets.txt', 'r', encoding='utf-8') as f:
                        # Obtener todos los números de ticket únicos
                        tickets_existentes = {int(linea.split('|')[0]) for linea in f if linea.strip()}
                        
                        if tickets_existentes:
                            ultimo_ticket = max(tickets_existentes)
                        else:
                            ultimo_ticket = 0  # Si no hay tickets
                    
                    nuevo_numero = ultimo_ticket + 1
                    
                    # Crear registro
                    fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    registro = (
                        f"{nuevo_numero}|{titulo}|{area}|{estado}|{descripcion}|"
                        f"{fecha_creacion}|{st.session_state.usuario_actual}|"
                        f"{fecha_creacion}|{st.session_state.usuario_actual}\n"
                    )
                    
                    # Guardar en archivo
                    with open('tickets.txt', 'a', encoding='utf-8') as f:
                        f.write(registro)
                    st.success(f"Ticket #{nuevo_numero} creado exitosamente!")
    
    else:  # Modificar ticket
        with st.form("buscar_ticket"):
            st.subheader("🔍 Buscar Ticket")
            ticket_id = st.number_input("Ingrese el número de ticket:", min_value=1, step=1)
            
            if st.form_submit_button("Buscar"):
                with open('tickets.txt', 'r', encoding='utf-8') as f:
                    tickets = f.readlines()
                
                encontrado = None
                for ticket in reversed(tickets):
                    datos = ticket.strip().split('|')
                    if int(datos[0]) == ticket_id:
                        encontrado = datos
                        break
                
                if encontrado:
                    if encontrado[3] == "cerrado":
                        st.error("No se puede modificar un ticket cerrado")
                    else:
                        st.session_state.ticket_actual = {
                            "numero": encontrado[0],
                            "titulo": encontrado[1],
                            "area": encontrado[2],
                            "estado": encontrado[3],
                            "descripcion": encontrado[4],
                            "fecha_creacion": encontrado[5],
                            "usuario_creacion": encontrado[6]
                        }
                else:
                    st.error("Ticket no encontrado")
        
        if 'ticket_actual' in st.session_state:
            with st.form("modificar_ticket"):
                st.subheader(f"✏️ Modificando Ticket #{st.session_state.ticket_actual['numero']}")
                
                nuevo_estado = st.selectbox(
                    "Nuevo estado:",
                    ["inicial", "documentacion pendiente", "documentacion enviada", "en reparacion", "cerrado"],
                    index=["inicial", "documentacion pendiente", "documentacion enviada", "en reparacion", "cerrado"]
                        .index(st.session_state.ticket_actual['estado'])
                )
                
                nueva_descripcion = st.text_area(
                    "Descripción actualizada:",
                    value=st.session_state.ticket_actual['descripcion']
                )
                
                if st.form_submit_button("Guardar Cambios"):
                    fecha_modificacion = datetime.now()
                    
                    # Calcular días desde última modificación
                    with open('tickets.txt', 'r', encoding='utf-8') as f:
                        lineas = f.readlines()
                    
                    ultima_fecha = datetime.strptime(
                        st.session_state.ticket_actual['fecha_creacion'], 
                        "%Y-%m-%d %H:%M:%S"
                    )
                    
                    for linea in reversed(lineas):
                        datos = linea.strip().split('|')
                        if datos[0] == st.session_state.ticket_actual['numero']:
                            ultima_fecha = datetime.strptime(
                                datos[7] if len(datos) > 7 else datos[5], 
                                "%Y-%m-%d %H:%M:%S"
                            )
                            break
                    
                    dias_transcurridos = (fecha_modificacion - ultima_fecha).days
                    
                    # Usar flecha ASCII en lugar de Unicode
                    if nuevo_estado != st.session_state.ticket_actual['estado']:
                        registro_dias = f"{dias_transcurridos}d ({st.session_state.ticket_actual['estado']} -> {nuevo_estado})"
                    else:
                        registro_dias = "Sin cambio de estado"
                    
                    nuevo_registro = (
                        f"{st.session_state.ticket_actual['numero']}|"
                        f"{st.session_state.ticket_actual['titulo']}|"
                        f"{st.session_state.ticket_actual['area']}|"
                        f"{nuevo_estado}|{nueva_descripcion}|"
                        f"{st.session_state.ticket_actual['fecha_creacion']}|"
                        f"{st.session_state.ticket_actual['usuario_creacion']}|"
                        f"{fecha_modificacion.strftime('%Y-%m-%d %H:%M:%S')}|"
                        f"{st.session_state.usuario_actual}|"
                        f"{registro_dias}\n"
                    )
                    
                    with open('tickets.txt', 'a', encoding='utf-8') as f:
                        f.write(nuevo_registro)
                    st.success("Ticket actualizado correctamente!")
                    del st.session_state.ticket_actual

# Función para descargar tickets
def descargar_tickets():
    if os.path.exists('tickets.txt'):
        with open('tickets.txt', 'r') as f:
            st.download_button(
                label="⬇️ Descargar todos los tickets",
                data=f.read(),
                file_name="tickets.txt",
                mime="text/plain"
            )
            
# Verificar autenticación antes de mostrar la app
if not autenticacion():
    st.stop()
# Configuración de la página
st.set_page_config(
    page_title="Sistema de Tickets y Análisis",
    page_icon="📊",
    layout="wide"
)

# Menú en la barra lateral
opcion = st.sidebar.radio(
    "Menú Principal",
    options=["Inicio", "📥 Ingresar Ticket", "📈 Análisis de Siniestralidad", "🚪 Salir"],
    index=0
)

# Contenido principal según la opción seleccionada
if opcion == "Inicio":
    st.title("Bienvenido al Sistema de Gestión de las Gestiones")
    st.write("---")
    st.subheader("Selecciona una opción del menú lateral")
    st.write("""
    **Opciones disponibles:**
    1. 📥 Ingresar Ticket - Registra nuevos tickets o incidencias
    2. 📈 Análisis de Siniestralidad - Visualiza estadísticas y métricas clave
    3. 🚪 Salir - Cierra la aplicación
    """)

elif opcion == "📥 Ingresar Ticket":
    st.title("📥 Registro de Nuevo Ticket")
    manejar_tickets()
    visualizar_tickets()  # Nueva función de visualización
    descargar_tickets()

elif opcion == "📈 Análisis de Siniestralidad":
    st.title("📈 Análisis de Siniestralidad")
    st.write("---")
    
    # Sección de métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tickets Totales", 152, delta="+12 este mes")
    with col2:
        st.metric("Siniestros Resueltos", "85%", delta="-5% vs anterior")
    with col3:
        st.metric("Costo Promedio", "$1,250", delta="+$150")
    
    # Gráfico de tendencias (ejemplo)
    st.subheader("Tendencia Mensual de Siniestros")
    # Aquí podrías incluir un gráfico con datos reales
    st.line_chart({
        'Ene': 23,
        'Feb': 45,
        'Mar': 32,
        'Abr': 28,
        'May': 41
    })
    
    # Análisis por categoría
    st.subheader("Distribución por Categoría")
    categorias = ['Técnico', 'Operativo', 'Financiero', 'Otro']
    valores = [65, 42, 28, 17]
    st.bar_chart(dict(zip(categorias, valores)))

elif opcion == "🚪 Salir":
    st.session_state.autenticado = False
    st.session_state.logout = True  # Nueva bandera de control
    
    # Mensaje de despedida
    st.title("👋 Sesión Finalizada")
    st.write("---")
    st.success("Has salido del sistema exitosamente. Redirigiendo al login...")
    
    # Esperar y forzar recarga
    time.sleep(2)
    st.rerun()  # Esto h

