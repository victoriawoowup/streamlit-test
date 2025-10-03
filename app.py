import streamlit as st
import requests

# ===============================
# Funciones para VTEX
# ===============================

def get_vtex_headers(app_key, app_token):
    return {
        'x-vtex-api-appKey': app_key,
        'x-vtex-api-appToken': app_token,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }

def validar_ventas(account, headers):
    url = f'https://{account}.vtexcommercestable.com.br/api/oms/pvt/orders'
    params = {'per_page': 1, 'page': 1}
    resp = requests.get(url, headers=headers, params=params, timeout=10)
    return resp.status_code, resp.text[:200]

def validar_productos(account, headers):
    url = f'https://{account}.vtexcommercestable.com.br/api/catalog_system/pub/products/search?_from=0&_to=5'
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code in [200, 206]:
        products = resp.json()
        if products and isinstance(products, list):
            for product in products:
                prod_id = product.get('productId')
                ref = product.get('productReference')
                if prod_id and ref:
                    return resp.status_code, f"productId={prod_id}, referenceId={ref}", prod_id, ref
    return resp.status_code, "No se encontró productId/referenceId", None, None

def validar_clientes(account, headers):
    url = f'https://{account}.vtexcommercestable.com.br/api/dataentities/CL/scroll'
    params = {'_fields': 'email,firstName', '_where': 'email is not null'}
    resp = requests.get(url, headers=headers, params=params, timeout=10)
    return resp.status_code, resp.text[:200]

# ===============================
# APP STREAMLIT
# ===============================

st.title("🔐 Validador de Accesos VTEX")

st.write("Ingresá tus credenciales para validar acceso a los endpoints principales de VTEX.")

account = st.text_input("Account Name (ej: ferrenovo)")
app_key = st.text_input("App Key", type="password")
app_token = st.text_input("App Token", type="password")

if st.button("Ejecutar Validación"):
    if not account or not app_key or not app_token:
        st.error("⚠️ Debes ingresar todas las credenciales.")
    else:
        headers = get_vtex_headers(app_key, app_token)

        st.subheader("1️⃣ Validando Ventas")
        status, detail = validar_ventas(account, headers)
        st.write(f"Status: {status}")
        st.code(detail)

        st.subheader("2️⃣ Validando Productos")
        status, detail, product_id, reference_id = validar_productos(account, headers)
        st.write(f"Status: {status}")
        st.code(detail)

        st.subheader("3️⃣ Validando Clientes")
        status, detail = validar_clientes(account, headers)
        st.write(f"Status: {status}")
        st.code(detail)

        st.success("✅ Validación completada")
