# VALIDAR ENDPOINTS VTEX COMPLET
import requests

# ---------- CONFIGURACIÓN ----------
ACCOUNT_NAME = 'ferrenovo'
VTEX_APP_KEY = 'vtexappkey-moreproducts-FZNBFT'
VTEX_APP_TOKEN = 'KQVRITWBIWWNUJRQCMOYUWEQSCRRTGHRXZKCIAOGJJXPAOJDCHDCTZXTRJAPZGSYVPKGOTHBCSSOUCTDNHTPLZEGFBYHWSEEXTDSPLFJKJZZAYMBXBJJPZZPDXBWIDQK'

# Credenciales alternativas para algunos endpoints
VTEX_APP_KEY_ALT = VTEX_APP_KEY
VTEX_APP_TOKEN_ALT = VTEX_APP_TOKEN
# -----------------------------------

def get_vtex_headers():
    return {
        'x-vtex-api-appKey': VTEX_APP_KEY,
        'x-vtex-api-appToken': VTEX_APP_TOKEN,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }

def get_vtex_headers_alt():
    return {
        'x-vtex-api-appKey': VTEX_APP_KEY_ALT,
        'x-vtex-api-appToken': VTEX_APP_TOKEN_ALT,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }

# -------- VALIDACIONES --------

def validar_ventas():
    print("\n1️⃣  VALIDANDO ACCESO A VENTAS")
    print("-"*60)
    headers = get_vtex_headers()
    url = f'https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/oms/pvt/orders'
    params = {'per_page': 1, 'page': 1}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            print("✅ ACCESO EXITOSO a API de Ventas")
            data = resp.json()
            orders = data.get("list", []) or data.get("orders", [])
            print(f"   Se encontraron órdenes: {len(orders) > 0}")
        else:
            print(f"❌ ERROR en API de Ventas - Status: {resp.status_code}")
    except Exception as e:
        print(f"❌ EXCEPCIÓN en API de Ventas: {e}")

def validar_productos():
    print("\n2️⃣  VALIDANDO ACCESO A PRODUCTOS")
    print("-"*60)
    headers = get_vtex_headers()
    url = f'https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/catalog_system/pub/products/search?_from=0&_to=5'
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code in [200, 206]:
            print("✅ ACCESO EXITOSO a API de Productos")
            products = resp.json()
            for product in products:
                prod_id = product.get('productId')
                ref = product.get('productReference')
                if prod_id and ref:
                    print(f"   Primer productId encontrado: {prod_id}")
                    print(f"   Primer referenceId encontrado: {ref}")
                    return prod_id, ref
            print("⚠️  No se encontró productId o referenceId")
        else:
            print(f"❌ ERROR en API de Productos - Status: {resp.status_code}")
    except Exception as e:
        print(f"❌ EXCEPCIÓN en API de Productos: {e}")
    return None, None

def validar_clientes():
    print("\n3️⃣  VALIDANDO ACCESO A CLIENTES")
    print("-"*60)
    headers = get_vtex_headers()
    url = f'https://{ACCOUNT_NAME}.vtexcommercestable.com.br/api/dataentities/CL/scroll'
    params = {'_fields': 'email,firstName', '_where': 'email is not null'}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            print("✅ ACCESO EXITOSO a API de Clientes")
            clients = resp.json()
            print(f"   Clientes encontrados en primera página: {len(clients)}")
        else:
            print(f"❌ ERROR en API de Clientes - Status: {resp.status_code}")
    except Exception as e:
        print(f"❌ EXCEPCIÓN en API de Clientes: {e}")

def validar_precios(reference_id):
    print("\n4️⃣  VALIDANDO ACCESO A PRECIOS")
    print("-"*60)
    if not reference_id:
        print("⚠️  SALTEADO - No hay referenceId disponible")
        return
    headers = get_vtex_headers_alt()
    headers['Accept'] = 'application/vnd.vtex.ds.v10+json'
    url = f'https://vta.vtexcommercestable.com.br/api/pricing/prices/{reference_id}'
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            print("✅ ACCESO EXITOSO a API de Precios")
            price_data = resp.json()
            print(f"   Base price: {price_data.get('basePrice','N/A')}")
            print(f"   List price: {price_data.get('listPrice','N/A')}")
        else:
            print(f"❌ ERROR en API de Precios - Status: {resp.status_code}")
    except Exception as e:
        print(f"❌ EXCEPCIÓN en API de Precios: {e}")

def validar_categorias():
    print("\n5️⃣  VALIDANDO ACCESO A CATEGORÍAS")
    print("-"*60)
    headers = get_vtex_headers_alt()
    headers['Accept'] = 'application/vnd.vtex.ds.v10+json'
    headers['REST-Range'] = 'resources=0-10'
    url = f'https://vta.vtexcommercestable.com.br/api/catalog_system/pub/category/tree/10'
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            categories = resp.json()
            print(f"✅ ACCESO EXITOSO a API de Categorías")
            print(f"   Categorías raíz encontradas: {len(categories)}")
        else:
            print(f"❌ ERROR en API de Categorías - Status: {resp.status_code}")
    except Exception as e:
        print(f"❌ EXCEPCIÓN en API de Categorías: {e}")

def validar_simulador(product_id):
    print("\n6️⃣  VALIDANDO ACCESO A SIMULADOR")
    print("-"*60)
    if not product_id:
        print("⚠️  SALTEADO - No hay productId disponible")
        return
    headers = get_vtex_headers_alt()
    url = f'https://vta.vtexcommercestable.com.br/api/checkout/pvt/orderForms/simulation'
    payload = {"items":[{"id": product_id,"quantity": 1,"seller": "1"}]}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        if resp.status_code == 200:
            print("✅ ACCESO EXITOSO a API de Simulador")
            sim_data = resp.json()
            total_value = sim_data.get('totals',[{}])[0].get('value','N/A') if sim_data.get('totals') else 'N/A'
            print(f"   Valor total simulación: {total_value}")
        else:
            print(f"❌ ERROR en API de Simulador - Status: {resp.status_code}")
    except Exception as e:
        print(f"❌ EXCEPCIÓN en API de Simulador: {e}")

# ========== EJECUCIÓN PRINCIPAL ==========
if __name__ == "__main__":
    print("="*60)
    print("🔐 SCRIPT DE VALIDACIÓN DE ACCESOS VTEX COMPLETO")
    print("="*60)
    
    product_id, reference_id = None, None

    # Validar Ventas, Productos y Clientes
    validar_ventas()
    product_id, reference_id = validar_productos()
    validar_clientes()

    # Validar Precios, Categorías y Simulador
    validar_precios(reference_id)
    validar_categorias()
    validar_simulador(product_id)

    print("\n" + "="*60)
    print("✅ VALIDACIÓN COMPLETADA")
    print("="*60)
