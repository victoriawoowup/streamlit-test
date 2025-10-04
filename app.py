import streamlit as st
import requests
import time
import pandas as pd
import io
from datetime import datetime

st.set_page_config(page_title="VTEX Validator", page_icon="🔐", layout="wide")


# Logo WOOWUP (usando URL directa)
st.markdown("""
    <div style="text-align: center;">
        <img src="https://woowup.com/wp-content/uploads/2023/03/logo-woowup.png" width="300">
    </div>
    """, unsafe_allow_html=True)
st.title("🔐 Validación de Endpoints VTEX")
st.markdown("---")

# =========================
# Inicializar session state
# =========================
if 'validation_results' not in st.session_state:
    st.session_state.validation_results = []

# =========================
# Inputs de usuario
# =========================
st.markdown("### 🔑 Credenciales VTEX")

col1, col2 = st.columns(2)

with col1:
    ACCOUNT_NAME = st.text_input("Cuenta VTEX", placeholder="mi-tienda")
    VTEX_APP_KEY = st.text_input("App Key", type="password", placeholder="vtexappkey-...")

with col2:
    VTEX_APP_TOKEN = st.text_input("App Token", type="password", placeholder="*******************")
    SALES_CHANNEL = st.text_input("Sales Channel", placeholder="1")

# Validación de campos obligatorios
def validar_credenciales():
    if not all([ACCOUNT_NAME, VTEX_APP_KEY, VTEX_APP_TOKEN, SALES_CHANNEL]):
        st.warning("⚠️ Por favor completa todos los campos antes de continuar")
        st.stop()

# =========================
# Headers
# =========================
def get_vtex_headers():
    return {
        'x-vtex-api-appKey': VTEX_APP_KEY,
        'x-vtex-api-appToken': VTEX_APP_TOKEN,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }

def get_vtex_headers_alt():
    headers = get_vtex_headers()
    headers['Accept'] = 'application/vnd.vtex.ds.v10+json'
    return headers

# =========================
# Funciones de validación con logs
# =========================
def log_resultado(endpoint, status, mensaje):
    st.session_state.validation_results.append({
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'endpoint': endpoint,
        'status': status,
        'mensaje': mensaje
    })

