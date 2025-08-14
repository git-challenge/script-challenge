# 📊 Artworks Report Generator

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![Build](https://github.com/git-challenge/script-challenge/actions/workflows/python-app.yml/badge.svg)

> 🛠 Script en Python para generar un **reporte en JSON y PDF** a partir de una configuración YAML. Obtiene los datos del [Art Institute of
Chicago API](https://api.artic.edu/docs/)

---

## ✨ Características
- 📄 Genera **2 archivos** de salida: `report.json` y `report.pdf`.
- ⚙️ Reporte configurable mediante archivo `.yml`.
- 🔄 Se integra con **GitHub Actions** para validación automática.

---
## 🚀 Uso rápido

### 1. Clonar el repositorio
```bash
git clone https://github.com/git-challenge/script-challenge.git
cd script-challenge
```

### 2. Montar el ambiente virtual (recomendado)
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Ejecutar el script
```bash
python -m artworks-report.py \
        --config config/queries.yml \
        --out out --dry-run
```