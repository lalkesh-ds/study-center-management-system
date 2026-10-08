import os
import re
import subprocess
from pathlib import Path
from markdown_it import MarkdownIt
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer, TextLexer
from pygments.formatters import HtmlFormatter

def syntax_highlight(code, lang, attrs):
    if not lang:
        try:
            lexer = guess_lexer(code)
        except Exception:
            lexer = TextLexer()
    else:
        try:
            lexer = get_lexer_by_name(lang.strip().lower())
        except Exception:
            lexer = TextLexer()
            
    formatter = HtmlFormatter(nowrap=True)
    highlighted = highlight(code, lexer, formatter)
    return f'<div class="code-wrapper"><pre class="highlight"><code class="language-{lang}">{highlighted}</code></pre></div>'

def generate_pdf():
    base_dir = Path(r"d:\Desktop\library management system")
    md_file = base_dir / "docs" / "MASTER_TECHNICAL_SPECIFICATION.md"
    html_file = base_dir / "docs" / "MASTER_TECHNICAL_SPECIFICATION.html"
    pdf_file = base_dir / "Smart_Library_Master_Technical_Architecture_Specification_v1.0.pdf"

    with open(md_file, "r", encoding="utf-8") as f:
        md_text = f.read()

    md = (
        MarkdownIt("commonmark", {"highlight": syntax_highlight})
        .enable("table")
        .disable("linkify")
    )
    
    rendered_body = md.render(md_text)

    # Pygments print-friendly CSS
    pygments_css = HtmlFormatter(style="default").get_style_defs(".highlight")

    # Wrap the first title and metadata table into a formal cover page
    # Search for the first HR or Table of Contents to separate cover from body
    cover_html = """
    <div class="cover-page">
        <div class="cover-badge">Master Technical Specification & Architecture</div>
        <h1 class="cover-title">Smart Library & Study Center<br>Management System</h1>
        <div class="cover-subtitle">Master Technical Architecture & Engineering Specification</div>
        
        <div class="cover-meta-card">
            <table class="cover-table">
                <tr><td><strong>Document Reference</strong></td><td>LMS-SPEC-V1.0</td></tr>
                <tr><td><strong>Architecture Version</strong></td><td>1.0.0 (Pre-Implementation Baseline)</td></tr>
                <tr><td><strong>Classification</strong></td><td>Technical Source of Truth (SSOT)</td></tr>
                <tr><td><strong>Effective Date</strong></td><td>October 2026</td></tr>
                <tr><td><strong>Facility Scale</strong></td><td>100 Physical Seats (Desk 1 to 100)</td></tr>
                <tr><td><strong>Daily Capacity</strong></td><td>300 Seat-Slots / 1,600 Daily Seat-Hours</td></tr>
                <tr><td><strong>Operating Hours</strong></td><td>07:00 AM – 11:00 PM (16 Operating Hours / Day)</td></tr>
                <tr><td><strong>Primary Core Stack</strong></td><td>Python 3.10+ | FastAPI | PostgreSQL 15+ | SQLAlchemy 2.0 | Streamlit</td></tr>
                <tr><td><strong>Authorial Roles</strong></td><td>Senior Software Architect, Backend Engineer, Database Architect, Data Engineer</td></tr>
            </table>
        </div>
        
        <div class="cover-footer">
            <p><strong>CONFIDENTIAL & PROPRIETARY</strong></p>
            <p>This master architecture document governs the end-to-end engineering, database constraints, business logic, API contracts, and phased execution of the Smart Library & Study Center platform. Autonomous AI models and human developers must adhere to this document as the authoritative architectural baseline.</p>
        </div>
    </div>
    """

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Smart Library Management System - Master Technical Architecture Specification v1.0</title>
<!-- KaTeX -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"
    onload="renderMathInElement(document.body, {{
        delimiters: [
            {{left: '$$', right: '$$', display: true}},
            {{left: '$', right: '$', display: false}}
        ],
        throwOnError : false
    }});"></script>

<style>
@page {{
    size: A4;
    margin: 20mm 15mm 20mm 15mm;
    @top-right {{
        content: "Smart Library Architecture v1.0";
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 8pt;
        color: #64748b;
    }}
    @bottom-center {{
        content: "Page " counter(page) " of " counter(pages);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 8pt;
        color: #64748b;
    }}
}}

body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #1e293b;
    background-color: #ffffff;
    line-height: 1.55;
    font-size: 10pt;
    margin: 0;
    padding: 0;
}}

/* Cover Page */
.cover-page {{
    page-break-after: always;
    padding-top: 30px;
    text-align: center;
}}

.cover-badge {{
    display: inline-block;
    padding: 6px 16px;
    background-color: #eff6ff;
    border: 1px solid #bfdbfe;
    color: #1d4ed8;
    font-weight: 700;
    font-size: 9pt;
    border-radius: 20px;
    margin-bottom: 24px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}}

