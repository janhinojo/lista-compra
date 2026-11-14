# 🛒 Llista de la Compra Familiar

Aplicació web privada feta amb **Streamlit** per gestionar la llista de la compra familiar.

## 🚀 Desplegament a Streamlit Community Cloud

1. Ves a [share.streamlit.io](https://share.streamlit.io/) i fes clic a **Create app**.
2. Selecciona el repositori `janhinojo/lista-compra`, la branca `main` i el fitxer principal `app.py`.
3. Abans de desplegar (o a **App settings → Secrets**), afegeix la contrasenya familiar en format TOML:
   ```toml
   password_familia = "la_teva_contrasenya"
   ```
4. Fes clic a **Deploy!**

## 💻 Execució en local

1. Instal·la les dependències:
   ```bash
   pip install -r requirements.txt
   ```
2. Crea el fitxer `.streamlit/secrets.toml` amb:
   ```toml
   password_familia = "la_teva_contrasenya"
   ```
3. Executa l'aplicació:
   ```bash
   streamlit run app.py
   ```
