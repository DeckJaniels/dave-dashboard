import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import json

# Konfiguráció
st.set_page_config(
    page_title="DAVE Dashboard", 
    page_icon="🏠",
    layout="wide"
)

# Hitelesítés (felhő + helyi)
@st.cache_resource
def load_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # FELHŐBEN: secrets-ből
    if "GOOGLE_CREDENTIALS" in st.secrets:
        creds = Credentials.from_service_account_info(
            json.loads(st.secrets["GOOGLE_CREDENTIALS"]), 
            scopes=scopes
        )
    # HELYIBEN: fájlból  
    else:
        creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
    
    return gspread.authorize(creds)

# Inicializálás
client = load_client()
SHEET_ID = st.secrets.get("SHEET_ID", "CSERÉLD_KI_HELYETTEN")

try:
    workbook = client.open_by_key(SHEET_ID)
    st.success("✅ Google Sheets kapcsolat OK!")
except:
    st.error("❌ Sheets ID probléma! Ellenőrizd a secrets-et.")

# === OLDALAK ===
def overview():
    st.header("🏠 DAVE Dashboard - Áttekintés")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # ADATOK OLVASÁSA
    try:
        ingatlanok = workbook.worksheet("Ingatlanok").get_all_records()
        fizetesek = workbook.worksheet("Fizetések").get_all_records()
        df_ing = pd.DataFrame(ingatlanok)
        df_fiz = pd.DataFrame(fizetesek)
        
        # METRIKÁK
        with col1:
            st.metric("🏠 Ingatlanok", len(df_ing))
        with col2:
            aktif = len(df_ing[df_ing.get("Státusz", "") == "Aktív"])
            st.metric("✅ Aktív", aktif)
        with col3:
            fizetett = len(df_fiz[df_fiz.get("Státusz", "") == "Fizetve"])
            st.metric("💰 Befizetve", fizetett)
        with col4:
            tartozik = len(df_fiz) - fizetett
            st.metric("⚠️ Tartozás", tartozik)
        
        # GRAFIKONOK
        colA, colB = st.columns(2)
        with colA:
            if not df_ing.empty:
                fig = px.pie(df_ing, names="Státusz", title="Ingatlan státuszok")
                st.plotly_chart(fig, use_container_width=True)
        
        with colB:
            if not df_fiz.empty and "Összeg" in df_fiz.columns:
                df_fiz["Összeg"] = pd.to_numeric(df_fiz["Összeg"], errors="coerce")
                fig = px.bar(df_fiz, x="Dátum", y="Összeg", color="Státusz", 
                           title="Befizetések")
                st.plotly_chart(fig, use_container_width=True)
        
        # TÁBLÁZATOK
        st.subheader("📋 Ingatlanok")
        st.dataframe(df_ing, use_container_width=True)
        
    except Exception as e:
        st.error(f"Adatbetöltés hiba: {e}")

def add_property():
    st.header("➕ Új ingatlan hozzáadása")
    with st.form("new_property"):
        col1, col2 = st.columns(2)
        with col1:
            ing_id = st.text_input("Ingatlan ID", value="ING00")
            cim = st.text_input("Cím")
            tulajdonos = st.text_input("Tulajdonos")
        with col2:
            status = st.selectbox("Státusz", ["Aktív", "Inaktív"])
            befiz_datum = st.date_input("Következő befizetés")
        
        submit = st.form_submit_button("✅ Hozzáadás", use_container_width=True)
        
        if submit:
            try:
                worksheet = workbook.worksheet("Ingatlanok")
                worksheet.append_row([
                    ing_id, cim, tulajdonos, status, 
                    befiz_datum.strftime("%Y.%m.%d")
                ])
                st.success("✅ Ingatlan hozzáadva!")
                st.rerun()
            except Exception as e:
                st.error(f"Hiba: {e}")

# === FŐPROGRAM ===
def main():
    st.sidebar.title("🏠 DAVE")
    page = st.sidebar.selectbox("Menü", ["📊 Áttekintés", "➕ Új ingatlan"])
    
    if page == "📊 Áttekintés":
        overview()
    elif page == "➕ Új ingatlan":
        add_property()

if __name__ == "__main__":
    main()