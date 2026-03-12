"""
마크다운 협상제안서 → PDF 변환기 v3.0
프리미엄 디자인 + 페이지 잘림 방지 + 대형 텍스트
"""
import markdown
import os
import sys

def md_to_pdf(md_path, pdf_path=None):
    if not pdf_path:
        pdf_path = md_path.replace('.md', '.pdf')
    
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    html_body = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
    
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.0.0"></script>
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

@page {{
    size: A4;
    margin: 15mm;
}}

body {{
    font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
    font-size: 11.5pt;
    font-weight: 400;
    line-height: 1.75;
    color: #1a1a1a;
    background: #ffffff;
    width: 210mm;
    max-width: 210mm;
    box-sizing: border-box;
    margin: 0 auto;
    padding: 0;
    overflow-x: hidden;
    overflow-wrap: break-word;
    word-wrap: break-word;
}}

.page-break {{
    page-break-before: always;
    break-before: page;
    clear: both;
}}

.keep-together {{
    page-break-inside: avoid !important;
    break-inside: avoid !important;
}}

/* ===== 표지 페이지 ===== */
.cover-page {{
    page-break-after: always;
    break-after: page;
    text-align: center;
    width: 100%;
    max-width: 100%;
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    overflow: hidden;
}}

.cover-image {{
    width: 100%;
    max-width: 100%;
    height: auto;
    display: block;
    object-fit: contain;
}}

/* ===== 파트별 대제목 (강력한 구분선과 여백) ===== */
h1 {{
    font-size: 16pt;
    font-weight: 600;
    color: #1a1a1a;
    border-top: 4px solid #cc0000;
    border-bottom: 2px solid #e0e0e0;
    padding: 14px 0 12px 0;
    margin: 35px 0 25px 0;
    page-break-before: always;
    break-before: page;
    page-break-after: avoid;
    break-after: avoid;
    letter-spacing: -0.3px;
}}

h2 {{
    font-size: 13.5pt;
    font-weight: 500;
    color: #222222;
    margin: 30px 0 15px 0;
    page-break-after: avoid;
    break-after: avoid;
    padding-left: 12px;
    border-left: 4px solid #555555;
}}

h3 {{
    font-size: 12.5pt;
    font-weight: 500;
    color: #444444;
    margin: 18px 0 10px 0;
    page-break-after: avoid;
    break-after: avoid;
}}

/* ===== 테이블 (플랫/실선) ===== */
table {{
    width: 100%;
    max-width: 100%;
    border-collapse: collapse;
    margin: 15px 0 20px 0;
    font-size: 11pt;
    page-break-inside: avoid;
    break-inside: avoid;
    border-top: 2px solid #333333;
    border-bottom: 1px solid #333333;
    background: #ffffff;
    word-break: keep-all;
    overflow-wrap: break-word;
}}

thead th {{
    background: #f5f5f5;
    color: #1a1a1a;
    padding: 12px 14px;
    text-align: center;
    font-weight: 500;
    font-size: 11pt;
    border-bottom: 1px solid #999999;
}}

td {{
    padding: 10px 14px;
    border-bottom: 1px solid #dddddd;
    color: #333333;
    font-size: 11pt;
    text-align: center;
    vertical-align: middle;
}}

tr:last-child td {{
    border-bottom: none;
}}

table strong {{
    color: inherit;
    font-weight: 600;
}}

strong {{ color: inherit; font-weight: 600; }}

/* ===== 인용 블록 ===== */
blockquote {{
    background: #fafafa;
    border-left: 4px solid #cc0000;
    padding: 16px 20px;
    margin: 18px 0;
    font-size: 11.5pt;
    line-height: 1.7;
    color: #444444;
    page-break-inside: avoid;
    break-inside: avoid;
}}

/* ===== 차트 박스 ===== */
.chart-container {{
    position: relative;
    width: 100%;
    max-width: 100%;
    margin: 25px 0;
    padding: 20px;
    background: #fff;
    border: 1px solid #dddddd;
    page-break-inside: avoid;
}}
canvas {{ max-height: 450px; }}

hr {{
    border: none;
    height: 1px;
    background: #cccccc;
    margin: 35px 0;
}}

ul, ol {{
    margin: 12px 0 12px 24px;
    font-size: 12pt;
    color: #333333;
}}

li {{
    margin: 8px 0;
    line-height: 1.8;
}}

p {{
    margin: 12px 0;
    font-size: 12.5pt;
    color: #333333;
}}

.doc-footer {{
    text-align: center;
    font-size: 10pt;
    color: #999999;
    margin-top: 50px;
    padding-top: 25px;
    border-top: 1px solid #cccccc;
    line-height: 1.6;
}}

/* ===== 인쇄/PDF 최적화 ===== */
@media print {{
    @page {{
        size: A4;
        margin: 15mm;
    }}

    body {{ 
        width: 100%;
        margin: 0;
        padding: 0;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }}
    
    .page-break {{
        page-break-before: always !important;
        break-before: page !important;
    }}
    
    table, blockquote, pre, .keep-together, .chart-container {{ 
        page-break-inside: avoid !important; 
        break-inside: avoid !important;
    }}
    
    h2, h3 {{ 
        page-break-after: avoid !important;
        break-after: avoid !important;
    }}
}}
</style>
</head>
<body>
{html_body}
</body>
</html>"""
    
    html_path = md_path.replace('.md', '.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    # Try pdfkit (wkhtmltopdf)
    try:
        import pdfkit
        options = {
            'encoding': 'UTF-8',
            'page-size': 'A4',
            'margin-top': '12mm',
            'margin-right': '12mm',
            'margin-bottom': '12mm',
            'margin-left': '12mm',
            'enable-local-file-access': '',
            'no-outline': None,
            'print-media-type': '',
        }
        pdfkit.from_file(html_path, pdf_path, options=options)
        print(f"[OK] PDF 생성: {pdf_path}")
        os.remove(html_path)
        return pdf_path
    except Exception as e:
        print(f"[INFO] pdfkit 실패: {e}")
        print(f"[OK] HTML 생성: {html_path}")
        print(f"  -> 브라우저에서 열어 Ctrl+P로 PDF 인쇄하세요")
        return html_path


if __name__ == "__main__":
    if len(sys.argv) > 1:
        md_file = sys.argv[1]
    else:
        md_file = os.path.join(os.path.dirname(__file__), 
                               '협상제안서_출력', '협상제안서_410동_1701호_매매_20260308.md')
    
    result = md_to_pdf(md_file)
