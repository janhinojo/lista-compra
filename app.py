import streamlit as st
import json
import os
import time
import hmac
import hashlib

# --- CONFIGURACIÓ DE LA PÀGINA ---
st.set_page_config(page_title="Llista de la Compra", page_icon="🛒", layout="centered")

# Estils CSS per a mòbil: mantenir el botó d'esborrar a la mateixa línia (petit) i fer el checkbox més gran
st.markdown(
    """
    <style>
    /* Mantenir cada fila de producte en una sola línia també al mòbil */
    [data-testid="stHorizontalBlock"]:has([data-testid="stCheckbox"]) {
        flex-wrap: nowrap !important;
        align-items: center !important;
        gap: 0.5rem !important;
    }
    [data-testid="stHorizontalBlock"]:has([data-testid="stCheckbox"]) > div:first-child {
        flex: 1 1 auto !important;
        min-width: 0 !important;
        width: auto !important;
    }
    [data-testid="stHorizontalBlock"]:has([data-testid="stCheckbox"]) > div:last-child {
        flex: 0 0 auto !important;
        min-width: auto !important;
        width: auto !important;
    }

    /* Fer el checkbox i el text del producte més grans i fàcils de prémer */
    [data-testid="stCheckbox"] label {
        padding: 0.35rem 0 !important;
        align-items: center !important;
    }
    [data-testid="stCheckbox"] label > span:first-child {
        transform: scale(1.45);
        margin-right: 0.65rem !important;
        margin-left: 0.2rem !important;
    }
    [data-testid="stCheckbox"] label p {
        font-size: 1.2rem !important;
        font-weight: 500 !important;
        line-height: 1.4 !important;
    }

    /* Fer el botó d'eliminar més petit i discret */
    [data-testid="stHorizontalBlock"]:has([data-testid="stCheckbox"]) [data-testid="stButton"] button {
        padding: 0.1rem 0.4rem !important;
        min-height: 1.75rem !important;
        height: 1.75rem !important;
        font-size: 0.8rem !important;
        opacity: 0.65;
    }
    [data-testid="stHorizontalBlock"]:has([data-testid="stCheckbox"]) [data-testid="stButton"] button:hover {
        opacity: 1;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- SISTEMA DE CONTRASENYA (SESSIÓ D'1 HORA) ---
SESSION_DURATION = 3600  # 1 hora en segons

def _create_session_token(secret: str, exp: int) -> str:
    sig = hmac.new(secret.encode("utf-8"), str(exp).encode("utf-8"), hashlib.sha256).hexdigest()[:16]
    return f"{exp}.{sig}"

def _verify_session_token(token: str, secret: str) -> int:
    try:
        exp_str, sig = token.split(".", 1)
        exp = int(exp_str)
        expected_sig = hmac.new(secret.encode("utf-8"), exp_str.encode("utf-8"), hashlib.sha256).hexdigest()[:16]
        if hmac.compare_digest(sig, expected_sig) and exp > time.time():
            return exp
    except Exception:
        pass
    return 0

def check_password():
    secret = st.secrets["password_familia"]
    now = time.time()

    # Comprovar si la sessió en memòria encara és vàlida
    if st.session_state.get("autenticat") and st.session_state.get("auth_exp", 0) > now:
        return

    # Comprovar si hi ha un token de sessió vàlid (< 1 hora) a l'URL per mantenir la sessió en recarregar
    token = st.query_params.get("sessio", "")
    if token:
        exp = _verify_session_token(token, secret)
        if exp > now:
            st.session_state["autenticat"] = True
            st.session_state["auth_exp"] = exp
            return
        else:
            st.query_params.clear()

    st.session_state["autenticat"] = False
    st.warning("🔒 Aquesta és una app privada.")
    with st.form("login_form"):
        password = st.text_input("Contrasenya de la família:", type="password")
        entrar = st.form_submit_button("Entrar 🔓", use_container_width=True)

        if entrar:
            # Comprovem si coincideix amb la contrasenya guardada als secrets
            if password == secret:
                exp = int(time.time()) + SESSION_DURATION
                st.session_state["autenticat"] = True
                st.session_state["auth_exp"] = exp
                st.query_params["sessio"] = _create_session_token(secret, exp)
                st.rerun()
            else:
                st.error("Contrasenya incorrecta. Prova-ho de nou.")

    # Atura l'execució aquí si no està autenticat
    st.stop()

# Cridem la funció de bloqueig abans de carregar res més
check_password()


# --- LÒGICA DE LES DADES (FITXER JSON) ---
FILE_PATH = 'llista.json'

def load_data():
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, 'r', encoding='utf-8') as f:
            try:
                raw_data = json.load(f)
                # Compatibilitat amb llistes antigues de textos simples
                return [
                    {"nom": item, "comprat": False} if isinstance(item, str) else item
                    for item in raw_data
                ]
            except json.JSONDecodeError:
                return []
    return []

def save_data(data):
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)


# --- INTERFÍCIE DE LA LLISTA ---
st.title("🛒 Llista de la Compra Familiar")

# Carregar la llista actual
items = load_data()

# Formulari per afegir productes
with st.form("add_item_form", clear_on_submit=True):
    col1, col2 = st.columns([3, 1])
    with col1:
        nou_producte = st.text_input("Què falta a la nevera?", placeholder="Ex: Llet, Ous, Pomes...", label_visibility="collapsed")
    with col2:
        afegir = st.form_submit_button("Afegir ➕", use_container_width=True)

    if afegir and nou_producte:
        nom_net = nou_producte.strip()
        noms_existents = [item["nom"].lower() for item in items]
        if nom_net and nom_net.lower() not in noms_existents:
            items.append({"nom": nom_net, "comprat": False})
            save_data(items)
            st.rerun()

st.divider()

# Mostrar la llista amb actualització automàtica en temps real per a tots els usuaris
@st.fragment(run_every="3s")
def mostrar_llista():
    items_actuals = load_data()
    st.subheader("📝 Pendent de comprar:")

    if not items_actuals:
        st.info("Ompliu la llista o el papa s'enfadara molt. 67.")
    else:
        for i, item in enumerate(items_actuals):
            col_item, col_del = st.columns([10, 1], vertical_alignment="center")
            with col_item:
                label = f"~~{item['nom']}~~" if item["comprat"] else item["nom"]
                marcat = st.checkbox(label, value=item["comprat"], key=f"check_{i}_{item['nom']}")
                if marcat != item["comprat"]:
                    items_actuals[i]["comprat"] = marcat
                    save_data(items_actuals)
                    st.rerun()
            with col_del:
                if st.button("🗑️", key=f"del_{i}_{item['nom']}", help="Eliminar producte"):
                    items_actuals.pop(i)
                    save_data(items_actuals)
                    st.rerun()

    st.divider()

    # Botó per reiniciar la llista
    if items_actuals:
        if st.button("✅ Compra feta! Reiniciar la llista", type="primary", use_container_width=True):
            save_data([])
            st.success("Llista esborrada correctament!")
            st.rerun()

mostrar_llista()