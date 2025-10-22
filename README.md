# Spotify ETL Project in Databricks

This project extracts data from the Spotify API and saves it as Delta tables in Databricks.

## Setup (One-Time)

1. **Run the `get_tone` Notebook:**
    - Access the `get_tone` notebook to execute the script that handles data extraction from the Spotify API.
    - Ensure all necessary libraries are installed before running:
      ```bash
      pip install -r requirements.txt
      ```

2. **Create a Secret Scope:**
    - You will need [Databricks CLI](http://googleusercontent.com/databricks/cli/0).
    - Create a "scope" for Spotify secrets:
      ```bash
      databricks secrets create-scope --scope spotify-scope
      ```

3. **Add the Token:**
    - Add the access token to the scope:
      ```bash
      databricks secrets put --scope spotify-scope --key spotify-token --string-value "YOUR_ACCESS_TOKEN_HERE"
      ```

4. **Cluster Setup:**
    - Attach a cluster to this repository.
    - Install the necessary libraries:
      ```bash
      pip install -r requirements.txt
      ```