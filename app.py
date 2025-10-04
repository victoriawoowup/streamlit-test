import streamlit as st
import requests
import time
import csv

st.title("🔐 Validación de Endpoints VTEX")

# =========================
# Inputs de usuario
# =========================
ACCOUNT_NAME = st.text_input("Cuenta VTEX")
VTEX_APP_KEY = st.text_input("App Key")
VTEX_APP_TOKEN = st.text_input("App Token")
SALES_CHANNEL = st.text_input("Sales Channel")

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
# Funciones de validación
# =========================
def validar_ventas():
    st.subheader("1️⃣ Ventas")
    headers = get_vtex_headers()
    url = f'https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/oms/pvt/orders'
    params = {
        'orderBy': 'creationDate,desc',
        'f_status': 'ready-for-handling,handling,invoiced',
        'f_salesChannel': SALES_CHANNEL,
        'page': 0,
        'per_page': 1  # solo validar acceso
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            st.success("✅ ACCESO EXITOSO a API de Ventas")
        else:
            st.error(f"❌ ERROR en API de Ventas - Status: {resp.status_code}")
            st.write(resp.text[:200])
    except Exception as e:
        st.error(f"❌ EXCEPCIÓN en API de Ventas: {e}")

def validar_productos():
    st.subheader("2️⃣ Productos")
    headers = get_vtex_headers()
    url = f'https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/catalog_system/pub/products/search?_from=0&_to=5'

    try:
        resp = requests.get(url, headers=headers, timeout=10)
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
                    st.write(f"- Primer productId: {product_id}, referenceId: {reference_id}")
                    break
            if not product_id:
                st.warning("⚠️ No se encontró productId o referenceId")
            return product_id, reference_id
        else:
            st.error(f"❌ ERROR en API de Productos - Status: {resp.status_code}")
            st.write(resp.text[:200])
            return None, None
    except Exception as e:
        st.error(f"❌ EXCEPCIÓN en API de Productos: {e}")
        return None, None

def validar_clientes():
    st.subheader("3️⃣ Clientes")
    headers = get_vtex_headers_alt()
    url = f'https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/dataentities/CL/search'
    params = {
        '_fields': '_all'
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            st.success("✅ ACCESO EXITOSO a API de Clientes")
        else:
            st.error(f"❌ ERROR en API de Clientes - Status: {resp.status_code}")
            st.write(resp.text[:200])
    except Exception as e:
        st.error(f"❌ EXCEPCIÓN en API de Clientes: {e}")

def validar_precios(product_id):
    st.subheader("4️⃣ Precios")
    if not product_id:
        st.warning("⚠️ SALTEADO - No hay productId disponible")
        return

    headers = get_vtex_headers_alt()
    headers['Accept'] = 'application/vnd.vtex.ds.v10+json'

    url = f'https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/pricing/prices/{product_id}'

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            st.success("✅ ACCESO EXITOSO a API de Precios")
        else:
            st.error(f"❌ ERROR en API de Precios - Status: {resp.status_code}")
    except Exception as e:
        st.error(f"❌ EXCEPCIÓN en API de Precios: {e}")


def validar_categorias():
    st.subheader("5️⃣ Categorías")
    headers = get_vtex_headers_alt()
    headers['REST-Range'] = 'resources=0-10'
    url = f'https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/catalog_system/pub/category/tree/10'

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            st.success("✅ ACCESO EXITOSO a API de Categorías")
        else:
            st.error(f"❌ ERROR en API de Categorías - Status: {resp.status_code}")
            st.write(resp.text[:200])
    except Exception as e:
        st.error(f"❌ EXCEPCIÓN en API de Categorías: {e}")

def validar_simulador(product_id):
    st.subheader("6️⃣ Simulador")
    if not product_id:
        st.warning("⚠️ SALTEADO - No hay productId disponible")
        return
    headers = get_vtex_headers_alt()
    url = f'https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/checkout/pvt/orderForms/simulation'
    payload = {"items": [{"id": product_id, "quantity": 1, "seller": SALES_CHANNEL}]}

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        if resp.status_code == 200:
            st.success("✅ ACCESO EXITOSO a API de Simulador")
        else:
            st.error(f"❌ ERROR en API de Simulador - Status: {resp.status_code}")
            st.write(resp.text[:200])
    except Exception as e:
        st.error(f"❌ EXCEPCIÓN en API de Simulador: {e}")

# =========================
# Botón de ejecución
# =========================
if st.button("💡 Validar Endpoints VTEX"):
    validar_ventas()
    product_id, reference_id = validar_productos()
    validar_clientes()
    validar_precios(product_id)
    validar_categorias()
    validar_simulador(product_id)
    st.success("🎉 Validación completada")

# ---------------------------------------------------------------------------------
# SEGUNDO BLOQUE: VALIDACIÓN DE ENTIDADES
# ---------------------------------------------------------------------------------
st.markdown("---")
st.header("➡️ Continuar validación")

# Configuración clientes
FECHA_CLIENTES_DESDE = '2023-09-01'
FECHA_CLIENTES_HASTA = '2025-09-30'
OUTPUT_CSV_CLIENTES = "clientes_vtex_prueba.csv"
CAMPOS_CLIENTES = [
    'document', 'email', 'firstName', 'lastName',
    'birthdate', 'homePhone', 'gender', 'isNewsletterOptIn'
]

def fetch_clientes_scroll(account_name, fecha_desde, fecha_hasta, campos):
    headers = get_vtex_headers()
    base_url = f'https://{account_name}.vtexcommercestable.com.br/api/dataentities/CL/scroll'
    where_clause = f'createdIn between {fecha_desde} AND {fecha_hasta}'
    fields_param = ','.join(campos)

    all_clients = []
    token = None

    while True:
        params = {'_where': where_clause, '_fields': fields_param}
        if token:
            params['_token'] = token

        resp = requests.get(base_url, headers=headers, params=params)

        if resp.status_code != 200:
            st.error(f"❌ Error en clientes: {resp.status_code} - {resp.text}")
            break

        token = resp.headers.get('X-VTEX-MD-TOKEN')
        clients = resp.json()

        if not clients:
            break

        all_clients.extend(clients)

        if not token:
            break

        time.sleep(0.2)

    return all_clients

def export_clientes_to_csv(clientes, output_file, campos):
    if not clientes:
        return None
    
    with open(output_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(campos)  # header
        for cliente in clientes:
            row = []
            for campo in campos:
                valor = cliente.get(campo, "")
                if valor is None:
                    valor = ""
                row.append(valor)
            writer.writerow(row)
    return output_file

# Botón para validar clientes
st.subheader("👥 Validar Clientes")
if st.button("Validar clientes"):
    with st.spinner("Descargando clientes de VTEX..."):
        clientes = fetch_clientes_scroll(
            ACCOUNT_NAME, 
            FECHA_CLIENTES_DESDE, 
            FECHA_CLIENTES_HASTA, 
            CAMPOS_CLIENTES
        )

    if clientes:
        st.success(f"✅ Total de clientes recuperados: {len(clientes)}")

        # Guardar CSV
        csv_file = export_clientes_to_csv(clientes, OUTPUT_CSV_CLIENTES, CAMPOS_CLIENTES)
        if csv_file:
            with open(csv_file, "rb") as f:
                st.download_button(
                    label="💾 Descargar CSV de Clientes",
                    data=f,
                    file_name=csv_file,
                    mime="text/csv"
                )

        # Mostrar muestra
        st.write("📋 Muestra de 5 clientes:")
        st.dataframe(clientes[:5])
    else:
        st.error("⚠️ No se recuperaron clientes.")

st.markdown("---")
st.header("💡 Continuar Validación")

# =========================
# Inputs de usuario para fechas
# =========================
st.subheader("📅 Validación de Clientes")
fecha_desde = st.date_input("Fecha desde")
fecha_hasta = st.date_input("Fecha hasta")
OUTPUT_CSV_CLIENTES = "clientes_vtex.csv"
CAMPOS_CLIENTES = ['document', 'email', 'firstName', 'lastName', 'birthdate', 'homePhone', 'gender', 'isNewsletterOptIn']

# =========================
# Funciones
# =========================
def fetch_clientes_scroll(account_name, fecha_desde, fecha_hasta, campos):
    """
    Obtiene clientes usando el endpoint de Master Data (scroll)
    """
    headers = get_vtex_headers()
    base_url = f'https://{account_name}.vtexcommercestable.com.br/api/dataentities/CL/scroll'

    where_clause = f'createdIn between {fecha_desde} AND {fecha_hasta}'
    fields_param = ','.join(campos)

    all_clients = []
    token = None
    page_count = 0

    while True:
        page_count += 1
        params = {
            '_where': where_clause,
            '_fields': fields_param
        }
        if token:
            params['_token'] = token

        try:
            resp = requests.get(base_url, headers=headers, params=params, timeout=10)
            if resp.status_code != 200:
                st.error(f"❌ Error en página {page_count}: {resp.status_code}")
                break

            token = resp.headers.get('X-VTEX-MD-TOKEN')
            clients = resp.json()

            if not clients:
                break

            all_clients.extend(clients)

            if not token:
                break

        except Exception as e:
            st.error(f"❌ Error procesando página {page_count}: {e}")
            break

    return all_clients

def export_clientes_to_csv(clientes, output_file, campos):
    """
    Exporta clientes a CSV
    """
    import csv
    if not clientes:
        st.warning("⚠️ No hay clientes para exportar")
        return

    with open(output_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(campos)
        for cliente in clientes:
            row = [cliente.get(c, "") if cliente.get(c) is not None else "" for c in campos]
            writer.writerow(row)
    st.success(f"💾 CSV de clientes generado: {output_file}")
    st.download_button("📥 Descargar CSV de Clientes", data=open(output_file, "rb"), file_name=output_file)

def mostrar_muestra_clientes(clientes, n=5):
    """
    Muestra los primeros N clientes
    """
    if not clientes:
        st.warning("⚠️ No hay clientes para mostrar")
        return

    st.write(f"👤 Mostrando los primeros {min(n,len(clientes))} clientes:")
    for i, cliente in enumerate(clientes[:n]):
        st.write(f"{i+1}. {cliente.get('email','N/A')} | {cliente.get('firstName','')} {cliente.get('lastName','')} | {cliente.get('document','N/A')} | {cliente.get('homePhone','')} | {cliente.get('gender','')} | Newsletter: {cliente.get('isNewsletterOptIn','N/A')}")

# =========================
# Botón para ejecutar
# =========================
if st.button("✅ Validar Clientes"):
    st.info("Consultando API de clientes...")
    clientes = fetch_clientes_scroll(ACCOUNT_NAME, fecha_desde, fecha_hasta, CAMPOS_CLIENTES)
    if clientes:
        export_clientes_to_csv(clientes, OUTPUT_CSV_CLIENTES, CAMPOS_CLIENTES)
        mostrar_muestra_clientes(clientes, 5)
    else:
        st.warning("⚠️ No se recuperaron clientes.")
