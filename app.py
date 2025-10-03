import streamlit as st

st.title("App de Prueba 🚀")
st.write("Hola! Esta es una app de prueba en Streamlit Cloud.")

# Input de usuario
nombre = st.text_input("¿Cómo te llamás?")

if st.button("Saludar"):
    st.success(f"Hola {nombre}, tu app está funcionando en la nube 🎉")
