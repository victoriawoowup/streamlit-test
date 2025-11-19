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
# TERCER BLOQUE: EXTRACCIÓN DE PRODUCTOS (VERSIÓN DUAL: TODOS O SOLO ACTIVOS)
# ---------------------------------------------------------------------------------
st.markdown("---")
st.markdown("---")
st.header("📦 Extracción de Productos")

# Inicializar session state para productos
if 'productos_data' not in st.session_state:
    st.session_state.productos_data = None
if 'df_productos' not in st.session_state:
    st.session_state.df_productos = None
if 'df_atributos' not in st.session_state:
    st.session_state.df_atributos = None

st.markdown("### ⚙️ Configuración de Extracción")

# Configuración de workers para requests concurrentes
with st.expander("⚙️ Configuración Avanzada"):
    max_workers_productos = st.slider("Requests concurrentes para productos", min_value=1, max_value=30, value=15, 
                            help="Cantidad de requests simultáneos para obtener detalles de SKUs")
    page_size = st.number_input("SKUs por página", min_value=1, max_value=1000, value=500,
                                help="Cantidad de SKUs a obtener por cada request de listado")

# Selector del tipo de extracción
st.markdown("### 📊 Selecciona el tipo de extracción")
col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    btn_todos = st.button("📥 Extraer TODOS los Productos", type="primary", use_container_width=True,
                          help="Extrae todos los SKUs (activos e inactivos) usando el endpoint completo")

with col_btn2:
    btn_activos = st.button("✅ Extraer Solo ACTIVOS", type="secondary", use_container_width=True,
                            help="Extrae solo productos activos usando el endpoint público")

# ====================================================================================
# FUNCIÓN COMÚN: OBTENER ÁRBOL DE CATEGORÍAS
# ====================================================================================
def obtener_categorias():
    """Obtiene el árbol de categorías de VTEX"""
    st.info("🔄 Obteniendo árbol de categorías...")
    
    category_map = {}
    headers_cat = get_vtex_headers()
    headers_cat['Accept'] = 'application/vnd.vtex.ds.v10+json'
    headers_cat['REST-Range'] = 'resources=0-10'
    url_categorias = f'https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/catalog_system/pub/category/tree/10'
    
    try:
        resp_cat = requests.get(url_categorias, headers=headers_cat, timeout=30)
        if resp_cat.status_code == 200:
            tree = resp_cat.json()
            
            def extract_categories(nodes, parent_path=""):
                for node in nodes:
                    cat_id = node.get('id')
                    cat_name = node.get('name')
                    full_path = f"{parent_path} > {cat_name}" if parent_path else cat_name
                    if cat_id:
                        category_map[cat_id] = full_path
                    children = node.get('children', [])
                    if children:
                        extract_categories(children, full_path)
            
            extract_categories(tree)
            st.success(f"✅ {len(category_map)} categorías cargadas")
        else:
            st.warning("⚠️ No se pudieron cargar categorías")
    except Exception as e:
        st.error(f"❌ Error cargando categorías: {e}")
    
    time.sleep(0.3)
    return category_map

