# Deploying The VMVI Annotation Explorer

The app is deployment-ready as a Streamlit application.

The hosted app does not need the full VMVI dataset checked into the repository. Users upload `Label400` PNG images through the browser, and the app parses them in memory.

## Recommended Deployment: Streamlit Community Cloud

1. Create a GitHub repository for the app.
2. Commit only the lightweight app files:

   ```text
   vmvi_explorer/
   requirements.txt
   packages.txt
   runtime.txt
   .streamlit/config.toml
   VMVI_ANNOTATION_EXPLORER_README.md
   VMVI_ANNOTATION_EXPLORER_PLAN.md
   VMVI_ANNOTATION_EXPLORER_RESULTS.md
   DEPLOYMENT.md
   ```

3. Do not commit these large local folders:

   ```text
   data/
   outputs/
   archive/
   ```

4. In Streamlit Community Cloud, choose:

   ```text
   Main file path: vmvi_explorer/app.py
   Python version: 3.12
   ```

5. Deploy.

## Local Deployment Test

Run:

```bash
/tmp/vmvi_explorer_venv/bin/python -m streamlit run vmvi_explorer/app.py --server.headless true --server.port 8501 --server.address 127.0.0.1
```

Open:

```text
http://127.0.0.1:8501
```

If port `8501` is busy:

```bash
/tmp/vmvi_explorer_venv/bin/python -m streamlit run vmvi_explorer/app.py --server.headless true --server.port 8502 --server.address 127.0.0.1
```

## Deployment Files

| File | Purpose |
|---|---|
| `requirements.txt` | Python package dependencies |
| `packages.txt` | System packages for hosted Linux environments |
| `runtime.txt` | Python runtime version hint |
| `.streamlit/config.toml` | Streamlit server/theme settings |
| `Procfile` | Generic PaaS command for platforms using `$PORT` |
| `.gitignore` | Prevents large local data from being committed |

## Important Hosting Note

The full local workspace is about 18 GB, with `data/` around 4.6 GB. Do not push the full workspace to a hosting service.

For deployment, create a clean repository containing only the app code and docs. The app is designed for upload-based analysis, so hosted users can drag and drop their own `Label400` images.

## Smoke Test

After deployment, verify:

1. The app loads.
2. A user can upload one or more `Label400` PNG files.
3. The app generates auto names.
4. The results table appears.
5. The image inspector appears.
6. CSV export buttons appear.

Local automated smoke test:

```bash
/tmp/vmvi_explorer_venv/bin/python scripts/smoke_test_annotation_explorer.py
```

