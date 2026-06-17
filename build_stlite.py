import json
from pathlib import Path

def build_index():
    py_files = ["app.py", "config.py", "loader.py", "prefilter.py", "honeypot.py", "scorer.py", "behavioral.py", "reasoning.py", "ranker.py"]
    filesData = {}

    # Add Python source files
    for f in py_files:
        path = Path(f)
        if path.exists():
            filesData[f] = path.read_text(encoding="utf-8")
        else:
            print(f"WARNING: {f} not found, skipping.")

    # Add sample_candidates.json as a bundled file
    sample_path = Path("sample_candidates.json")
    if sample_path.exists():
        # Read as JSON and re-dump to compact string to ensure valid JSON in browser
        sample_data = json.loads(sample_path.read_text(encoding="utf-8"))
        filesData["sample_candidates.json"] = json.dumps(sample_data)
        print(f"Bundled sample_candidates.json ({len(filesData['sample_candidates.json'])} chars)")
    else:
        print("WARNING: sample_candidates.json not found - sandbox will require file upload.")

    files_json = json.dumps(filesData, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
    <title>Redrob AI Candidate Ranker — Sandbox</title>
    <meta name="description" content="Interactive sandbox to explore the Redrob AI candidate ranking pipeline." />
    <style>
      *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
      body, html {{ height: 100%; font-family: 'Inter', 'Segoe UI', sans-serif; background-color: #f8fafc; }}
      #loading-screen {{
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        z-index: 9999; transition: opacity 0.5s ease;
      }}
      #loading-screen.hidden {{ opacity: 0; pointer-events: none; }}
      .spinner {{
        width: 56px; height: 56px;
        border: 5px solid rgba(255,255,255,0.3);
        border-top: 5px solid #ffffff;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 24px;
      }}
      @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
      .loading-title {{
        font-size: 1.8rem; font-weight: 800; color: #ffffff;
        margin-bottom: 12px; letter-spacing: -0.5px;
      }}
      .loading-sub {{
        font-size: 0.95rem; color: rgba(255,255,255,0.75);
        max-width: 380px; text-align: center; line-height: 1.6;
      }}
      #root {{ height: 100vh; }}
    </style>
  </head>
  <body>
    <!-- Splash screen shown while stlite boots -->
    <div id="loading-screen">
      <div class="spinner"></div>
      <div class="loading-title">🔍 Redrob AI Ranker</div>
      <div class="loading-sub">
        Booting Python runtime in your browser (WebAssembly).<br/>
        Installing pandas &amp; plotly — first load takes ~30s.
      </div>
    </div>

    <div id="root"></div>

    <script src="https://cdn.jsdelivr.net/npm/@stlite/mountable@0.64.2/build/stlite.js"></script>
    <script>
      // All Python source files and data bundled here
      const filesData = {files_json};

      stlite.mount(
        {{
          requirements: ["pandas", "plotly", "pyyaml"],
          entrypoint: "app.py",
          files: filesData,
          onProgress: (progress) => {{
            // You can use this to show loading progress if desired
            console.log("stlite progress:", progress);
          }},
        }},
        document.getElementById("root"),
      );

      // Hide the splash screen once stlite is done booting
      // stlite triggers a DOM mutation when the iframe is ready; we watch for it.
      const loadingScreen = document.getElementById("loading-screen");
      const observer = new MutationObserver(() => {{
        // Once the stlite root has child elements, the app is loading
        if (document.getElementById("root").children.length > 0) {{
          setTimeout(() => {{
            loadingScreen.classList.add("hidden");
            setTimeout(() => {{ loadingScreen.style.display = "none"; }}, 600);
          }}, 2000); // 2s grace period after first render
          observer.disconnect();
        }}
      }});
      observer.observe(document.getElementById("root"), {{ childList: true, subtree: false }});

      // Fallback: hide spinner after 60s no matter what
      setTimeout(() => {{
        loadingScreen.classList.add("hidden");
        setTimeout(() => {{ loadingScreen.style.display = "none"; }}, 600);
      }}, 60000);
    </script>
  </body>
</html>"""

    Path("index.html").write_text(html, encoding="utf-8")
    size_kb = len(html.encode("utf-8")) / 1024
    print(f"index.html generated ({size_kb:.1f} KB)")

if __name__ == "__main__":
    build_index()
