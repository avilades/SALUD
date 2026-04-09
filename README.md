# ⚖️ Dashboard de Análisis Corporal

Esta es una aplicación web interactiva diseñada para visualizar, analizar y llevar un seguimiento detallado de las métricas registradas por tu báscula inteligente a lo largo del tiempo. 

## 🚀 Características Principales

- **Dashboard Interactivo:** Convierte tu historial de mediciones (archivo CSV) en un panel web moderno con tan solo un clic.
- **KPIs Destacados:** Visualiza rápidamente la evolución entre tu primera y última medición, abarcando las métricas más importantes:
  - Peso
  - Porcentaje de Grasa Corporal
  - Masa Muscular Esquelética
  - Edad Corporal
  - Calificación de Grasa Visceral
- **Evolución Gráfica:** Crea al instante gráficas interactivas dinámicas combinando los parámetros que más te interesen (puedes activar o desactivar tantas métricas como desees al mismo tiempo).
- **Control de Datos:** Acceso a una tabla completa de registros con función de filtrado y orden, lo que permite revisar la evolución paso a paso.

## 🛠️ Tecnologías Usadas

El proyecto está creado utilizando **Python** y sus librerías más populares orientadas a ciencia de datos y visualización:
- **Streamlit**: Para levantar una interfaz de usuario web de forma rápida y sencilla.
- **Pandas**: Para la limpieza, conversión de fechas y manipulación del archivo CSV.
- **Plotly**: Para generar gráficos lineales visualmente atractivos y 100% interactivos.

## 📋 Requisitos de Instalación

Asegúrate de tener Python instalado en tu ordenador. Abre la terminal (o consola de comandos de Windows) e instala las dependencias necesarias:

```bash
pip install streamlit pandas plotly
```

## ⚙️ Cómo iniciar la aplicación

1. Asegúrate de tener los archivos `app_bascula.py` y `results_2.csv` en la misma carpeta.
2. Abre la terminal en esa carpeta y ejecuta el siguiente comando:

```bash
streamlit run app_bascula.py
```

3. Automáticamente se abrirá una pestaña en tu navegador predeterminado (por defecto en `http://localhost:8501`) mostrando tu dashboard.

## 📝 Notas sobre la Base de Datos

La aplicación lee directamente de un archivo llamado `results_2.csv` alojado en la misma carpeta que el script (`app_bascula.py`). 
Cada vez que obtengas un nuevo pesaje, solo tienes que añadir esa fila al final de tu archivo `results_2.csv`. Una vez modificado, solo tienes que dar a refrescar (`Ctrl + R` en Windows o darle al botón **Rerun** dentro de Streamlit) y el dashboard se actualizará automáticamente con los nuevos datos.
