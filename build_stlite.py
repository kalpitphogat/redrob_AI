import json
from pathlib import Path

def build_index():
    files = ["app.py", "config.py", "loader.py", "prefilter.py", "honeypot.py", "scorer.py", "behavioral.py", "reasoning.py", "ranker.py"]
    filesData = {}
    for f in files:
        path = Path(f)
        if path.exists():
            filesData[f] = path.read_text(encoding="utf-8")
    
    html = f"""<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
    <title>Redrob AI Candidate Ranker</title>
    <style>
      body, html {{ margin: 0; padding: 0; height: 100vh; font-family: 'Inter', sans-serif; background-color: #f8fafc; }}
      #loading-screen {{
        position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: #f8fafc;
        display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 9999;
      }}
      .spinner {{
        width: 50px; height: 50px; border: 5px solid #e2e8f0; border-top: 5px solid #2a5298;
        border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 20px;
      }}
      @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
      .loading-title {{ font-size: 1.5rem; font-weight: 700; color: #1e293b; margin-bottom: 10px; }}
      .loading-sub {{ font-size: 0.9rem; color: #64748b; max-width: 400px; text-align: center; }}
    </style>
  </head>
  <body>
    <div id="loading-screen">
      <div class="spinner"></div>
      <div class="loading-title">Launching Redrob Sandbox</div>
      <div class="loading-sub">Downloading Python runtime (WebAssembly) and installing dependencies (pandas, plotly, pyyaml) directly in your browser. This takes a little while on first load...</div>
    </div>
    <div id="root"></div>
    <script src="https://cdn.jsdelivr.net/npm/@stlite/mountable@0.64.2/build/stlite.js"></script>
    <script>
      const filesData = {json.dumps(filesData)};
      stlite.mount({{
        requirements: ["pandas", "plotly", "pyyaml"],
        entrypoint: "app.py",
        files: filesData
      }}, document.getElementById("root"));
    </script>
  </body>
</html>"""
    
    Path("index.html").write_text(html, encoding="utf-8")
    print("index.html generated")

if __name__ == "__main__":
    build_index()