# ====================================================================================
# OPCIÓN 1: EXTRAER TODOS LOS PRODUCTOS (ACTIVOS E INACTIVOS)
# ====================================================================================
if btn_todos:
    validar_credenciales()
    
    # PASO 1: OBTENER CATEGORÍAS
    category_map = obtener_categorias()
    
    # PASO 2: OBTENER LISTA DE TODOS LOS SKU IDs
    st.info("🔄 Paso 1/5: Obteniendo lista completa de SKU IDs...")
    
    headers_productos = get_vtex_headers()
    all_sku_ids = []
    page = 1
    
    progress_text_skus = st.empty()
    info_text_skus = st.empty()
    
    with st.spinner('📋 Listando todos los SKU IDs...'):
        while True:
            url_sku_list = f'https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/catalog_system/pvt/sku/stockkeepingunitids'
            params = {
                'page': page,
                'pagesize': page_size
            }
            
            try:
                resp = requests.get(url_sku_list, headers=headers_productos, params=params, timeout=30)
                
                if resp.status_code != 200:
                    st.error(f"❌ Error obteniendo SKU IDs en página {page}: Status {resp.status_code}")
                    with st.expander("Ver detalle del error"):
                        st.code(resp.text[:500])
                    break
                
                sku_ids = resp.json()
                
                if not sku_ids or len(sku_ids) == 0:
                    info_text_skus.success("✅ Se obtuvieron todos los SKU IDs")
                    break
                
                all_sku_ids.extend(sku_ids)
                
                progress_text_skus.text(f"📄 Página {page}")
                info_text_skus.info(f"✅ {len(sku_ids)} SKUs en esta página | Total acumulado: {len(all_sku_ids)}")
                
                if len(sku_ids) < page_size:
                    info_text_skus.success("✅ Se obtuvieron todos los SKU IDs")
                    break
                
                page += 1
                time.sleep(0.3)
                
            except requests.exceptions.Timeout:
                st.error(f"⏱️ Timeout en página {page}. Reintentando...")
                time.sleep(2)
                continue
            except Exception as e:
                st.error(f"❌ Excepción obteniendo SKU IDs en página {page}: {str(e)}")
                break
    
    if not all_sku_ids:
        st.error("❌ No se pudo obtener ningún SKU ID")
        st.stop()
    
    st.success(f"✅ Total de SKU IDs obtenidos: {len(all_sku_ids)}")
    
    # PASO 3: OBTENER DETALLES DE CADA SKU (CONCURRENTE)
    st.info(f"🔄 Paso 2/5: Obteniendo detalles de {len(all_sku_ids)} SKUs (concurrente)...")
    
    sku_details = []
    progress_bar_details = st.progress(0)
    status_text_details = st.empty()
    
    def fetch_sku_detail(sku_id):
        """Función para obtener detalle de un SKU"""
        url = f"https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/catalog_system/pvt/sku/stockkeepingunitbyid/{sku_id}"
        headers = get_vtex_headers()
        headers['Accept'] = 'application/vnd.vtex.ds.v10+json'
        
        try:
            resp = requests.get(url, headers=headers, timeout=20)
            if resp.status_code == 200:
                return resp.json()
            return None
        except:
            return None
    
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    with ThreadPoolExecutor(max_workers=max_workers_productos) as executor:
        future_to_sku = {
            executor.submit(fetch_sku_detail, sku_id): sku_id 
            for sku_id in all_sku_ids
        }
        
        completed = 0
        for future in as_completed(future_to_sku):
            detail = future.result()
            if detail:
                sku_details.append(detail)
            completed += 1
            
            progress_pct = completed / len(all_sku_ids)
            progress_bar_details.progress(progress_pct)
            status_text_details.text(f"⏳ Procesados {completed}/{len(all_sku_ids)} SKUs")
    
    st.success(f"✅ Detalles obtenidos: {len(sku_details)} SKUs")
    
    # PASO 4: OBTENER STOCK DE CADA SKU (CONCURRENTE)
    st.info(f"🔄 Paso 3/5: Obteniendo stock de {len(sku_details)} SKUs (concurrente)...")
    
    stock_data = {}
    progress_bar_stock = st.progress(0)
    status_text_stock = st.empty()
    
    def fetch_sku_stock(sku_id):
        """Función para obtener stock de un SKU"""
        url = f"https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/logistics/pvt/inventory/skus/{sku_id}"
        headers = get_vtex_headers()
        
        try:
            resp = requests.get(url, headers=headers, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                total_balance = sum([wh.get('totalQuantity', 0) for wh in data.get('balance', [])])
                return {sku_id: total_balance}
            return {sku_id: 0}
        except:
            return {sku_id: 0}
    
    with ThreadPoolExecutor(max_workers=max_workers_productos) as executor:
        future_to_sku_stock = {
            executor.submit(fetch_sku_stock, detail.get('Id')): detail.get('Id') 
            for detail in sku_details if detail.get('Id')
        }
        
        completed = 0
        for future in as_completed(future_to_sku_stock):
            stock_info = future.result()
            if stock_info:
                stock_data.update(stock_info)
            completed += 1
            
            progress_pct = completed / len(sku_details)
            progress_bar_stock.progress(progress_pct)
            status_text_stock.text(f"⏳ Procesados {completed}/{len(sku_details)} SKUs")
    
    st.success(f"✅ Stock obtenido: {len(stock_data)} SKUs")
    
    # PASO 5: OBTENER ATRIBUTOS Y COLECCIONES DESDE ENDPOINT PÚBLICO
    st.info(f"🔄 Paso 4/5: Obteniendo atributos y colecciones desde endpoint público...")
    
    unique_product_ids = list(set([d.get('ProductId') for d in sku_details if d.get('ProductId')]))
    
    product_enriched_data = {}
    progress_bar_enriched = st.progress(0)
    status_text_enriched = st.empty()
    
    def fetch_product_public(product_id):
        """Función para obtener info pública del producto (atributos y colecciones)"""
        url = f"https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/catalog_system/pub/products/search?fq=productId:{product_id}"
        headers = get_vtex_headers()
        
        try:
            resp = requests.get(url, headers=headers, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                if data and len(data) > 0:
                    product = data[0]
                    
                    # Extraer atributos
                    atributos = {}
                    all_specs = product.get("allSpecifications", [])
                    for spec in all_specs:
                        valores = product.get(spec, [])
                        if isinstance(valores, list):
                            atributos[spec] = valores
                        else:
                            atributos[spec] = [valores]
                    
                    if product.get("complementName"):
                        atributos["nombreComplementario"] = [product.get("complementName")]
                    
                    # Extraer colecciones
                    colecciones = []
                    if product.get("productClusters"):
                        colecciones = list(product["productClusters"].values())
                    
                    return {
                        product_id: {
                            'atributos': atributos,
                            'colecciones': colecciones
                        }
                    }
            return {product_id: {'atributos': {}, 'colecciones': []}}
        except:
            return {product_id: {'atributos': {}, 'colecciones': []}}
    
    with ThreadPoolExecutor(max_workers=max_workers_productos) as executor:
        future_to_product = {
            executor.submit(fetch_product_public, prod_id): prod_id 
            for prod_id in unique_product_ids
        }
        
        completed = 0
        for future in as_completed(future_to_product):
            enriched = future.result()
            if enriched:
                product_enriched_data.update(enriched)
            completed += 1
            
            progress_pct = completed / len(unique_product_ids)
            progress_bar_enriched.progress(progress_pct)
            status_text_enriched.text(f"⏳ Procesados {completed}/{len(unique_product_ids)} productos")
    
    st.success(f"✅ Atributos y colecciones obtenidos: {len(product_enriched_data)} productos")
    
    # PASO 6: PROCESAR Y GENERAR CSV
    st.info("🔄 Paso 5/5: Procesando datos y generando CSV...")
    
    # Extraer todos los atributos únicos para las columnas
    all_attributes = set()
    for prod_data in product_enriched_data.values():
        all_attributes.update(prod_data['atributos'].keys())
    
    attr_headers = [f"atributo.{a}" for a in sorted(all_attributes)]
    
    productos_rows = []
    
    for detail in sku_details:
        sku_id = detail.get('Id', 'N/A')
        product_id = detail.get('ProductId', 'N/A')
        sku_name = detail.get('Name', 'N/A')
        product_name = detail.get('ProductName', 'N/A')
        product_reference = detail.get('ProductRefId', 'N/A')
        ref_id = detail.get('RefId', 'N/A')
        brand_name = detail.get('BrandName', 'N/A')
        category_id = detail.get('CategoryId', 'N/A')
        ean = detail.get('Ean', 'N/A')
        is_active = detail.get('IsActive', False)
        
        available_quantity = stock_data.get(sku_id, 0)
        description = detail.get('ProductDescription', '') or detail.get('Description', '')
        category_name = category_map.get(int(category_id), 'N/A') if category_id != 'N/A' else 'N/A'
        
        enriched = product_enriched_data.get(product_id, {'atributos': {}, 'colecciones': []})
        atributos = enriched['atributos']
        colecciones = enriched['colecciones']
        colecciones_str = ", ".join(colecciones) if colecciones else 'N/A'
        
        # Construir valores de atributos
        attr_values = []
        for a in sorted(all_attributes):
            val = atributos.get(a, [])
            if isinstance(val, list):
                attr_values.append(", ".join(str(v) for v in val))
            else:
                attr_values.append(str(val))
        
        productos_rows.append([
            product_id, product_reference, sku_id, ref_id, sku_name,
            product_name, description[:500] if description else '', 
            brand_name, category_id, category_name, ean, is_active, 
            available_quantity, colecciones_str
        ] + attr_values)
    
    # Crear DataFrame y guardar en session_state
    st.session_state.df_productos = pd.DataFrame(
        productos_rows,
        columns=[
            'productId', 'productReference', 'skuId', 'refId', 'skuName',
            'productName', 'description', 'brandName', 'categoryId', 'categoryName', 
            'ean', 'isActive', 'availableQuantity', 'colecciones'
        ] + attr_headers
    )
    
    # Crear DataFrame de atributos
    atributos_info = []
    for a in sorted(all_attributes):
        valores = set()
        for prod_data in product_enriched_data.values():
            vals = prod_data['atributos'].get(a, [])
            if vals:
                valores.update(str(v) for v in vals)
        atributos_info.append({
            "atributo": f"atributo.{a}",
            "valores_ejemplo": ", ".join(list(valores)[:10])
        })
    
    st.session_state.df_atributos = pd.DataFrame(atributos_info)
    
    st.session_state.productos_data = {
        'total_skus': len(sku_details),
        'total_activos': sum(1 for row in productos_rows if row[11] is True),
        'total_con_stock': sum(1 for row in productos_rows if row[12] > 0),
        'total_atributos': len(all_attributes),
        'tipo_extraccion': 'TODOS'
    }

# ====================================================================================
# OPCIÓN 2: EXTRAER SOLO PRODUCTOS ACTIVOS
# ====================================================================================
elif btn_activos:
    validar_credenciales()
    
    # PASO 1: OBTENER CATEGORÍAS
    category_map = obtener_categorias()
    
    # PASO 2: FETCH PRODUCTOS ACTIVOS (ENDPOINT PÚBLICO)
    st.info("🔄 Paso 1/2: Extrayendo productos activos desde endpoint público...")
    
    headers_productos = get_vtex_headers()
    headers_productos['Accept'] = 'application/vnd.vtex.ds.v10+json'
    
    productos = []
    from_index = 0
    page_count = 0
    productos_por_pagina = 50
    
    progress_text_prod = st.empty()
    info_text_prod = st.empty()
    
    with st.spinner('📦 Extrayendo productos activos de VTEX...'):
        while True:
            page_count += 1
            to_index = from_index + productos_por_pagina - 1
            
            url_productos = f'https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/catalog_system/pub/products/search?_from={from_index}&_to={to_index}'
            
            try:
                resp_prod = requests.get(url_productos, headers=headers_productos, timeout=30)
                
                if resp_prod.status_code not in [200, 206]:
                    st.error(f"❌ Error en página {page_count}: Status {resp_prod.status_code}")
                    break
                
                products_page = resp_prod.json()
                
                if not products_page or len(products_page) == 0:
                    info_text_prod.success("✅ No hay más productos para procesar")
                    break
                
                productos.extend(products_page)
                
                progress_text_prod.text(f"📄 Página {page_count}")
                info_text_prod.info(f"✅ {len(products_page)} productos en esta página | Total acumulado: {len(productos)}")
                
                if len(products_page) < productos_por_pagina:
                    info_text_prod.success("✅ Se procesaron todos los productos activos disponibles")
                    break
                
                from_index = to_index + 1
                time.sleep(0.5)
                
            except requests.exceptions.Timeout:
                st.error(f"⏱️ Timeout en página {page_count}. Reintentando...")
                time.sleep(2)
                continue
            except Exception as e:
                st.error(f"❌ Excepción en página {page_count}: {str(e)}")
                break
    
    if not productos:
        st.error("❌ No se pudieron obtener productos activos")
        st.stop()
    
    # PASO 3: PROCESAR Y EXPORTAR
    st.info("🔄 Paso 2/2: Procesando datos y generando CSVs...")
    
    # Extraer atributos de todos los productos
    all_attributes = set()
    for producto in productos:
        atributos = {}
        all_specs = producto.get("allSpecifications", [])
        for spec in all_specs:
            valores = producto.get(spec, [])
            if isinstance(valores, list):
                atributos[spec] = valores
            else:
                atributos[spec] = [valores]
        
        if producto.get("complementName"):
            atributos["nombreComplementario"] = [producto.get("complementName")]
        if producto.get("productClusters"):
            atributos["colecciones"] = list(producto["productClusters"].values())
        
        producto["_atributos"] = atributos
        all_attributes.update(atributos.keys())
    
    # Generar CSV de productos
    attr_headers = [f"atributo.{a}" for a in sorted(all_attributes)]
    
    productos_rows = []
    for producto in productos:
        product_id = producto.get('productId', 'N/A')
        product_name = producto.get('productName', 'N/A')
        product_reference = producto.get('productReference', 'N/A')
        brand = producto.get('brand', 'N/A')
        category_id = producto.get('categoryId', 'N/A')
        description = producto.get('description') or producto.get('metaTagDescription') or ''
        category_name = category_map.get(int(category_id), 'N/A') if category_id != 'N/A' else 'N/A'

        atributos = producto.get("_atributos", {})
        
        # Procesar SKUs
        items = producto.get('items', [])
        if not items:
            attr_values = []
            for a in sorted(all_attributes):
                val = atributos.get(a, [])
                if isinstance(val, list):
                    attr_values.append(", ".join(str(v) for v in val))
                else:
                    attr_values.append(str(val))
            
            productos_rows.append([
                product_id, product_reference, 'N/A', 'N/A', product_name,
                (description or "")[:500], brand, category_id, category_name, 0
            ] + attr_values)
        else:
            for item in items:
                sku_id = item.get('itemId', 'N/A')
                sku_name = item.get('name', 'N/A')
                available_qty = 0
                
                for seller in item.get('sellers', []):
                    offer = seller.get('commertialOffer', {}) or seller.get('commercialOffer', {})
                    qty = offer.get('AvailableQuantity', 0)
                    if isinstance(qty, (int, float)):
                        available_qty += qty
                
                attr_values = []
                for a in sorted(all_attributes):
                    val = atributos.get(a, [])
                    if isinstance(val, list):
                        attr_values.append(", ".join(str(v) for v in val))
                    else:
                        attr_values.append(str(val))
                
                productos_rows.append([
                    product_id, product_reference, sku_id, sku_name, product_name,
                    (description or "")[:500], brand, category_id, category_name, available_qty
                ] + attr_values)
    
    # Crear DataFrames y guardar en session_state
    st.session_state.df_productos = pd.DataFrame(
        productos_rows,
        columns=['productId','productReference','skuId','skuName','productName',
                'description','brand','categoryId','categoryName','availableQuantity'] + attr_headers
    )
    
    # Crear DataFrame de atributos
    atributos_info = []
    for a in sorted(all_attributes):
        valores = set()
        for p in productos:
            vals = p.get("_atributos", {}).get(a, [])
            if vals:
                valores.update(str(v) for v in vals)
        atributos_info.append({
            "atributo": f"atributo.{a}",
            "valores_ejemplo": ", ".join(list(valores)[:10])
        })
    
    st.session_state.df_atributos = pd.DataFrame(atributos_info)
    st.session_state.productos_data = {
        'total_productos': len(productos),
        'total_skus': len(productos_rows),
        'total_atributos': len(all_attributes),
        'tipo_extraccion': 'SOLO_ACTIVOS'
    }

# ====================================================================================
# MOSTRAR RESULTADOS SI EXISTEN DATOS EN SESSION STATE
# ====================================================================================
if st.session_state.df_productos is not None:
    data = st.session_state.productos_data
    df_productos = st.session_state.df_productos
    df_atributos = st.session_state.df_atributos
    
    tipo_badge = "🟢 SOLO ACTIVOS" if data.get('tipo_extraccion') == 'SOLO_ACTIVOS' else "🔵 TODOS (ACTIVOS E INACTIVOS)"
    
    st.success(f"🎉 Extracción completada: {tipo_badge}")
    
    # Métricas según el tipo de extracción
    if data.get('tipo_extraccion') == 'TODOS':
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total SKUs", data['total_skus'])
        with col2:
            st.metric("SKUs Activos", data['total_activos'])
        with col3:
            st.metric("SKUs con Stock", data['total_con_stock'])
        with col4:
            st.metric("Atributos", data['total_atributos'])
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Productos", data['total_productos'])
        with col2:
            st.metric("Total SKUs", data['total_skus'])
        with col3:
            st.metric("Atributos", data['total_atributos'])
    
    # Mostrar muestra de productos
    st.markdown("#### 👀 Muestra de los primeros 10 productos")
    st.dataframe(df_productos.head(10), use_container_width=True)
    
    # Mostrar muestra de atributos
    st.markdown("#### 🏷️ Muestra de atributos disponibles")
    st.dataframe(df_atributos.head(10), use_container_width=True)
    
    # Descargas
    col1, col2 = st.columns(2)
    
    with col1:
        csv_productos = df_productos.to_csv(index=False, encoding='utf-8')
        tipo_archivo = "activos" if data.get('tipo_extraccion') == 'SOLO_ACTIVOS' else "completo"
        st.download_button(
            label="📥 Descargar CSV de Productos",
            data=csv_productos,
            file_name=f"productos_{tipo_archivo}_vtex_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        csv_atributos = df_atributos.to_csv(index=False, encoding='utf-8')
        st.download_button(
            label="📥 Descargar CSV de Atributos",
            data=csv_atributos,
            file_name=f"atributos_vtex_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
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