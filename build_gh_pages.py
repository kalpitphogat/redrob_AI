import json
from pathlib import Path

# Files to embed in the stlite virtual filesystem
FILES_TO_EMBED = [
    "app.py",
    "config.py",
    "loader.py",
    "prefilter.py",
    "scorer.py",
    "honeypot.py",
    "behavioral.py",
    "reasoning.py",
    "ranker.py",
    "sample_candidates.json",
    "submission_metadata.yaml",
]

def generate_index_html():
    files_json = {}
    
    for filename in FILES_TO_EMBED:
        path = Path(filename)
        if not path.exists():
            print(f"Warning: {filename} not found, skipping...")
            continue
            
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            files_json[filename] = content
            
    # Serialize to JSON strings so they are safe to put inside <script> tag without escaping issues
    serialized_files = {name: content for name, content in files_json.items()}
    
    # HTML template with stlite mountable
    html_template = f"""<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta
      name="viewport"
      width="device-width"
      initial-scale="1, shrink-to-fit=no"
    />
    <title>Redrob AI Candidate Ranker Sandbox</title>
    <!-- stlite CSS -->
    <link
      rel="stylesheet"
      href="https://cdn.jsdelivr.net/npm/@stlite/mountable@0.64.2/build/stlite.css"
    />
    <style>
      /* Splash loading screen style */
      #loading-screen {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        color: white;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
        z-index: 9999;
        transition: opacity 0.5s ease-out;
      }}
      .spinner {{
        width: 50px;
        height: 50px;
        border: 5px solid rgba(255, 255, 255, 0.1);
        border-top: 5px solid #3b82f6;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 20px;
      }}
      @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
      }}
      .loading-title {{
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 8px;
        letter-spacing: -0.5px;
      }}
      .loading-sub {{
        font-size: 0.95rem;
        color: #94a3b8;
        max-width: 400px;
        text-align: center;
        line-height: 1.5;
      }}
    </style>
  </head>
  <body>
    <!-- Splash Screen during Pyodide & library download -->
    <div id="loading-screen">
      <div class="spinner"></div>
      <div class="loading-title">Launching Redrob Sandbox</div>
      <div class="loading-sub">Downloading Python runtime (WebAssembly) and installing dependencies (pandas, plotly, streamlit) directly in your browser. This takes a few seconds on first load...</div>
    </div>

    <!-- Container for Streamlit app -->
    <div id="root"></div>

    <!-- stlite js -->
    <script src="https://cdn.jsdelivr.net/npm/@stlite/mountable@0.64.2/build/stlite.js"></script>
    <script>
      // The python files serialized from backend
      const filesData = {json.dumps(serialized_files)};

      // Mount the Streamlit app using stlite
      stlite.mount(
        {{
          entrypoint: "app.py",
          files: filesData,
          requirements: ["pandas", "plotly", "pyyaml"],
          onMounted: () => {{
            // Fade out splash screen when streamlit finishes mounting
            const loader = document.getElementById("loading-screen");
            loader.style.opacity = "0";
            setTimeout(() => {{
              loader.remove();
            }}, 500);
          }}
        }},
        document.getElementById("root")
      );
    </script>
  </body>
</html>
"""

    output_path = Path("index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)
        
    print(f"Generated standalone index.html with {len(files_json)} files embedded successfully!")

if __name__ == "__main__":
    generate_index_html()
