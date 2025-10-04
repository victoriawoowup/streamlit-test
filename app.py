import streamlit as st
import requests
import time
import csv
import pandas as pd

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
st.header("➡️ Continuar Validación")

# =========================
# Validación de Clientes
# =========================
st.subheader("👥 Validación de Clientes")

# Input de fecha mínima
updated_in_desde = st.date_input(
    "Fecha mínima de actualización (updatedIn)",
    value=pd.to_datetime("2025-01-01")
)

OUTPUT_CSV_CLIENTES = "clientes_vtex.csv"

def fetch_clientes_scroll(account_name, updated_min, headers):
    """
    Descarga masiva de clientes usando el endpoint /scroll de VTEX
    """
    url = f'https://{account_name}.vtexcommercestable.com.br/api/dataentities/CL/scroll'
    where_clause = f"(updatedIn>{updated_min}T00:00:00.000Z) OR ((updatedIn is null) AND (createdIn>{updated_min}T00:00:00.000Z))"
    fields_param = "_all"
    all_clients = []
    token = None
    page_count = 0

    while True:
        page_count += 1
        params = {'_where': where_clause, '_fields': fields_param}
        if token:
            params['_token'] = token

        resp = requests.get(url, headers={**headers, "REST-Range": "resources=0-100"}, params=params, timeout=15)
        
        if resp.status_code != 200:
            st.error(f"❌ ERROR en página {page_count}: {resp.status_code}")
            break

        clients = resp.json()
        all_clients.extend(clients)

        token = resp.headers.get("X-VTEX-MD-TOKEN")
        if not token or not clients:
            break

    return all_clients

def export_clientes_to_csv(clientes, output_file):
    if not clientes:
        st.warning("⚠️ No hay clientes para exportar")
        return
    # Usar todos los campos de la primera fila para el CSV
    campos = list(clientes[0].keys())
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        for c in clientes:
            writer.writerow({k: c.get(k, "") for k in campos})
    st.success(f"💾 CSV de clientes generado: {output_file} (Total registros: {len(clientes)})")

def mostrar_muestra_clientes(clientes, n=5):
    if not clientes:
        st.warning("⚠️ No hay clientes para mostrar")
        return
    st.markdown(f"Mostrando los primeros {min(n,len(clientes))} clientes:")
    for i, c in enumerate(clientes[:n]):
        st.write(f"{i+1}. {c.get('email','N/A')} - {c.get('firstName','')} {c.get('lastName','')} - updatedIn: {c.get('updatedIn','N/A')}")

# Botón para ejecutar validación de clientes
if st.button("✅ Validar Clientes"):
    st.info("Consultando API de clientes...")
    clientes = fetch_clientes_scroll(ACCOUNT_NAME, updated_in_desde.strftime("%Y-%m-%d"), get_vtex_headers())
    export_clientes_to_csv(clientes, OUTPUT_CSV_CLIENTES)
    mostrar_muestra_clientes(clientes, 5)
