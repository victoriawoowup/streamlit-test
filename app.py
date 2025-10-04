import streamlit as st
import requests
import time
import csv
import pandas as pd
import io
from datetime import datetime

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
st.subheader("➡️ Continuar Validación")

# =========================
# Inputs de usuario para clientes
# =========================
st.markdown("### 👥 Validar Clientes")
fecha_desde = st.date_input("Fecha mínima de actualización (updatedIn) desde", value=datetime(2023, 1, 1))
fecha_hasta = st.date_input("Fecha máxima de actualización (updatedIn) hasta", value=datetime.today())

# Botón para ejecutar validación
if st.button("✅ Validar Clientes"):

    st.info("Consultando API de clientes...")

    # Convertir fechas a ISO 8601 UTC para VTEX
    fecha_desde_iso = fecha_desde.strftime("%Y-%m-%dT00:00:00.000Z")
    fecha_hasta_iso = fecha_hasta.strftime("%Y-%m-%dT23:59:59.999Z")

    # Headers con credenciales que ya tenés en tu app
    headers = {
        'x-vtex-api-appKey': VTEX_APP_KEY,
        'x-vtex-api-appToken': VTEX_APP_TOKEN,
        'Accept': 'application/vnd.vtex.ds.v10+json',
        'Content-Type': 'application/json',
        'REST-Range': 'resources=0-100'
    }

    # URL de scroll histórico de clientes
    url = f'https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/dataentities/CL/scroll'

    # Parámetros para VTEX
    params = {
        '_fields': '_all',
        '_where': f"(updatedIn>{fecha_desde_iso}) OR ((updatedIn is null) AND (createdIn>{fecha_desde_iso}))"
    }

    clientes = []
    token = None
    page_count = 0

    while True:
        page_count += 1
        if token:
            params['_token'] = token
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            if resp.status_code != 200:
                st.error(f"❌ Error en página {page_count}: {resp.status_code}")
                break

            # Obtener token de la siguiente página
            token = resp.headers.get('X-VTEX-MD-TOKEN')

            data = resp.json()
            if not data or len(data) == 0:
                st.success("✅ No hay más clientes para procesar.")
                break

            clientes.extend(data)
            st.write(f"\rPágina {page_count}: {len(data)} clientes procesados (Total: {len(clientes)})", end="")

            if not token:
                st.success("✅ Se procesaron todas las páginas.")
                break

        except Exception as e:
            st.error(f"❌ Excepción en página {page_count}: {e}")
            break

    if clientes:
        # Definir los campos que queremos mostrar/exportar
        campos_clientes = ['document', 'email', 'firstName', 'lastName', 'birthdate', 
                           'homePhone', 'gender', 'isNewsletterOptIn', 'updatedIn']

        # Crear DataFrame
        df = pd.DataFrame(clientes)

        # Filtrar solo campos existentes
        campos_existentes = [c for c in campos_clientes if c in df.columns]
        df = df[campos_existentes]

        # Mostrar primeros 5 clientes con solo los campos deseados
        st.markdown("#### 👀 Muestra de los primeros 5 clientes")
        st.dataframe(df.head(5))

        # Preparar CSV para descarga
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8')
        csv_bytes = csv_buffer.getvalue().encode('utf-8')

        st.download_button(
            label="📥 Descargar CSV de Clientes",
            data=csv_bytes,
            file_name="clientes_vtex.csv",
            mime="text/csv"
        )
    else:
        st.warning("⚠️ No se recuperaron clientes para las fechas indicadas.")

