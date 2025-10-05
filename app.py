import streamlit as st
import requests
import time
import pandas as pd
import io
from datetime import datetime

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

st.set_page_config(page_title="VTEX Validator", page_icon="🔐", layout="wide")

# Logo WOOWUP centrado
col1, col2, col3 = st.columns([2, 1, 2])
with col2:
    st.image("woowup_logo.png", width=200)
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
# TERCER BLOQUE: EXTRACCIÓN DE PRODUCTOS
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

# Configuración fija para productos
productos_por_pagina = 50

if st.button("📥 Extraer Productos", type="primary", use_container_width=True):
    validar_credenciales()
    
    st.info("🔄 Paso 1/3: Obteniendo árbol de categorías...")
    
    # Headers para productos
    headers_productos = get_vtex_headers()
    headers_productos['Accept'] = 'application/vnd.vtex.ds.v10+json'
    headers_productos['REST-Range'] = 'resources=0-10'
    
    # ===== FETCH CATEGORÍAS =====
    category_map = {}
    url_categorias = f'https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/catalog_system/pub/category/tree/10'
    
    try:
        resp_cat = requests.get(url_categorias, headers=headers_productos, timeout=30)
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
    
    # ===== FETCH PRODUCTOS =====
    st.info("🔄 Paso 2/3: Extrayendo productos...")
    
    productos = []
    from_index = 0
    page_count = 0
    
    progress_text_prod = st.empty()
    info_text_prod = st.empty()
    
    with st.spinner('📦 Extrayendo productos de VTEX...'):
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
                
                # Si obtuvo menos productos que el límite, terminó
                if len(products_page) < productos_por_pagina:
                    info_text_prod.success("✅ Se procesaron todos los productos disponibles")
                    break
                
                from_index = to_index + 1
                time.sleep(0.5)  # Rate limiting
                
            except requests.exceptions.Timeout:
                st.error(f"⏱️ Timeout en página {page_count}. Reintentando...")
                time.sleep(2)
                continue
            except Exception as e:
                st.error(f"❌ Excepción en página {page_count}: {str(e)}")
                break
    
    # ===== PROCESAR Y EXPORTAR =====
    if productos:
        st.info("🔄 Paso 3/3: Procesando datos y generando CSVs...")
        
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
            description = producto.get('description', '') or producto.get('metaTagDescription', 'N/A')
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
                    description[:500], brand, category_id, category_name, 0
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
                        description[:500], brand, category_id, category_name, available_qty
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
            'total_atributos': len(all_attributes)
        }

