# Proiect ETL Spotify în Databricks

Acest proiect extrage date de pe API-ul Spotify și le salvează ca tabele Delta în Databricks.

## Setup (O singură dată)

1. **Rulare Notebook `get_tone`:**
    - Accesați notebook-ul `get_tone` pentru a rula scriptul care gestionează extragerea datelor de la API-ul Spotify.
    - Asigurați-vă că aveți toate bibliotecile necesare instalate pentru rularea acestuia:
      ```bash
      pip install -r requirements.txt
      ```

2. **Creare Secret Scope:**
    - Veți avea nevoie de [Databricks CLI](http://googleusercontent.com/databricks/cli/0).
    - Creați un "scope" pentru secretele Spotify:
      ```bash
      databricks secrets create-scope --scope spotify-scope
      ```

3. **Adăugare Token:**
    - Adăugați token-ul de acces în scope:
      ```bash
      databricks secrets put --scope spotify-scope --key spotify-token --string-value "YOUR_ACCESS_TOKEN_HERE"
      ```

4. **Setup Cluster:**
    - Atașați un cluster la acest repo.
    - Instalați bibliotecile necesare:
      ```bash
      pip install -r requirements.txt
      ```