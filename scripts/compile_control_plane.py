import os

ARTIFACT_PATH = r"C:\Users\tamma\.gemini\antigravity\brain\fec58e9d-ead8-43d8-9377-c0f221416b9d\vault_control_plane.html"
DASHBOARD_PATH = r"C:\surya\vault\dashboard\public\index.html"
SCAFFOLD_FILE = r"C:\surya\vault\scripts\build_real_life_control_plane.mjs"
VIEWS_FILE = r"C:\surya\vault\scripts\build_ui.py"

def main():
    with open(SCAFFOLD_FILE, 'r', encoding='utf-8') as f:
        mjs_text = f.read()

    # Locate HTML base
    html_start = mjs_text.find("<!DOCTYPE html>")
    if html_start == -1:
        raise ValueError("Could not find <!DOCTYPE html>")

    script_start = mjs_text.find("<script>", html_start)
    if script_start == -1:
        raise ValueError("Could not find <script>")

    base_html = mjs_text[html_start:script_start]

    # Locate JS scaffold end
    func_marker = "window.runAllRunbookSteps"
    func_idx = mjs_text.find(func_marker, script_start)
    if func_idx == -1:
        raise ValueError(f"Could not find {func_marker}")

    # find closing '};' of window.runAllRunbookSteps
    close_idx = mjs_text.find("};", func_idx)
    if close_idx == -1:
        raise ValueError("Could not find closing }; for runAllRunbookSteps")
    script_end = close_idx + 2

    raw_js_scaffold = mjs_text[script_start:script_end]

    # Unescape escaped backticks and escaped template literals
    # In .mjs file, backticks were \` and ${ was \${
    clean_js_scaffold = raw_js_scaffold.replace(r"\`", "`").replace(r"\${", "${")

    # Now read views_code from build_ui.py
    with open(VIEWS_FILE, 'r', encoding='utf-8') as f:
        py_text = f.read()

    views_start_marker = 'views_code = """\n'
    idx_views_start = py_text.find(views_start_marker)
    if idx_views_start == -1:
        # try without newline
        views_start_marker = 'views_code = """'
        idx_views_start = py_text.find(views_start_marker)

    if idx_views_start == -1:
        raise ValueError("Could not find views_code start in build_ui.py")

    idx_views_start += len(views_start_marker)

    views_end_marker = '\n"""\n\n    full_html'
    idx_views_end = py_text.find(views_end_marker, idx_views_start)
    if idx_views_end == -1:
        # try alternative
        views_end_marker = '"""'
        idx_views_end = py_text.rfind(views_end_marker)

    views_code = py_text[idx_views_start:idx_views_end].strip()

    # Combine
    full_html = base_html + clean_js_scaffold + "\n\n" + views_code

    print(f"Base HTML length: {len(base_html)} chars")
    print(f"Scaffold JS length: {len(clean_js_scaffold)} chars")
    print(f"Views code length: {len(views_code)} chars")
    print(f"Total HTML length: {len(full_html)} chars")

    # Write to artifact
    with open(ARTIFACT_PATH, 'w', encoding='utf-8') as f:
        f.write(full_html)
    print("Successfully wrote artifact:", ARTIFACT_PATH)

    # Write to dashboard public
    os.makedirs(os.path.dirname(DASHBOARD_PATH), exist_ok=True)
    with open(DASHBOARD_PATH, 'w', encoding='utf-8') as f:
        f.write(full_html)
    print("Successfully wrote dashboard index:", DASHBOARD_PATH)

if __name__ == "__main__":
    main()