# Mostrar resultados si existen datos en session_state
if st.session_state.df_productos is not None:
    data = st.session_state.productos_data
    df_productos = st.session_state.df_productos
    df_atributos = st.session_state.df_atributos
    
    st.success(f"🎉 Extracción completada: {data['total_productos']} productos | {data['total_skus']} SKUs")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Productos", data['total_productos'])
    with col2:
        st.metric("Total SKUs", data['total_skus'])
    with col3:
        st.metric("Atributos", data['total_atributos'])
    
    # Mostrar muestra de productos
    st.markdown("#### 👀 Muestra de los primeros 5 productos")
    st.dataframe(df_productos.head(5), use_container_width=True)
    
    # Mostrar muestra de atributos
    st.markdown("#### 🏷️ Muestra de atributos disponibles")
    st.dataframe(df_atributos.head(10), use_container_width=True)
    
    # Descargas - AHORA PERSISTEN
    col1, col2 = st.columns(2)
    
    with col1:
        csv_productos = df_productos.to_csv(index=False, encoding='utf-8')
        st.download_button(
            label="📥 Descargar CSV de Productos",
            data=csv_productos,
            file_name=f"productos_vtex_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
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
# CUARTO BLOQUE: EXTRACCIÓN DE VENTAS
# ---------------------------------------------------------------------------------
st.markdown("---")
st.markdown("---")
st.header("💰 Extracción de Ventas")

# Inicializar session state para ventas
if 'ventas_data' not in st.session_state:
    st.session_state.ventas_data = None
if 'df_ventas' not in st.session_state:
    st.session_state.df_ventas = None

st.markdown("### 📅 Rango de Fechas")

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

# Configuración de workers para requests concurrentes
with st.expander("⚙️ Configuración Avanzada"):
    max_workers = st.slider("Requests concurrentes", min_value=1, max_value=20, value=10, 
                            help="Cantidad de requests simultáneos para detalles de órdenes")

if st.button("📥 Extraer Ventas", type="primary", use_container_width=True):
    validar_credenciales()
    
    # Convertir fechas a ISO 8601 UTC
    fecha_desde_iso = fecha_desde_ventas.strftime("%Y-%m-%dT00:00:00.000Z")
    fecha_hasta_iso = fecha_hasta_ventas.strftime("%Y-%m-%dT23:59:59.999Z")
    
    st.info("🔄 Paso 1/2: Extrayendo órdenes...")
    
    # Headers
    headers_ventas = get_vtex_headers()
    
    # ===== FETCH ÓRDENES PAGINADAS =====
    all_orders = []
    page = 0
    per_page = 100
    
    progress_text_ventas = st.empty()
    info_text_ventas = st.empty()
    
    with st.spinner('💰 Extrayendo órdenes de VTEX...'):
        while True:
            url_orders = f"https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/oms/pvt/orders"
            params = {
                "orderBy": "creationDate,asc",
                "f_status": "ready-for-handling,handling,invoiced",
                "f_creationDate": f"creationDate:[{fecha_desde_iso} TO {fecha_hasta_iso}]",
                "f_salesChannel": SALES_CHANNEL,
                "page": page,
                "per_page": per_page
            }
            
            try:
                resp = requests.get(url_orders, headers=headers_ventas, params=params, timeout=30)
                
                if resp.status_code != 200:
                    st.error(f"❌ Error en página {page}: Status {resp.status_code}")
                    with st.expander("Ver detalle del error"):
                        st.code(resp.text[:500])
                    break
                
                data = resp.json()
                orders = data.get("list", [])
                
                if not orders:
                    info_text_ventas.success("✅ No hay más órdenes para procesar")
                    break
                
                all_orders.extend(orders)
                
                progress_text_ventas.text(f"📄 Página {page}")
                info_text_ventas.info(f"✅ {len(orders)} órdenes en esta página | Total acumulado: {len(all_orders)}")
                
                if len(orders) < per_page:
                    info_text_ventas.success("✅ Se procesaron todas las órdenes disponibles")
                    break
                
                page += 1
                time.sleep(0.3)  # Rate limiting
                
            except requests.exceptions.Timeout:
                st.error(f"⏱️ Timeout en página {page}. Reintentando...")
                time.sleep(2)
                continue
            except Exception as e:
                st.error(f"❌ Excepción en página {page}: {str(e)}")
                break
    
    # ===== FETCH DETALLES CON CONCURRENCIA =====
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
                        "N/A", "N/A", "N/A", "N/A"
                    ])
                else:
                    for item in items:
                        refId = item.get("refId", "N/A")
                        name = item.get("name", "N/A")
                        qty = item.get("quantity", "N/A")
                        price = item.get("price", "N/A")
                        
                        ventas_rows.append([
                            order_id, status, creation, sales_channel, total_value,
                            client_email, client_first, client_last, client_doc,
                            refId, name, qty, price
                        ])
            
            # Crear DataFrame y guardar en session_state
            st.session_state.df_ventas = pd.DataFrame(
                ventas_rows,
                columns=[
                    'orderId', 'status', 'creationDate', 'salesChannel', 'value',
                    'client_email', 'client_firstName', 'client_lastName', 'client_document',
                    'item_refId', 'item_name', 'item_quantity', 'item_price'
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
        total_value = df_ventas['value'].astype(float).sum() / 100  # VTEX guarda en centavos
        st.metric("Valor Total", f"${total_value:,.2f}")
    
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