.cover-title {{
    font-size: 26pt;
    color: #0f172a;
    font-weight: 800;
    line-height: 1.2;
    margin-bottom: 12px;
    border: none !important;
}}

.cover-subtitle {{
    font-size: 14pt;
    color: #2563eb;
    font-weight: 600;
    margin-bottom: 35px;
}}

.cover-meta-card {{
    width: 90%;
    margin: 0 auto;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}}

.cover-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 9.5pt;
    text-align: left;
    margin: 0 !important;
}}

.cover-table td {{
    padding: 9px 14px;
    border-bottom: 1px solid #e2e8f0;
}}

.cover-table tr:last-child td {{
    border-bottom: none;
}}

.cover-table td:first-child {{
    width: 35%;
    background-color: #f8fafc;
    color: #334155;
}}

.cover-footer {{
    margin-top: 50px;
    padding: 0 40px;
    font-size: 8.5pt;
    color: #64748b;
    line-height: 1.5;
}}

/* Typography */
h1, h2, h3, h4, h5, h6 {{
    color: #0f172a;
    font-weight: 700;
    line-height: 1.25;
    margin-top: 1.8em;
    margin-bottom: 0.6em;
    page-break-after: avoid;
}}

h1 {{
    font-size: 20pt;
    border-bottom: 2px solid #2563eb;
    padding-bottom: 6px;
    margin-top: 0;
    color: #1e3a8a;
}}

h2 {{
    font-size: 15pt;
    border-bottom: 1px solid #cbd5e1;
    padding-bottom: 4px;
    color: #1e40af;
}}

h3 {{
    font-size: 12pt;
    color: #1e293b;
}}

h4 {{
    font-size: 10.5pt;
    color: #334155;
}}

p {{
    margin-top: 0;
    margin-bottom: 0.85em;
    text-align: justify;
}}

ul, ol {{
    margin-top: 0;
    margin-bottom: 0.85em;
    padding-left: 22px;
}}

li {{
    margin-bottom: 0.3em;
}}

hr {{
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 1.8em 0;
}}

strong {{
    color: #0f172a;
    font-weight: 600;
}}

/* Tables */
table {{
    width: 100%;
    border-collapse: collapse;
    margin: 1.2em 0;
    font-size: 9pt;
    page-break-inside: avoid;
}}

th, td {{
    border: 1px solid #cbd5e1;
    padding: 6px 9px;
    text-align: left;
    vertical-align: top;
}}

th {{
    background-color: #f1f5f9;
    color: #0f172a;
    font-weight: 600;
}}

tr:nth-child(even) td {{
    background-color: #f8fafc;
}}

/* Code & Pre */
pre.highlight, pre {{
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #3b82f6;
    border-radius: 4px;
    padding: 9px 12px;
    font-family: "JetBrains Mono", "Cascadia Code", Consolas, "Courier New", monospace;
    font-size: 8.4pt;
    line-height: 1.45;
    overflow-x: auto;
    white-space: pre-wrap;
    word-break: break-all;
    page-break-inside: avoid;
    margin: 0.9em 0;
}}

code {{
    font-family: "JetBrains Mono", "Cascadia Code", Consolas, "Courier New", monospace;
    font-size: 8.8pt;
    background-color: #f1f5f9;
    padding: 2px 4px;
    border-radius: 3px;
    color: #0f172a;
}}

pre code {{
    background-color: transparent;
    padding: 0;
    border-radius: 0;
    color: inherit;
}}

/* Pygments Highlighting */
{pygments_css}

/* Callouts & Quotes */
blockquote {{
    border-left: 4px solid #2563eb;
    background-color: #eff6ff;
    margin: 1em 0;
    padding: 8px 14px;
    color: #1e3a8a;
    border-radius: 0 4px 4px 0;
}}
</style>
</head>
<body>

{cover_html}

{rendered_body}

</body>
</html>
"""

    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_template)
    
    print(f"HTML written to: {html_file}")

    # Headless Chrome PDF generation
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(chrome_path):
        chrome_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        
    cmd = [
        chrome_path,
        "--headless=new",
        "--disable-gpu",
        "--allow-file-access-from-files",
        "--run-all-compositor-stages-before-draw",
        f"--print-to-pdf={str(pdf_file)}",
        f"file:///{str(html_file).replace(os.sep, '/')}"
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(pdf_file):
        size_kb = os.path.getsize(pdf_file) / 1024
        print(f"PDF generated successfully: {pdf_file} ({size_kb:.2f} KB)")
    else:
        print("PDF generation failed! Stderr:", res.stderr)

if __name__ == "__main__":
    generate_pdf()
