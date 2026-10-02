@echo off
cd /d C:\Paykan\COSVEN
C:\Users\IT\AppData\Local\Programs\Python\Python313\python.exe -m streamlit run app\dashboard_cosven.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