def validar_ventas():
    st.subheader("1️⃣ Ventas")
    headers = get_vtex_headers()
    url = f'https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/oms/pvt/orders'
    params = {
        'orderBy': 'creationDate,desc',
        'f_status': 'ready-for-handling,handling,invoiced',
        'f_salesChannel': SALES_CHANNEL,
        'page': 0,
        'per_page': 1
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        if resp.status_code == 200:
            st.success("✅ ACCESO EXITOSO a API de Ventas")
            log_resultado("Ventas", "✅ SUCCESS", f"Status: {resp.status_code}")
        else:
            st.error(f"❌ ERROR en API de Ventas - Status: {resp.status_code}")
            log_resultado("Ventas", "❌ ERROR", f"Status: {resp.status_code}")
            with st.expander("Ver detalle del error"):
                st.code(resp.text[:500])
    except Exception as e:
        st.error(f"❌ EXCEPCIÓN en API de Ventas: {str(e)}")
        log_resultado("Ventas", "❌ EXCEPTION", str(e))
    
    time.sleep(0.3)  # Rate limiting

def validar_productos():
    st.subheader("2️⃣ Productos")
    headers = get_vtex_headers()
    url = f'https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/catalog_system/pub/products/search?_from=0&_to=5'

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code in [200, 206]:
            st.success("✅ ACCESO EXITOSO a API de Productos")
            products = resp.json()
            product_id = reference_id = None
            for product in products:
                prod_id = product.get('productId')
                ref = product.get('productReference')
                if prod_id and ref:
                    product_id = prod_id
                    reference_id = ref
                    st.info(f"📦 Primer producto encontrado - ID: `{product_id}`, Ref: `{reference_id}`")
                    break
            if not product_id:
                st.warning("⚠️ No se encontró productId o referenceId")
            log_resultado("Productos", "✅ SUCCESS", f"Productos encontrados: {len(products)}")
            time.sleep(0.3)
            return product_id, reference_id
        else:
            st.error(f"❌ ERROR en API de Productos - Status: {resp.status_code}")
            log_resultado("Productos", "❌ ERROR", f"Status: {resp.status_code}")
            with st.expander("Ver detalle del error"):
                st.code(resp.text[:500])
            return None, None
    except Exception as e:
        st.error(f"❌ EXCEPCIÓN en API de Productos: {str(e)}")
        log_resultado("Productos", "❌ EXCEPTION", str(e))
        return None, None

def validar_clientes():
    st.subheader("3️⃣ Clientes")
    headers = get_vtex_headers_alt()
    url = f'https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/dataentities/CL/search'
    params = {'_fields': '_all'}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        if resp.status_code == 200:
            st.success("✅ ACCESO EXITOSO a API de Clientes")
            log_resultado("Clientes", "✅ SUCCESS", f"Status: {resp.status_code}")
        else:
            st.error(f"❌ ERROR en API de Clientes - Status: {resp.status_code}")
            log_resultado("Clientes", "❌ ERROR", f"Status: {resp.status_code}")
            with st.expander("Ver detalle del error"):
                st.code(resp.text[:500])
    except Exception as e:
        st.error(f"❌ EXCEPCIÓN en API de Clientes: {str(e)}")
        log_resultado("Clientes", "❌ EXCEPTION", str(e))
    
    time.sleep(0.3)

def validar_precios(product_id):
    st.subheader("4️⃣ Precios")
    if not product_id:
        st.warning("⚠️ SALTEADO - No hay productId disponible")
        log_resultado("Precios", "⚠️ SKIPPED", "No hay productId")
        return

    headers = get_vtex_headers_alt()
    url = f'https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/pricing/prices/{product_id}'

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            st.success("✅ ACCESO EXITOSO a API de Precios")
            log_resultado("Precios", "✅ SUCCESS", f"ProductId: {product_id}")
        else:
            st.error(f"❌ ERROR en API de Precios - Status: {resp.status_code}")
            log_resultado("Precios", "❌ ERROR", f"Status: {resp.status_code}")
    except Exception as e:
        st.error(f"❌ EXCEPCIÓN en API de Precios: {str(e)}")
        log_resultado("Precios", "❌ EXCEPTION", str(e))
    
    time.sleep(0.3)

def validar_categorias():
    st.subheader("5️⃣ Categorías")
    headers = get_vtex_headers_alt()
    headers['REST-Range'] = 'resources=0-10'
    url = f'https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/catalog_system/pub/category/tree/10'

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            st.success("✅ ACCESO EXITOSO a API de Categorías")
            log_resultado("Categorías", "✅ SUCCESS", f"Status: {resp.status_code}")
        else:
            st.error(f"❌ ERROR en API de Categorías - Status: {resp.status_code}")
            log_resultado("Categorías", "❌ ERROR", f"Status: {resp.status_code}")
            with st.expander("Ver detalle del error"):
                st.code(resp.text[:500])
    except Exception as e:
        st.error(f"❌ EXCEPCIÓN en API de Categorías: {str(e)}")
        log_resultado("Categorías", "❌ EXCEPTION", str(e))
    
    time.sleep(0.3)

def validar_simulador(product_id):
    st.subheader("6️⃣ Simulador")
    if not product_id:
        st.warning("⚠️ SALTEADO - No hay productId disponible")
        log_resultado("Simulador", "⚠️ SKIPPED", "No hay productId")
        return
    
    headers = get_vtex_headers_alt()
    url = f'https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/checkout/pvt/orderForms/simulation'
    payload = {"items": [{"id": str(product_id), "quantity": 1, "seller": SALES_CHANNEL}]}

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            st.success("✅ ACCESO EXITOSO a API de Simulador")
            log_resultado("Simulador", "✅ SUCCESS", f"ProductId: {product_id}")
        else:
            st.error(f"❌ ERROR en API de Simulador - Status: {resp.status_code}")
            log_resultado("Simulador", "❌ ERROR", f"Status: {resp.status_code}")
            with st.expander("Ver detalle del error"):
                st.code(resp.text[:500])
    except Exception as e:
        st.error(f"❌ EXCEPCIÓN en API de Simulador: {str(e)}")
        log_resultado("Simulador", "❌ EXCEPTION", str(e))

def generar_reporte_txt():
    """Genera un reporte en texto plano de todas las validaciones"""
    reporte = []
    reporte.append("=" * 60)
    reporte.append("REPORTE DE VALIDACIÓN DE ENDPOINTS VTEX")
    reporte.append("=" * 60)
    reporte.append(f"Cuenta: {ACCOUNT_NAME}")
    reporte.append(f"Sales Channel: {SALES_CHANNEL}")
    reporte.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    reporte.append("=" * 60)
    reporte.append("")
    
    for resultado in st.session_state.validation_results:
        reporte.append(f"[{resultado['timestamp']}] {resultado['endpoint']}")
        reporte.append(f"  Status: {resultado['status']}")
        reporte.append(f"  Mensaje: {resultado['mensaje']}")
        reporte.append("")
    
    return "\n".join(reporte)

# =========================
# Botón de validación de endpoints
# =========================
st.markdown("---")

if st.button("🚀 Validar Todos los Endpoints", type="primary", use_container_width=True):
    validar_credenciales()
    
    # Limpiar resultados anteriores
    st.session_state.validation_results = []
    
    with st.spinner('🔄 Validando endpoints VTEX...'):
        validar_ventas()
        product_id, reference_id = validar_productos()
        validar_clientes()
        validar_precios(product_id)
        validar_categorias()
        validar_simulador(product_id)
    
    st.success("🎉 Validación completada")
    
    # Botón de descarga de reporte
    reporte_txt = generar_reporte_txt()
    st.download_button(
        label="📄 Descargar Reporte de Validación",
        data=reporte_txt,
        file_name=f"validacion_vtex_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain"
    )

# ---------------------------------------------------------------------------------
# SEGUNDO BLOQUE: EXTRACCIÓN DE CLIENTES
# ---------------------------------------------------------------------------------
st.markdown("---")
st.markdown("---")
st.header("👥 Extracción de Clientes")

col1, col2 = st.columns(2)

with col1:
    fecha_desde = st.date_input(
        "📅 Fecha desde (updatedIn)", 
        value=datetime(2023, 1, 1),
        help="Fecha mínima de actualización de clientes"
    )

with col2:
    fecha_hasta = st.date_input(
        "📅 Fecha hasta (updatedIn)", 
        value=datetime.today(),
        help="Fecha máxima de actualización de clientes"
    )

# Configuración fija
registros_por_pagina = 100  # Estándar de VTEX

campos_clientes = ['document', 'email', 'firstName', 'lastName', 'birthdate', 
                   'homePhone', 'gender', 'isNewsletterOptIn', 'updatedIn']

# Botón para ejecutar extracción
if st.button("📥 Extraer Clientes", type="primary", use_container_width=True):
    validar_credenciales()
    
    # Convertir fechas a ISO 8601 UTC para VTEX
    fecha_desde_iso = fecha_desde.strftime("%Y-%m-%dT00:00:00.000Z")
    fecha_hasta_iso = fecha_hasta.strftime("%Y-%m-%dT23:59:59.999Z")

    # Headers
    headers = {
        'x-vtex-api-appKey': VTEX_APP_KEY,
        'x-vtex-api-appToken': VTEX_APP_TOKEN,
        'Accept': 'application/vnd.vtex.ds.v10+json',
        'Content-Type': 'application/json',
        'REST-Range': f'resources=0-{registros_por_pagina}'
    }

    # URL de scroll
    url = f'https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/dataentities/CL/scroll'

    # Parámetros
    params = {
        '_fields': '_all',
        '_where': f"(updatedIn>{fecha_desde_iso} AND updatedIn<{fecha_hasta_iso}) OR ((updatedIn is null) AND (createdIn>{fecha_desde_iso} AND createdIn<{fecha_hasta_iso}))"
    }

    clientes = []
    token = None
    page_count = 0

    # Barra de progreso
    progress_text = st.empty()
    info_text = st.empty()

    with st.spinner('🔄 Extrayendo clientes de VTEX...'):
        while True:  # Sin límite - recorre hasta que no haya más datos
            page_count += 1
            if token:
                params['_token'] = token
            
            try:
                resp = requests.get(url, headers=headers, params=params, timeout=20)
                
                if resp.status_code != 200:
                    st.error(f"❌ Error en página {page_count}: Status {resp.status_code}")
                    with st.expander("Ver detalle del error"):
                        st.code(resp.text[:500])
                    break

                # Token para siguiente página
                token = resp.headers.get('X-VTEX-MD-TOKEN')

                data = resp.json()
                if not data or len(data) == 0:
                    info_text.success("✅ No hay más clientes para procesar")
                    break

                clientes.extend(data)
                
                # Actualizar progreso
                progress_text.text(f"📄 Página {page_count}")
                info_text.info(f"✅ {len(data)} clientes en esta página | Total acumulado: {len(clientes)}")

                if not token:
                    info_text.success("✅ Se procesaron todas las páginas disponibles")
                    break
                
                # Rate limiting
                time.sleep(0.5)

            except requests.exceptions.Timeout:
                st.error(f"⏱️ Timeout en página {page_count}. Reintentando...")
                time.sleep(2)
                continue
            except Exception as e:
                st.error(f"❌ Excepción en página {page_count}: {str(e)}")
                break

    # Procesar resultados
    if clientes:
        st.success(f"🎉 Extracción completada: {len(clientes)} clientes recuperados")
        
        # Convertir a DataFrame
        df = pd.DataFrame(clientes)
        df = df.reindex(columns=campos_clientes)

        # Mostrar estadísticas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Clientes", len(df))
        with col2:
            st.metric("Páginas Procesadas", page_count)
        with col3:
            emails_validos = df['email'].notna().sum()
            st.metric("Emails Válidos", emails_validos)

        # Mostrar muestra
        st.markdown("#### 👀 Muestra de los primeros 5 clientes")
        st.dataframe(df.head(5), use_container_width=True)

        # Preparar CSV para descarga
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8')
        csv_data = csv_buffer.getvalue()

        st.download_button(
            label="📥 Descargar CSV Completo de Clientes",
            data=csv_data,
            file_name=f"clientes_vtex_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.warning("⚠️ No se recuperaron clientes para el rango de fechas indicado")

# Footer
st.markdown("---")
st.markdown("🔐 **VTEX Endpoint Validator** | Desarrollado con Streamlit")