import streamlit as st
import requests
import time
import pandas as pd
import io
from datetime import datetime, timedelta

# ========================= ESTILOS CSS =========================
st.markdown("""
<style>
    /* Ajustar tamaño de títulos */
    h1 {
        font-size: 2rem !important;
        font-weight: 600 !important;
    }
    h2 {
        font-size: 1.5rem !important;
        font-weight: 600 !important;
    }
    h3 {
        font-size: 1.2rem !important;
        font-weight: 500 !important;
    }
    
    /* Mejorar botones */
    .stButton button {
        border-radius: 8px;
        font-weight: 500;
    }
    
    /* Mejorar inputs */
    .stTextInput input {
        border-radius: 6px;
    }
    
    /* Espaciado más compacto */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

st.set_page_config(
    page_title="VTEX Validator", 
    page_icon="icono_woowup.png",
    layout="wide"
)

st.markdown("<br>", unsafe_allow_html=True)

# Logo WOOWUP centrado
col1, col2, col3 = st.columns([2, 1, 2])
with col2:
    st.image("woowup_logo.png", use_container_width=True)
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
    SALES_CHANNEL = st.text_input("Sales Channel (opcional)", placeholder="1", help="Dejar vacío para traer todos los sales channels")

# Validación de campos obligatorios (sin Sales Channel)
def validar_credenciales():
    if not all([ACCOUNT_NAME, VTEX_APP_KEY, VTEX_APP_TOKEN]):
        st.warning("⚠️ Por favor completa Cuenta, App Key y App Token antes de continuar")
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
        'f_status': 'payment-approved,ready-for-handling,handling,invoiced',
        'page': 0,
        'per_page': 1
    }
    
    # Solo agregar sales channel si no está vacío
    if SALES_CHANNEL and SALES_CHANNEL.strip():
        params['f_salesChannel'] = SALES_CHANNEL

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
    
    time.sleep(0.3)

def validar_productos():
    st.subheader("2️⃣ Productos")
    headers = get_vtex_headers()
    url = f'https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/catalog_system/pub/products/search?_from=0&_to=5'

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code in [200, 206]:
            st.success("✅ ACCESO EXITOSO a API de Productos")
            products = resp.json()
            product_id = reference_id = item_id = None
            for product in products:
                prod_id = product.get('productId')
                ref = product.get('productReference')
                items = product.get('items', [])
                sku_id = items[0].get('itemId') if items else None
                
                if prod_id and ref:
                    product_id = prod_id
                    reference_id = ref
                    item_id = sku_id
                    st.info(f"📦 Primer producto encontrado - ProductID: `{product_id}`, Ref: `{reference_id}`, ItemID: `{item_id}`")
                    break
            if not product_id:
                st.warning("⚠️ No se encontró productId o referenceId")
            log_resultado("Productos", "✅ SUCCESS", f"Productos encontrados: {len(products)}")
            time.sleep(0.3)
            return product_id, reference_id, item_id
        else:
            st.error(f"❌ ERROR en API de Productos - Status: {resp.status_code}")
            log_resultado("Productos", "❌ ERROR", f"Status: {resp.status_code}")
            with st.expander("Ver detalle del error"):
                st.code(resp.text[:500])
            return None, None, None
    except Exception as e:
        st.error(f"❌ EXCEPCIÓN en API de Productos: {str(e)}")
        log_resultado("Productos", "❌ EXCEPTION", str(e))
        return None, None, None

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

def validar_precios(product_id, item_id=None):
    st.subheader("4️⃣ Precios")
    if not product_id and not item_id:
        st.warning("⚠️ SALTEADO - No hay productId ni itemId disponible")
        log_resultado("Precios", "⚠️ SKIPPED", "No hay productId ni itemId")
        return

    headers = get_vtex_headers_alt()
    
    # Intentar primero con productId
    url = f'https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/pricing/prices/{product_id}'

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            st.success(f"✅ ACCESO EXITOSO a API de Precios (usando ProductID: {product_id})")
            log_resultado("Precios", "✅ SUCCESS", f"ProductId: {product_id}")
        else:
            # Si falla con productId, intentar con itemId
            if item_id:
                st.warning(f"⚠️ ProductID {product_id} falló, intentando con ItemID...")
                url_item = f'https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/pricing/prices/{item_id}'
                resp_item = requests.get(url_item, headers=headers, timeout=15)
                
                if resp_item.status_code == 200:
                    st.success(f"✅ ACCESO EXITOSO a API de Precios (usando ItemID: {item_id})")
                    log_resultado("Precios", "✅ SUCCESS", f"ItemId: {item_id} (fallback)")
                else:
                    st.error(f"❌ ERROR en API de Precios - Status ProductID: {resp.status_code}, Status ItemID: {resp_item.status_code}")
                    log_resultado("Precios", "❌ ERROR", f"ProductID y ItemID fallaron")
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
    
    # Usar sales channel si está disponible, sino "1" por defecto
    seller = SALES_CHANNEL if SALES_CHANNEL and SALES_CHANNEL.strip() else "1"
    payload = {"items": [{"id": str(product_id), "quantity": 1, "seller": seller}]}

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
    reporte.append(f"Sales Channel: {SALES_CHANNEL if SALES_CHANNEL else 'Todos'}")
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
        product_id, reference_id, item_id = validar_productos()
        validar_clientes()
        validar_precios(product_id, item_id)
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

# Inicializar session state para clientes
if 'clientes_data' not in st.session_state:
    st.session_state.clientes_data = None
if 'df_clientes' not in st.session_state:
    st.session_state.df_clientes = None

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
registros_por_pagina = 100

campos_clientes = ['document', 'email', 'firstName', 'lastName', 'birthdate', 
                   'homePhone', 'gender', 'isNewsletterOptIn', 'updatedIn']

# Botón para ejecutar extracción
if st.button("📥 Extraer Clientes", type="primary", use_container_width=True):
    validar_credenciales()
    
    # Convertir fechas a ISO 8601 UTC para VTEX
    fecha_desde_iso = fecha_desde.strftime("%Y-%m-%dT00:00:00.000Z")
    fecha_hasta_iso = fecha_hasta.strftime("%Y-%m-%dT23:59:59.999Z")

    # Headers con credenciales ya definidas
    headers = {
        'x-vtex-api-appKey': VTEX_APP_KEY,
        'x-vtex-api-appToken': VTEX_APP_TOKEN,
        'Accept': 'application/vnd.vtex.ds.v10+json',
        'Content-Type': 'application/json',
        'REST-Range': f'resources=0-{registros_por_pagina}'
    }

    # URL de scroll histórico de clientes
    url = f'https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/dataentities/CL/scroll'

    # Parámetros para VTEX
    params = {
        '_fields': '_all',
        '_where': f"(updatedIn>{fecha_desde_iso} AND updatedIn<{fecha_hasta_iso}) OR ((updatedIn is null) AND (createdIn>{fecha_desde_iso} AND createdIn<{fecha_hasta_iso}))"
    }

    clientes = []
    token = None
    page_count = 0

    progress_text = st.empty()
    info_text = st.empty()

    with st.spinner('🔄 Extrayendo clientes de VTEX...'):
        while True:
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

    if clientes:
        # Filtrar solo los campos que queremos
        df = pd.DataFrame(clientes)
        df = df.reindex(columns=campos_clientes)

        # Guardar en session_state
        st.session_state.df_clientes = df
        st.session_state.clientes_data = {
            'total_clientes': len(df),
            'emails_validos': df['email'].notna().sum(),
            'paginas': page_count
        }
    else:
        st.warning("⚠️ No se recuperaron clientes para el rango de fechas indicado")

# Mostrar resultados si existen datos en session_state
if st.session_state.df_clientes is not None:
    data = st.session_state.clientes_data
    df = st.session_state.df_clientes
    
    st.success(f"🎉 Extracción completada: {data['total_clientes']} clientes recuperados")
    
    # Mostrar estadísticas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Clientes", data['total_clientes'])
    with col2:
        st.metric("Páginas Procesadas", data['paginas'])
    with col3:
        st.metric("Emails Válidos", data['emails_validos'])

    # Mostrar primeros 5 clientes
    st.markdown("#### 👀 Muestra de los primeros 5 clientes")
    st.dataframe(df.head(5), use_container_width=True)

    # Descarga
    csv_data = df.to_csv(index=False, encoding='utf-8')
    st.download_button(
        label="📥 Descargar CSV Completo de Clientes",
        data=csv_data,
        file_name=f"clientes_vtex_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True
    )

# ---------------------------------------------------------------------------------
# BLOQUE 3 - EXTRACCIÓN DE PRODUCTOS VTEX - VERSIÓN CORREGIDA (NO RESETEA LA APP)
# ---------------------------------------------------------------------------------

import streamlit as st
import requests
import pandas as pd
import time
import json
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from queue import Queue

st.markdown("---")
st.header("📦 Extracción de Productos VTEX")

# Inicializar session state
if 'productos_data' not in st.session_state:
    st.session_state.productos_data = None
if 'df_productos' not in st.session_state:
    st.session_state.df_productos = None
if 'paso_actual' not in st.session_state:
    st.session_state.paso_actual = 0
if 'extraccion_finalizada' not in st.session_state:
    st.session_state.extraccion_finalizada = False
if 'mostrar_descarga' not in st.session_state:
    st.session_state.mostrar_descarga = False

# Configuración
st.markdown("### ⚙️ Configuración de Extracción")

with st.expander("⚙️ Configuración Avanzada"):
    max_workers = st.slider("Requests concurrentes", 5, 50, 20, key="workers_productos")
    page_size = st.number_input("SKUs por página", 100, 1000, 1000, key="pagesize_productos")
    delay_between_pages = st.slider("Delay entre páginas (seg)", 0.0, 1.0, 0.1, 0.1, key="delay_productos")
    lote_guardado = st.number_input("Guardar progreso cada N SKUs", 500, 5000, 1000,
                                    help="Cada cuántos SKUs se guarda el progreso en disco",
                                    key="lote_productos")

# ================================================================================
# FUNCIONES DE GUARDADO/CARGA DE PROGRESO
# ================================================================================
CACHE_DIR = "vtex_cache"

def crear_cache_dir():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def guardar_progreso_productos(paso, datos, nombre_archivo):
    """Guarda progreso en archivo JSON"""
    crear_cache_dir()
    ruta = os.path.join(CACHE_DIR, nombre_archivo)
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    return ruta

def cargar_progreso_productos(nombre_archivo):
    """Carga progreso desde archivo JSON"""
    ruta = os.path.join(CACHE_DIR, nombre_archivo)
    if os.path.exists(ruta):
        with open(ruta, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def limpiar_cache_productos():
    """Limpia archivos de caché"""
    if os.path.exists(CACHE_DIR):
        for archivo in os.listdir(CACHE_DIR):
            os.remove(os.path.join(CACHE_DIR, archivo))
        st.success("🗑️ Caché limpiado")

# Rate limiting
rate_limit_lock = threading.Lock()
last_request_times = Queue(maxsize=10)

def rate_limited_request():
    with rate_limit_lock:
        current_time = time.time()
        if last_request_times.full():
            oldest = last_request_times.get()
            diff = current_time - oldest
            if diff < 1.0:
                time.sleep(1.0 - diff)
            current_time = time.time()
        last_request_times.put(current_time)

# ================================================================================
# PASO 0: CATEGORÍAS
# ================================================================================
def obtener_categorias_productos():
    st.info("🔄 Obteniendo categorías...")
    
    cache = cargar_progreso_productos("categorias.json")
    if cache:
        st.success(f"✅ {len(cache)} categorías (desde caché)")
        return cache
    
    category_map = {}
    headers = get_vtex_headers()
    headers['Accept'] = 'application/vnd.vtex.ds.v10+json'
    url = f'https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/catalog_system/pub/category/tree/10'
    
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 200:
            tree = resp.json()
            
            def extract_categories(nodes, parent_path=""):
                for node in nodes:
                    cat_id = node.get('id')
                    cat_name = node.get('name')
                    full_path = f"{parent_path} > {cat_name}" if parent_path else cat_name
                    if cat_id:
                        category_map[cat_id] = full_path
                    if node.get('children'):
                        extract_categories(node['children'], full_path)
            
            extract_categories(tree)
            guardar_progreso_productos(0, category_map, "categorias.json")
            st.success(f"✅ {len(category_map)} categorías")
        else:
            st.warning(f"⚠️ Error categorías: Status {resp.status_code}")
    except Exception as e:
        st.error(f"❌ Error: {e}")
    
    return category_map

# ================================================================================
# PASO 1: LISTAR SKU IDs
# ================================================================================
def listar_sku_ids_productos():
    st.info("🔄 PASO 1/4: Listando SKU IDs...")
    
    cache = cargar_progreso_productos("sku_ids.json")
    if cache:
        st.success(f"✅ {len(cache)} SKU IDs (desde caché)")
        return cache
    
    headers = get_vtex_headers()
    headers['Accept'] = 'application/json'
    
    all_ids = []
    page = 1
    status = st.empty()
    
    while True:
        url = f'https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/catalog_system/pvt/sku/stockkeepingunitids'
        params = {'page': page, 'pagesize': page_size}
        
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            if resp.status_code != 200:
                st.error(f"❌ Error en página {page}: {resp.status_code}")
                break
            
            ids = resp.json()
            if not ids:
                break
            
            all_ids.extend(ids)
            status.text(f"📄 Página {page} | Total: {len(all_ids)} SKUs")
            
            if page % 10 == 0:
                guardar_progreso_productos(1, all_ids, "sku_ids.json")
                st.info(f"💾 Progreso guardado: {len(all_ids)} IDs")
            
            if len(ids) < page_size:
                break
            
            page += 1
            time.sleep(delay_between_pages)
            
        except Exception as e:
            st.error(f"❌ Error: {e}")
            break
    
    guardar_progreso_productos(1, all_ids, "sku_ids.json")
    st.success(f"✅ PASO 1 COMPLETADO: {len(all_ids)} SKU IDs")
    return all_ids

# ================================================================================
# PASO 2: OBTENER DETALLES
# ================================================================================
def obtener_detalles_productos(sku_ids):
    st.info(f"🔄 PASO 2/4: Obteniendo detalles de {len(sku_ids)} SKUs...")
    
    cache = cargar_progreso_productos("sku_details.json")
    if cache:
        st.success(f"✅ {len(cache)} detalles (desde caché)")
        return cache
    
    detalles = []
    errores = 0
    
    progress = st.progress(0)
    status = st.empty()
    
    def fetch_detail(sku_id):
        rate_limited_request()
        url = f"https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/catalog_system/pvt/sku/stockkeepingunitbyid/{sku_id}"
        headers = get_vtex_headers()
        headers['Accept'] = 'application/vnd.vtex.ds.v10+json'
        
        for attempt in range(3):
            try:
                resp = requests.get(url, headers=headers, timeout=15)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 429:
                    time.sleep(2 ** attempt)
            except:
                if attempt < 2:
                    time.sleep(1)
        return None
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_detail, sid): sid for sid in sku_ids}
        
        for i, future in enumerate(as_completed(futures), 1):
            detail = future.result()
            if detail:
                detalles.append(detail)
            else:
                errores += 1
            
            progress.progress(i / len(sku_ids))
            status.text(f"⏳ {i}/{len(sku_ids)} | ❌ {errores} errores")
            
            if i % lote_guardado == 0:
                guardar_progreso_productos(2, detalles, "sku_details.json")
                st.info(f"💾 Progreso guardado: {len(detalles)} detalles")
    
    guardar_progreso_productos(2, detalles, "sku_details.json")
    st.success(f"✅ PASO 2 COMPLETADO: {len(detalles)} detalles | ❌ {errores} errores")
    return detalles

# ================================================================================
# PASO 3: OBTENER STOCK
# ================================================================================
def obtener_stock_productos(detalles):
    st.info(f"🔄 PASO 3/4: Obteniendo stock de {len(detalles)} SKUs...")
    
    cache = cargar_progreso_productos("stock_data.json")
    if cache:
        st.success(f"✅ Stock de {len(cache)} SKUs (desde caché)")
        return cache
    
    stock_data = {}
    
    progress = st.progress(0)
    status = st.empty()
    
    def fetch_stock(sku_id):
        rate_limited_request()
        url = f"https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/logistics/pvt/inventory/skus/{sku_id}"
        headers = get_vtex_headers()
        
        for attempt in range(2):
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    total = sum(wh.get('totalQuantity', 0) for wh in data.get('balance', []))
                    return {sku_id: total}
            except:
                pass
        return {sku_id: 0}
    
    sku_ids = [d.get('Id') for d in detalles if d.get('Id')]
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_stock, sid): sid for sid in sku_ids}
        
        for i, future in enumerate(as_completed(futures), 1):
            stock = future.result()
            stock_data.update(stock)
            
            progress.progress(i / len(sku_ids))
            status.text(f"⏳ {i}/{len(sku_ids)}")
            
            if i % lote_guardado == 0:
                guardar_progreso_productos(3, stock_data, "stock_data.json")
                st.info(f"💾 Progreso guardado: {len(stock_data)} stocks")
    
    guardar_progreso_productos(3, stock_data, "stock_data.json")
    st.success(f"✅ PASO 3 COMPLETADO: {len(stock_data)} stocks")
    return stock_data

# ================================================================================
# PASO 4: OBTENER PRECIOS
# ================================================================================
def obtener_precios_productos(detalles):
    st.info(f"🔄 PASO 4/4: Obteniendo precios de {len(detalles)} SKUs...")
    
    cache = cargar_progreso_productos("price_data.json")
    if cache:
        st.success(f"✅ Precios de {len(cache)} SKUs (desde caché)")
        return cache
    
    price_data = {}
    
    progress = st.progress(0)
    status = st.empty()
    
    def fetch_price(sku_id):
        rate_limited_request()
        url = f"https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/pricing/prices/{sku_id}"
        headers = get_vtex_headers()
        
        for attempt in range(2):
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    price = data.get('basePrice') or data.get('listPrice') or data.get('costPrice') or 0
                    return {sku_id: price}
            except:
                pass
        return {sku_id: 0}
    
    sku_ids = [d.get('Id') for d in detalles if d.get('Id')]
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_price, sid): sid for sid in sku_ids}
        
        for i, future in enumerate(as_completed(futures), 1):
            price = future.result()
            price_data.update(price)
            
            progress.progress(i / len(sku_ids))
            status.text(f"⏳ {i}/{len(sku_ids)}")
            
            if i % lote_guardado == 0:
                guardar_progreso_productos(4, price_data, "price_data.json")
                st.info(f"💾 Progreso guardado: {len(price_data)} precios")
    
    guardar_progreso_productos(4, price_data, "price_data.json")
    st.success(f"✅ PASO 4 COMPLETADO: {len(price_data)} precios")
    return price_data

# ================================================================================
# INTERFAZ PRINCIPAL
# ================================================================================

st.markdown("### 🎮 Control de Extracción")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🚀 INICIAR EXTRACCIÓN", type="primary", use_container_width=True, key="btn_iniciar"):
        validar_credenciales()
        st.session_state.paso_actual = 1

with col2:
    if st.button("♻️ CONTINUAR DESDE CACHÉ", use_container_width=True, key="btn_continuar"):
        validar_credenciales()
        st.session_state.paso_actual = 2

with col3:
    if st.button("🗑️ LIMPIAR CACHÉ", use_container_width=True, key="btn_limpiar"):
        limpiar_cache_productos()
        st.session_state.paso_actual = 0
        st.session_state.extraccion_finalizada = False
        st.session_state.mostrar_descarga = False

# Mostrar estado del caché
if os.path.exists(CACHE_DIR):
    archivos = os.listdir(CACHE_DIR)
    if archivos:
        with st.expander("💾 Estado del Caché"):
            for archivo in archivos:
                ruta = os.path.join(CACHE_DIR, archivo)
                tamaño = os.path.getsize(ruta) / 1024  # KB
                st.text(f"• {archivo}: {tamaño:.1f} KB")

# Ejecutar extracción
if st.session_state.paso_actual > 0:
    try:
        category_map = obtener_categorias_productos()
        
        sku_ids = listar_sku_ids_productos()
        if not sku_ids:
            st.error("❌ No se obtuvieron SKU IDs")
            st.session_state.paso_actual = 0
            st.stop()
        
        detalles = obtener_detalles_productos(sku_ids)
        if not detalles:
            st.error("❌ No se obtuvieron detalles de productos")
            st.session_state.paso_actual = 0
            st.stop()
        
        stock_data = obtener_stock_productos(detalles)
        price_data = obtener_precios_productos(detalles)
        
        st.info("🔄 Generando DataFrame final con todos los datos...")
        
        rows = []
        for d in detalles:
            sku_id = d.get('Id')
            product_id = d.get('ProductId')
            
            category_id = ''
            category_name = ''
            product_categories = d.get('ProductCategories', {})
            if product_categories and isinstance(product_categories, dict):
                cat_ids_list = list(product_categories.keys())
                if cat_ids_list:
                    category_id = cat_ids_list[-1]
                    category_path_parts = []
                    for cat_id_item in cat_ids_list:
                        cat_name_item = product_categories.get(cat_id_item, '')
                        if cat_name_item:
                            category_path_parts.append(cat_name_item)
                    if category_path_parts:
                        category_name = " > ".join(category_path_parts)
            
            rows.append({
                'productId': product_id,
                'productReference': d.get('ProductRefId', ''),
                'skuId': sku_id,
                'skuRefId': d.get('AlternateIds', {}).get('RefId', '') if isinstance(d.get('AlternateIds'), dict) else '',
                'skuName': d.get('SkuName', ''),
                'productName': d.get('ProductName', ''),
                'brandName': d.get('BrandName', ''),
                'categoryId': category_id,
                'categoryName': category_name,
                'ean': d.get('Ean', ''),
                'isActive': d.get('IsActive', False),
                'availableQuantity': stock_data.get(sku_id, 0),
                'price': price_data.get(sku_id, 0)
            })
        
        df = pd.DataFrame(rows)
        st.session_state.df_productos = df

        # 🔥 CORRECCIÓN: NO reiniciar flujo, no perder el botón
        st.session_state.paso_actual = 99
        st.session_state.extraccion_finalizada = True
        st.session_state.mostrar_descarga = True
        
        st.session_state.productos_data = {
            'total_skus': len(df),
            'total_activos': df['isActive'].sum(),
            'total_con_stock': (df['availableQuantity'] > 0).sum(),
            'total_con_precio': (df['price'] > 0).sum()
        }
        
        st.success("🎉 EXTRACCIÓN COMPLETADA")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total SKUs", len(df))
        col2.metric("Activos", int(df['isActive'].sum()))
        col3.metric("Con Stock", int((df['availableQuantity'] > 0).sum()))
        col4.metric("Con Precio", int((df['price'] > 0).sum()))
        
        with st.expander("📊 Análisis Detallado"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Stock**")
                total_stock = df['availableQuantity'].sum()
                avg_stock = df[df['availableQuantity'] > 0]['availableQuantity'].mean()
                st.metric("Stock Total", f"{total_stock:,.0f}")
                st.metric("Promedio Stock", f"{avg_stock:,.1f}" if not pd.isna(avg_stock) else "0")
            
            with col2:
                st.markdown("**Precios**")
                avg_price = df[df['price'] > 0]['price'].mean()
                max_price = df['price'].max()
                st.metric("Precio Promedio", f"${avg_price:,.2f}" if not pd.isna(avg_price) else "$0.00")
                st.metric("Precio Máximo", f"${max_price:,.2f}" if not pd.isna(max_price) else "$0.00")
        
        st.markdown("#### 👀 Muestra de productos")
        st.dataframe(df.head(20), use_container_width=True)
        
        if st.session_state.mostrar_descarga:
            csv = df.to_csv(index=False, encoding='utf-8')
            st.download_button(
                "📥 DESCARGAR CSV COMPLETO",
                csv,
                f"productos_vtex_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv",
                use_container_width=True,
                key="btn_download_productos"
            )
        
    except Exception as e:
        st.error(f"❌ Error durante la extracción: {str(e)}")
        st.info("💡 Usa 'CONTINUAR DESDE CACHÉ' para reanudar desde el último punto guardado")
        import traceback
        with st.expander("🔍 Ver detalle técnico del error"):
            st.code(traceback.format_exc())

# Mostrar resultados anteriores cuando ya terminó
elif st.session_state.df_productos is not None:
    st.info("📋 Mostrando resultados de extracción anterior")
    
    data = st.session_state.productos_data
    df = st.session_state.df_productos
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total SKUs", data['total_skus'])
    col2.metric("Activos", data['total_activos'])
    col3.metric("Con Stock", data['total_con_stock'])
    col4.metric("Con Precio", data['total_con_precio'])
    
    st.dataframe(df.head(20), use_container_width=True)
    
    if st.session_state.mostrar_descarga:
        csv = df.to_csv(index=False, encoding='utf-8')
        st.download_button(
            "📥 DESCARGAR CSV",
            csv,
            f"productos_vtex_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv",
            use_container_width=True,
            key="btn_download_productos_cached"
        )

# ---------------------------------------------------------------------------------
# CUARTO BLOQUE: EXTRACCIÓN DE VENTAS (MEJORADO Y CORREGIDO)
# ---------------------------------------------------------------------------------
st.markdown("---")
st.markdown("---")
st.header("💰 Extracción de Ventas")

# Inicializar session state para ventas
if 'ventas_data' not in st.session_state:
    st.session_state.ventas_data = None
if 'df_ventas' not in st.session_state:
    st.session_state.df_ventas = None

st.markdown("### 📅 Configuración de Filtros")

col1, col2 = st.columns(2)

with col1:
    fecha_desde_ventas = st.date_input(
        "📅 Fecha desde (creationDate)", 
        value=datetime(2025, 1, 1),
        help="Fecha mínima de creación de órdenes",
        key="ventas_desde"
    )

with col2:
    fecha_hasta_ventas = st.date_input(
        "📅 Fecha hasta (creationDate)", 
        value=datetime.today(),
        help="Fecha máxima de creación de órdenes",
        key="ventas_hasta"
    )

# NUEVA FUNCIONALIDAD: Filtro de status
st.markdown("### 🏷️ Filtro de Status de Órdenes")
status_opciones = [
    "payment-approved",
    "ready-for-handling",
    "handling",
    "invoiced"
]

status_seleccionados = st.multiselect(
    "Selecciona uno o más status de órdenes",
    options=status_opciones,
    default=["payment-approved","ready-for-handling", "handling", "invoiced"],
    help="Puedes seleccionar múltiples status. Si no seleccionas ninguno, se usarán los 3 por defecto."
)

# Configuración de workers para requests concurrentes
with st.expander("⚙️ Configuración Avanzada"):
    max_workers = st.slider("Requests concurrentes", min_value=1, max_value=20, value=10, 
                            help="Cantidad de requests simultáneos para detalles de órdenes")
    sales_window_hours = st.number_input("Ventana de tiempo (horas)", min_value=1, max_value=720, value=24,
                                         help="Tamaño de ventana temporal para dividir la consulta si supera el límite de paginación")

# Constantes
VTEX_PAGE_LIMIT = 30  # Límite de páginas de VTEX

if st.button("📥 Extraer Ventas", type="primary", use_container_width=True, key="btn_extraer_ventas"):
    validar_credenciales()
    
    st.info("🔄 Extrayendo órdenes con ventanas de tiempo adaptativas...")
    
    # Headers
    headers_ventas = get_vtex_headers()
    
    # ===== FETCH ÓRDENES CON VENTANAS TEMPORALES (CORREGIDO) =====
    all_orders = []
    
    # Convertir fechas a datetime con hora
    fecha_inicio = datetime.combine(fecha_desde_ventas, datetime.min.time())
    fecha_fin = datetime.combine(fecha_hasta_ventas, datetime.max.time())
    
    current_from = fecha_inicio
    interval_hours = sales_window_hours
    
    progress_text_ventas = st.empty()
    info_text_ventas = st.empty()
    window_count = 0
    
    with st.spinner('💰 Extrayendo órdenes de VTEX con ventanas adaptativas...'):
        while current_from < fecha_fin:
            window_count += 1
            current_to = min(current_from + timedelta(hours=interval_hours), fecha_fin)
            
            # Convertir a formato ISO
            fecha_desde_iso = current_from.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            fecha_hasta_iso = current_to.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            
            progress_text_ventas.text(f"🕐 Ventana {window_count}: {fecha_desde_iso[:10]} - {fecha_hasta_iso[:10]} ({interval_hours}h)")
            
            # Parámetros base
            params = {
                "orderBy": "creationDate,asc",
                "f_creationDate": f"creationDate:[{fecha_desde_iso} TO {fecha_hasta_iso}]",
                "per_page": 100
            }
            
            # Aplicar filtro de status
            if status_seleccionados:
                params["f_status"] = ",".join(status_seleccionados)
            else:
                params["f_status"] = "payment-approved,ready-for-handling,handling,invoiced"
            
            # Solo agregar sales channel si no está vacío
            if SALES_CHANNEL and SALES_CHANNEL.strip():
                params["f_salesChannel"] = SALES_CHANNEL
            
            # Intentar obtener órdenes de esta ventana
            page = 1
            ventana_procesada = False
            
            while not ventana_procesada:
                params["page"] = page
                
                try:
                    url_orders = f"https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/oms/pvt/orders"
                    resp = requests.get(url_orders, headers=headers_ventas, params=params, timeout=30)
                    
                    if resp.status_code != 200:
                        st.error(f"❌ Error en ventana {window_count}, página {page}: Status {resp.status_code}")
                        with st.expander("Ver detalle del error"):
                            st.code(resp.text[:500])
                        ventana_procesada = True
                        break
                    
                    data = resp.json()
                    orders = data.get("list", [])
                    paging = data.get("paging", {})
                    total_pages = paging.get("pages", 0)
                    total_orders = paging.get("total", 0)
                    
                    # CRITICAL: Si se supera el límite de páginas de VTEX, reducir ventana
                    if page == 1 and total_pages > VTEX_PAGE_LIMIT:
                        st.warning(f"⚠️ Límite de páginas alcanzado ({total_pages} > {VTEX_PAGE_LIMIT}). Dividiendo ventana temporal...")
                        interval_hours = max(1, interval_hours // 2)  # Reducir a la mitad, mínimo 1 hora
                        
                        if interval_hours < 1:
                            st.error("❌ No se puede reducir más la ventana temporal. Hay demasiadas órdenes en un período muy corto.")
                            ventana_procesada = True
                            break
                        
                        # Recalcular current_to con nuevo intervalo
                        current_to = min(current_from + timedelta(hours=interval_hours), fecha_fin)
                        fecha_hasta_iso = current_to.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                        params["f_creationDate"] = f"creationDate:[{fecha_desde_iso} TO {fecha_hasta_iso}]"
                        
                        info_text_ventas.warning(f"🔄 Nueva ventana: {interval_hours} hora(s)")
                        page = 1  # Reiniciar paginación
                        continue
                    
                    # Agregar órdenes
                    if orders:
                        all_orders.extend(orders)
                        info_text_ventas.info(f"✅ Ventana {window_count}, Página {page}/{total_pages}: {len(orders)} órdenes | Total acumulado: {len(all_orders)}")
                    
                    # Verificar si hay más páginas
                    if page >= total_pages or len(orders) == 0:
                        ventana_procesada = True
                        break
                    
                    page += 1
                    time.sleep(0.3)
                    
                except requests.exceptions.Timeout:
                    st.error(f"⏱️ Timeout en ventana {window_count}, página {page}. Reintentando...")
                    time.sleep(2)
                    continue
                except Exception as e:
                    st.error(f"❌ Excepción en ventana {window_count}, página {page}: {str(e)}")
                    ventana_procesada = True
                    break
            
            # Avanzar al siguiente intervalo
            current_from = current_to
            time.sleep(0.5)  # Pausa entre ventanas
    
    info_text_ventas.success(f"✅ Extracción completada: {len(all_orders)} órdenes en {window_count} ventanas")
    
    # ===== FETCH DETALLES CON CONCURRENCIA =====
    # Eliminar duplicados antes de procesar
    unique_order_ids = list(set([o.get("orderId") for o in all_orders]))
    if len(unique_order_ids) < len(all_orders):
        st.warning(f"⚠️ Se eliminaron {len(all_orders) - len(unique_order_ids)} órdenes duplicadas")
        all_orders = [{"orderId": oid} for oid in unique_order_ids]
    
    if all_orders:
        st.info(f"🔄 Paso 2/2: Obteniendo detalles de {len(all_orders)} órdenes (concurrente)...")
        
        detalles = []
        progress_bar_detalles = st.progress(0)
        status_text = st.empty()
        
        def fetch_order_detail_local(order_id):
            """Función local para fetch de detalle"""
            url_detail = f"https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/oms/pvt/orders/{order_id}"
            try:
                resp = requests.get(url_detail, headers=headers_ventas, timeout=20)
                if resp.status_code == 200:
                    return resp.json()
                return None
            except:
                return None
        
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_order = {
                executor.submit(fetch_order_detail_local, o.get("orderId")): o 
                for o in all_orders
            }
            
            completed = 0
            for future in as_completed(future_to_order):
                detalle = future.result()
                if detalle:
                    detalles.append(detalle)
                completed += 1
                
                # Actualizar progreso
                progress_pct = completed / len(all_orders)
                progress_bar_detalles.progress(progress_pct)
                status_text.text(f"⏳ Procesadas {completed}/{len(all_orders)} órdenes")
        
        st.success(f"✅ Detalles obtenidos: {len(detalles)} órdenes")
        
        # ===== PROCESAR Y EXPORTAR =====
        if detalles:
            st.info("🔄 Procesando datos y generando CSV...")
            
            ventas_rows = []
            
            for order in detalles:
                order_id = order.get("orderId", "N/A")
                status = order.get("status", "N/A")
                creation = order.get("creationDate", "N/A")
                sales_channel = order.get("salesChannel", "N/A")
                total_value = order.get("value", "N/A")
                
                client = order.get("clientProfileData", {})
                client_email = client.get("email", "N/A")
                client_first = client.get("firstName", "N/A")
                client_last = client.get("lastName", "N/A")
                client_doc = client.get("document", "N/A")
                
                items = order.get("items", [])
                
                if not items:
                    ventas_rows.append([
                        order_id, status, creation, sales_channel, total_value,
                        client_email, client_first, client_last, client_doc,
                        "N/A", "N/A", "N/A", "N/A", 0, 0
                    ])
                else:
                    for item in items:
                        # Extraer todos los identificadores posibles del item
                        product_id = item.get("productId", "N/A")
                        sku_id = item.get("id", "N/A")  # Este es el SKU ID
                        ref_id = item.get("refId", "N/A")
                        name = item.get("name", "N/A")
                        qty = item.get("quantity", 0)
                        price = item.get("price", 0)
                        
                        ventas_rows.append([
                            order_id, status, creation, sales_channel, total_value,
                            client_email, client_first, client_last, client_doc,
                            product_id, sku_id, ref_id, name, qty, price
                        ])
            
            # Crear DataFrame y guardar en session_state
            st.session_state.df_ventas = pd.DataFrame(
                ventas_rows,
                columns=[
                    'orderId', 'status', 'creationDate', 'salesChannel', 'value',
                    'client_email', 'client_firstName', 'client_lastName', 'client_document',
                    'productId', 'skuId', 'refId', 'item_name', 'item_quantity', 'item_price'
                ]
            )
            
            st.session_state.ventas_data = {
                'total_ordenes': len(detalles),
                'total_items': len(ventas_rows)
            }
        else:
            st.warning("⚠️ No se obtuvieron detalles de órdenes")
    else:
        st.warning("⚠️ No se recuperaron órdenes para el rango de fechas indicado")

# Mostrar resultados si existen datos en session_state
if st.session_state.df_ventas is not None:
    data = st.session_state.ventas_data
    df_ventas = st.session_state.df_ventas
    
    st.success(f"🎉 Extracción completada: {data['total_ordenes']} órdenes | {data['total_items']} items")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Órdenes", data['total_ordenes'])
    with col2:
        st.metric("Total Items", data['total_items'])
    with col3:
        # Calcular valor total (VTEX guarda en centavos)
        try:
            total_value = df_ventas['value'].astype(float).sum() / 100
            st.metric("Valor Total", f"${total_value:,.2f}")
        except:
            st.metric("Valor Total", "N/A")
    
    # Mostrar muestra
    st.markdown("#### 👀 Muestra de las primeras 5 ventas")
    st.dataframe(df_ventas.head(5), use_container_width=True)
    
    # Descarga
    csv_ventas = df_ventas.to_csv(index=False, encoding='utf-8')
    st.download_button(
        label="📥 Descargar CSV de Ventas",
        data=csv_ventas,
        file_name=f"ventas_vtex_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True
    )