from fpdf import FPDF

class PDFReport(FPDF):
    def header(self):
        # Logo or Title
        self.set_font('Arial', 'B', 16)
        self.set_text_color(59, 130, 246) # Blue
        self.cell(0, 10, 'Quantum-Shield Security Audit', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf(results, filename="audit_report.pdf"):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # 1. Summary Section
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Scan Summary", 0, 1)
    
    total_issues = len(results) if results else 0
    pdf.set_font("Arial", "", 10)
    
    if total_issues == 0:
        pdf.set_text_color(34, 197, 94) # Green
        pdf.cell(0, 10, "Status: PASSED - No Quantum Vulnerabilities Found", 0, 1)
    else:
        pdf.set_text_color(239, 68, 68) # Red
        pdf.cell(0, 10, f"Status: FAILED - {total_issues} Vulnerabilities Detected", 0, 1)

    pdf.ln(10)

    # 2. Detailed Findings
    if results:
        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, "Detailed Findings", 0, 1)
        pdf.ln(2)

        for issue in results:
            # Issue Title (Red Box effect)
            pdf.set_fill_color(254, 226, 226) # Light Red bg
            pdf.set_text_color(185, 28, 28) # Dark Red text
            pdf.set_font("Arial", "B", 10)
            check_id = issue.get('check_id', 'Unknown Issue')
            pdf.cell(0, 8, f" {check_id}", 0, 1, fill=True)
            
            # File Location
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", "", 9)
            path = issue.get('path', 'unknown')
            line = issue.get('start', {}).get('line', '?')
            pdf.cell(0, 6, f"File: {path} (Line {line})", 0, 1)

            # Code Snippet (Gray Box)
            pdf.set_fill_color(241, 245, 249) # Slate 100
            pdf.set_font("Courier", "", 8)
            code = issue.get('extra', {}).get('lines', '').strip()
            pdf.multi_cell(0, 5, code, fill=True)
            
            # Recommendation
            pdf.set_font("Arial", "I", 9)
            msg = issue.get('extra', {}).get('message', 'No fix provided.')
            pdf.multi_cell(0, 5, f"Fix: {msg}")
            
            pdf.ln(5) # Space between issues

    # Output
    output_path = f"/tmp/{filename}" if filename != "audit_report.pdf" else filename
    # Local windows fallback for testing
    if not output_path.startswith("/tmp/"):
        output_path = filename
        
    pdf.output(output_path)
    return output_path