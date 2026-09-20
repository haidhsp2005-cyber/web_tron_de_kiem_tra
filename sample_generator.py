import os
import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import qn, nsdecls

RED_COLOR = RGBColor(220, 38, 38)
BLUE_COLOR = RGBColor(30, 64, 175)
GRAY_COLOR = RGBColor(107, 114, 128)

def add_run(p, text, bold=False, italic=False, is_red=False, sub=False, sup=False, size=Pt(12), font_name="Times New Roman"):
    r = p.add_run(text)
    r.bold = bold
    r.italic = italic
    r.font.name = font_name
    r.font.size = size
    if is_red:
        r.font.color.rgb = RED_COLOR
    if sub or sup:
        rPr = r._r.get_or_add_rPr()
        va = OxmlElement('w:vertAlign')
        va.set(qn('w:val'), 'subscript' if sub else 'superscript')
        rPr.append(va)
    return r

def set_table_no_borders(table):
    """Sets all borders of a table to none."""
    tblPr = table._tbl.tblPr
    tblBorders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="none"/><w:left w:val="none"/><w:bottom w:val="none"/><w:right w:val="none"/>'
        f'<w:insideH w:val="none"/><w:insideV w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(tblBorders)

def format_cell(cell, bg_hex=None, bold=False, align=WD_ALIGN_PARAGRAPH.CENTER, font_size=Pt(10.5)):
    p = cell.paragraphs[0]
    p.alignment = align
    if bg_hex:
        tcPr = cell._tc.get_or_add_tcPr()
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{bg_hex}"/>')
        tcPr.append(shd)
    for r in p.runs:
        r.bold = bold
        r.font.name = "Times New Roman"
        r.font.size = font_size

def set_cell_box_border(cell, color="4B5563", sz="8"):
    """Sets a thin solid border around a single cell for answer boxes."""
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:right w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)

def add_part3_answer_box(doc):
    """Creates a clean answer box table under Part III question for student handwriting."""
    tbl_ans = doc.add_table(rows=1, cols=2)
    tbl_ans.alignment = WD_TABLE_ALIGNMENT.LEFT
    tbl_ans.autofit = False
    set_table_no_borders(tbl_ans)

    for r in tbl_ans.rows:
        trPr = r._tr.get_or_add_trPr()
        trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

    c0 = tbl_ans.cell(0, 0)
    c0.width = Inches(0.9)
    p0 = c0.paragraphs[0]
    p0.paragraph_format.space_before = Pt(2)
    p0.paragraph_format.space_after = Pt(2)
    p0.paragraph_format.line_spacing = 1.15
    add_run(p0, "Đáp án:", bold=True, size=Pt(11))

    c1 = tbl_ans.cell(0, 1)
    c1.width = Inches(2.2)
    set_cell_box_border(c1, color="4B5563", sz="8")
    p1 = c1.paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p1.paragraph_format.space_before = Pt(3)
    p1.paragraph_format.space_after = Pt(3)
    p1.paragraph_format.line_spacing = Pt(14)
    add_run(p1, "")

def add_2x2_choices(doc, choices: list[tuple[str, str]], correct_key: str = None):
    """
    Creates a 2x2 borderless table for choices:
    Row 0: Cell 0 = A, Cell 1 = B
    Row 1: Cell 0 = C, Cell 1 = D
    If correct_key is provided, highlights the correct choice with bold & red.
    """
    tbl = doc.add_table(rows=2, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    set_table_no_borders(tbl)

    for r in tbl.rows:
        trPr = r._tr.get_or_add_trPr()
        trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

    cells = [
        (tbl.cell(0, 0), choices[0][0], choices[0][1]),
        (tbl.cell(0, 1), choices[1][0], choices[1][1]),
        (tbl.cell(1, 0), choices[2][0], choices[2][1]),
        (tbl.cell(1, 1), choices[3][0], choices[3][1]),
    ]
    for cell, k, val in cells:
        cell.width = Inches(3.35)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.15
        is_corr = (k.strip().upper() == (correct_key or "").strip().upper())
        add_run(p, f"{k}. ", bold=True, is_red=is_corr)
        add_run(p, val, bold=is_corr, is_red=is_corr)

def setup_footer(doc, code: str = "101"):
    """Sets up exam footer: left = Mã đề thi: {code}, right = Trang {PAGE}/{NUMPAGES} across all pages."""
    for sec in doc.sections:
        sec.footer_distance = Inches(0.40)
        footer = sec.footer
        footer.is_linked_to_previous = False

        p = footer.paragraphs[0]
        p.text = ""
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0

        p.paragraph_format.tab_stops.clear_all()
        p.paragraph_format.tab_stops.add_tab_stop(Inches(6.87), WD_TAB_ALIGNMENT.RIGHT)

        left_text = f"Mã đề thi: {code}"
        r_code = p.add_run(left_text)
        r_code.font.name = "Times New Roman"
        r_code.font.size = Pt(10)
        r_code.italic = True

        p.add_run("\t")

        r_trang = p.add_run("Trang ")
        r_trang.font.name = "Times New Roman"
        r_trang.font.size = Pt(10)
        r_trang.italic = True

        fld_page = parse_xml(
            f'<w:fldSimple {nsdecls("w")} w:instr="PAGE">'
            f'<w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:i/><w:sz w:val="20"/></w:rPr><w:t>1</w:t></w:r>'
            f'</w:fldSimple>'
        )
        p._p.append(fld_page)

        r_slash = p.add_run("/")
        r_slash.font.name = "Times New Roman"
        r_slash.font.size = Pt(10)
        r_slash.italic = True

        fld_numpages = parse_xml(
            f'<w:fldSimple {nsdecls("w")} w:instr="NUMPAGES">'
            f'<w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:i/><w:sz w:val="20"/></w:rPr><w:t>1</w:t></w:r>'
            f'</w:fldSimple>'
        )
        p._p.append(fld_numpages)

def create_sample_docx(output_path="samples/de_thi_mau_chuan.docx"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc = docx.Document()
    
    for section in doc.sections:
        section.top_margin = Inches(0.70)
        section.bottom_margin = Inches(0.70)
        section.left_margin = Inches(0.70)
        section.right_margin = Inches(0.70)

    setup_footer(doc, "101")
        
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)
    style.paragraph_format.line_spacing = 1.15
    
    # 0. INSTRUCTIONS BOX
    tbl_intro = doc.add_table(rows=1, cols=1)
    tbl_intro.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell_intro = tbl_intro.cell(0, 0)
    tcPr = cell_intro._tc.get_or_add_tcPr()
    shd = parse_xml(r'<w:shd {} w:fill="FFFBEB"/>'.format(nsdecls('w')))
    tcPr.append(shd)
    
    ip = cell_intro.paragraphs[0]
    add_run(ip, "📌 HƯỚNG DẪN ĐỊNH DẠNG ĐỀ THI TOÁN LỚP 12 CÓ IN ĐẬM ĐÁP ÁN ĐỎ:", bold=True, size=Pt(11))
    
    points = [
        ("• Cấu trúc 4 phần chuẩn Bộ GD&ĐT 2025+: ", "PHẦN I (Trắc nghiệm 4 lựa chọn), PHẦN II (Trắc nghiệm Đúng/Sai), PHẦN III (Trả lời ngắn), PHẦN IV (Tự luận)."),
        ("• Tự động nhận diện đáp án IN ĐẬM ĐỎ: ", "Phần I: Phương án đúng được in đậm màu đỏ. Phần II: Các ý có (Đúng)/(Sai) in đậm đỏ. Phần III: Có dòng 'Đáp án: [số]' in đậm đỏ. Phần IV: Có 'Hướng dẫn chấm' in đậm đỏ."),
        ("• Dàn 2 phương án / dòng: ", "Các câu hỏi toán được bố trí 2 phương án một dòng (A & B dòng 1; C & D dòng 2) theo đúng mẫu đề thi chính thức."),
        ("• Bảo toàn công thức Toán 12: ", "Hỗ trợ công thức số mũ (x², x³), căn số (√), tích phân (∫), vectơ (a⃗, u⃗), phân số hoàn toàn nguyên vẹn khi đảo đề.")
    ]
    for bold_txt, normal_txt in points:
        p_sub = cell_intro.add_paragraph()
        p_sub.paragraph_format.space_before = Pt(2)
        p_sub.paragraph_format.space_after = Pt(2)
        add_run(p_sub, bold_txt, bold=True, size=Pt(10.5))
        add_run(p_sub, normal_txt, size=Pt(10.5))
        
    doc.add_paragraph()
    
    # 1. HEADER
    tbl_header = doc.add_table(rows=1, cols=2)
    tbl_header.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_header.autofit = False
    set_table_no_borders(tbl_header)

    c00 = tbl_header.cell(0, 0)
    c00.width = Inches(3.1)
    p00 = c00.paragraphs[0]
    p00.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_run(p00, "SỞ GIÁO DỤC VÀ ĐÀO TẠO\n", bold=True, size=Pt(10))
    add_run(p00, "TRƯỜNG THPT LONG CANG\n", bold=True, size=Pt(11))
    add_run(p00, "NĂM HỌC 2026 - 2027", bold=True, size=Pt(10))

    c01 = tbl_header.cell(0, 1)
    c01.width = Inches(3.6)
    p01 = c01.paragraphs[0]
    p01.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_run(p01, "ĐỀ KIỂM TRA CHÍNH THỨC\n", bold=True, size=Pt(11))
    add_run(p01, "BÀI THI: TOÁN (LỚP 12) - ĐỀ MẪU CÓ ĐÁP ÁN ĐỎ\n", bold=True, size=Pt(11.5))
    add_run(p01, "Thời gian làm bài: 90 phút (không kể thời gian phát đề)\n", italic=True, size=Pt(10))
    add_run(p01, "MÃ ĐỀ GỐC: 000", bold=True, size=Pt(11.5))

    # 2. Student Info Section (Clean 2-line layout matching official exam template)
    p_info1 = doc.add_paragraph()
    p_info1.paragraph_format.space_before = Pt(8)
    p_info1.paragraph_format.space_after = Pt(2)
    p_info1.paragraph_format.line_spacing = 1.15
    add_run(p_info1, "Họ và tên thí sinh: .................................................... Lớp: .....................", size=Pt(11))

    p_info2 = doc.add_paragraph()
    p_info2.paragraph_format.space_before = Pt(2)
    p_info2.paragraph_format.space_after = Pt(8)
    p_info2.paragraph_format.line_spacing = 1.15
    add_run(p_info2, "Số báo danh: ....................................................", size=Pt(11))
    
    # ==================== PHẦN I: TRẮC NGHIỆM 4 PHƯƠNG ÁN (IN ĐẬM ĐÁP ÁN ĐỎ) ====================
    p_p1 = doc.add_paragraph()
    p_p1.paragraph_format.space_before = Pt(10)
    p_p1.paragraph_format.space_after = Pt(4)
    add_run(p_p1, "PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn.", bold=True, size=Pt(12.5))
    p_p1_note = doc.add_paragraph()
    p_p1_note.paragraph_format.space_after = Pt(6)
    add_run(p_p1_note, "Thí sinh trả lời từ câu 1 đến câu 6. Mỗi câu hỏi thí sinh chỉ chọn một phương án. (Đáp án đúng được in đậm màu đỏ)", italic=True)
    
    # Q1: Đơn điệu hàm số (B đúng)
    p_q1 = doc.add_paragraph()
    add_run(p_q1, "Câu 1: ", bold=True)
    add_run(p_q1, "Cho hàm số ")
    add_run(p_q1, "y = f(x)", italic=True)
    add_run(p_q1, " có đạo hàm ")
    add_run(p_q1, "f'(x) = x(x - 2)(x + 1)", italic=True)
    add_run(p_q1, ". Hàm số đã cho đồng biến trên khoảng nào dưới đây?")
    add_2x2_choices(doc, [
        ("A", "(-1; 0)."),
        ("B", "(2; +∞)."),
        ("C", "(0; 2)."),
        ("D", "(-∞; -1).")
    ], correct_key="B")
    
    # Q2: Tiệm cận (B đúng)
    p_q2 = doc.add_paragraph()
    add_run(p_q2, "Câu 2: ", bold=True)
    add_run(p_q2, "Đồ thị hàm số ")
    add_run(p_q2, "y = (2x - 1)/(x + 1)", italic=True)
    add_run(p_q2, " có đường tiệm cận đứng là:")
    add_2x2_choices(doc, [
        ("A", "x = 2."),
        ("B", "x = -1."),
        ("C", "y = 2."),
        ("D", "y = -1.")
    ], correct_key="B")

    # Q3: Cực trị (B đúng)
    p_q3 = doc.add_paragraph()
    add_run(p_q3, "Câu 3: ", bold=True)
    add_run(p_q3, "Cho hàm số ")
    add_run(p_q3, "y = x³ - 3x + 2", italic=True)
    add_run(p_q3, ". Điểm cực đại của đồ thị hàm số là:")
    add_2x2_choices(doc, [
        ("A", "M(1; 0)."),
        ("B", "N(-1; 4)."),
        ("C", "P(0; 2)."),
        ("D", "Q(2; 4).")
    ], correct_key="B")

    # Q4: Nguyên hàm (B đúng)
    p_q4 = doc.add_paragraph()
    add_run(p_q4, "Câu 4: ", bold=True)
    add_run(p_q4, "Họ nguyên hàm của hàm số ")
    add_run(p_q4, "f(x) = 3x² + cos x", italic=True)
    add_run(p_q4, " là:")
    add_2x2_choices(doc, [
        ("A", "F(x) = x³ - sin x + C."),
        ("B", "F(x) = x³ + sin x + C."),
        ("C", "F(x) = 6x + sin x + C."),
        ("D", "F(x) = x³ + cos x + C.")
    ], correct_key="B")

    # Q5: Mặt cầu Oxyz (A đúng)
    p_q5 = doc.add_paragraph()
    add_run(p_q5, "Câu 5: ", bold=True)
    add_run(p_q5, "Trong không gian với hệ tọa độ Oxyz, cho mặt cầu (S): ")
    add_run(p_q5, "(x - 1)² + (y + 2)² + (z - 3)² = 16", italic=True)
    add_run(p_q5, ". Tọa độ tâm I và bán kính R của (S) là:")
    add_2x2_choices(doc, [
        ("A", "I(1; -2; 3), R = 4."),
        ("B", "I(-1; 2; -3), R = 4."),
        ("C", "I(1; -2; 3), R = 16."),
        ("D", "I(-1; 2; -3), R = 16.")
    ], correct_key="A")

    # Q6: Vectơ không gian Oxyz (A đúng)
    p_q6 = doc.add_paragraph()
    add_run(p_q6, "Câu 6: ", bold=True)
    add_run(p_q6, "Trong không gian Oxyz, cho hai vectơ ")
    add_run(p_q6, "a⃗ = (1; 2; -1)", italic=True)
    add_run(p_q6, " và ")
    add_run(p_q6, "b⃗ = (2; 0; 1)", italic=True)
    add_run(p_q6, ". Tọa độ của vectơ ")
    add_run(p_q6, "u⃗ = a⃗ + 2b⃗", italic=True)
    add_run(p_q6, " là:")
    add_2x2_choices(doc, [
        ("A", "u⃗ = (5; 2; 1)."),
        ("B", "u⃗ = (3; 2; 0)."),
        ("C", "u⃗ = (5; 4; 1)."),
        ("D", "u⃗ = (4; 2; -1).")
    ], correct_key="A")

    # ==================== PHẦN II: TRẮC NGHIỆM ĐÚNG SAI (IN ĐẬM ĐÁP ÁN ĐỎ) ====================
    p_p2 = doc.add_paragraph()
    p_p2.paragraph_format.space_before = Pt(12)
    p_p2.paragraph_format.space_after = Pt(4)
    add_run(p_p2, "PHẦN II. Câu trắc nghiệm đúng sai.", bold=True, size=Pt(12.5))
    p_p2_note = doc.add_paragraph()
    p_p2_note.paragraph_format.space_after = Pt(6)
    add_run(p_p2_note, "Thí sinh trả lời từ câu 1 đến câu 2. Trong mỗi ý a), b), c), d) ở mỗi câu, thí sinh chọn Đúng hoặc Sai. (Đáp án Đúng/Sai được in đậm màu đỏ)", italic=True)
    
    # Q1: Ứng dụng đạo hàm tối ưu chi phí
    p_p2_q1 = doc.add_paragraph()
    add_run(p_p2_q1, "Câu 1: ", bold=True)
    add_run(p_p2_q1, "Một doanh nghiệp sản xuất độc quyền một loại sản phẩm. Biết rằng hàm tổng chi phí sản xuất x sản phẩm (nghìn đồng) được cho bởi công thức ")
    add_run(p_p2_q1, "C(x) = x³ - 30x² + 400x + 500", italic=True)
    add_run(p_p2_q1, " (với 0 ≤ x ≤ 25):")
    
    p_p2_q1_a = doc.add_paragraph()
    p_p2_q1_a.paragraph_format.space_before = Pt(1)
    p_p2_q1_a.paragraph_format.space_after = Pt(1)
    add_run(p_p2_q1_a, "a) Chi phí cố định khi chưa sản xuất sản phẩm nào (x = 0) là 500 nghìn đồng. ")
    add_run(p_p2_q1_a, "(Đúng)", bold=True, is_red=True)

    p_p2_q1_b = doc.add_paragraph()
    p_p2_q1_b.paragraph_format.space_before = Pt(1)
    p_p2_q1_b.paragraph_format.space_after = Pt(1)
    add_run(p_p2_q1_b, "b) Chi phí biên tại mức sản lượng x = 10 là C'(10) = 100 nghìn đồng. ")
    add_run(p_p2_q1_b, "(Đúng)", bold=True, is_red=True)

    p_p2_q1_c = doc.add_paragraph()
    p_p2_q1_c.paragraph_format.space_before = Pt(1)
    p_p2_q1_c.paragraph_format.space_after = Pt(1)
    add_run(p_p2_q1_c, "c) Chi phí sản xuất trung bình cho mỗi sản phẩm luôn giảm khi số lượng sản phẩm tăng từ 0 đến 25. ")
    add_run(p_p2_q1_c, "(Sai)", bold=True, is_red=True)

    p_p2_q1_d = doc.add_paragraph()
    p_p2_q1_d.paragraph_format.space_before = Pt(1)
    p_p2_q1_d.paragraph_format.space_after = Pt(1)
    add_run(p_p2_q1_d, "d) Tổng chi phí sản xuất đạt giá trị nhỏ nhất khi mức sản lượng x = 20 sản phẩm. ")
    add_run(p_p2_q1_d, "(Sai)", bold=True, is_red=True)

    # Q2: Tọa độ Oxyz tam giác và mặt phẳng
    p_p2_q2 = doc.add_paragraph()
    add_run(p_p2_q2, "Câu 2: ", bold=True)
    add_run(p_p2_q2, "Trong không gian Oxyz, cho ba điểm ")
    add_run(p_p2_q2, "A(1; 0; 2), B(-1; 1; 3), C(3; 2; 1)", italic=True)
    add_run(p_p2_q2, " và mặt phẳng ")
    add_run(p_p2_q2, "(P): 2x - y + 2z - 5 = 0", italic=True)
    add_run(p_p2_q2, ":")
    
    p_p2_q2_a = doc.add_paragraph()
    p_p2_q2_a.paragraph_format.space_before = Pt(1)
    p_p2_q2_a.paragraph_format.space_after = Pt(1)
    add_run(p_p2_q2_a, "a) Tọa độ trọng tâm G của tam giác ABC là G(1; 1; 2). ")
    add_run(p_p2_q2_a, "(Đúng)", bold=True, is_red=True)

    p_p2_q2_b = doc.add_paragraph()
    p_p2_q2_b.paragraph_format.space_before = Pt(1)
    p_p2_q2_b.paragraph_format.space_after = Pt(1)
    add_run(p_p2_q2_b, "b) Mặt phẳng (P) có một vectơ pháp tuyến là n⃗ = (2; -1; 2). ")
    add_run(p_p2_q2_b, "(Đúng)", bold=True, is_red=True)

    p_p2_q2_c = doc.add_paragraph()
    p_p2_q2_c.paragraph_format.space_before = Pt(1)
    p_p2_q2_c.paragraph_format.space_after = Pt(1)
    add_run(p_p2_q2_c, "c) Điểm A(1; 0; 2) nằm trên mặt phẳng (P). ")
    add_run(p_p2_q2_c, "(Sai)", bold=True, is_red=True)

    p_p2_q2_d = doc.add_paragraph()
    p_p2_q2_d.paragraph_format.space_before = Pt(1)
    p_p2_q2_d.paragraph_format.space_after = Pt(1)
    add_run(p_p2_q2_d, "d) Khoảng cách từ gốc tọa độ O đến mặt phẳng (P) bằng 1. ")
    add_run(p_p2_q2_d, "(Sai)", bold=True, is_red=True)

    # ==================== PHẦN III: TRẢ LỜI NGẮN (IN ĐẬM ĐÁP ÁN ĐỎ) ====================
    p_p3 = doc.add_paragraph()
    p_p3.paragraph_format.space_before = Pt(12)
    p_p3.paragraph_format.space_after = Pt(4)
    add_run(p_p3, "PHẦN III. Câu trắc nghiệm trả lời ngắn.", bold=True, size=Pt(12.5))
    p_p3_note = doc.add_paragraph()
    p_p3_note.paragraph_format.space_after = Pt(6)
    add_run(p_p3_note, "Thí sinh trả lời từ câu 1 đến câu 3. Thí sinh điền kết quả vào ô tương ứng. (Đáp án được in đậm màu đỏ)", italic=True)
    
    # Q1: GTLN (Đáp án: 9)
    p_p3_q1 = doc.add_paragraph()
    p_p3_q1.paragraph_format.space_before = Pt(3)
    p_p3_q1.paragraph_format.space_after = Pt(1)
    add_run(p_p3_q1, "Câu 1: ", bold=True)
    add_run(p_p3_q1, "Tìm giá trị lớn nhất của hàm số ")
    add_run(p_p3_q1, "y = -x² + 4x + 5", italic=True)
    add_run(p_p3_q1, " trên đoạn [0; 3].")
    p_ans_q1 = doc.add_paragraph()
    p_ans_q1.paragraph_format.space_before = Pt(1)
    p_ans_q1.paragraph_format.space_after = Pt(3)
    add_run(p_ans_q1, "Đáp án: ", bold=True, is_red=True)
    add_run(p_ans_q1, "9", bold=True, is_red=True)

    # Q2: Tích phân (Đáp án: 12)
    p_p3_q2 = doc.add_paragraph()
    p_p3_q2.paragraph_format.space_before = Pt(3)
    p_p3_q2.paragraph_format.space_after = Pt(1)
    add_run(p_p3_q2, "Câu 2: ", bold=True)
    add_run(p_p3_q2, "Tính tích phân ")
    add_run(p_p3_q2, "I = ∫ (2x + 1) dx", italic=True)
    add_run(p_p3_q2, " từ 0 đến 3.")
    p_ans_q2 = doc.add_paragraph()
    p_ans_q2.paragraph_format.space_before = Pt(1)
    p_ans_q2.paragraph_format.space_after = Pt(3)
    add_run(p_ans_q2, "Đáp án: ", bold=True, is_red=True)
    add_run(p_ans_q2, "12", bold=True, is_red=True)

    # Q3: Bán kính mặt cầu Oxyz (Đáp án: 3)
    p_p3_q3 = doc.add_paragraph()
    p_p3_q3.paragraph_format.space_before = Pt(3)
    p_p3_q3.paragraph_format.space_after = Pt(1)
    add_run(p_p3_q3, "Câu 3: ", bold=True)
    add_run(p_p3_q3, "Trong không gian Oxyz, cho mặt cầu (S) có tâm ")
    add_run(p_p3_q3, "I(1; 1; 2)", italic=True)
    add_run(p_p3_q3, " và đi qua điểm ")
    add_run(p_p3_q3, "A(2; -1; 4)", italic=True)
    add_run(p_p3_q3, ". Tính bán kính R của mặt cầu (S).")
    p_ans_q3 = doc.add_paragraph()
    p_ans_q3.paragraph_format.space_before = Pt(1)
    p_ans_q3.paragraph_format.space_after = Pt(3)
    add_run(p_ans_q3, "Đáp án: ", bold=True, is_red=True)
    add_run(p_ans_q3, "3", bold=True, is_red=True)

    # ==================== PHẦN IV: TỰ LUẬN (IN ĐẬM ĐÁP ÁN ĐỎ) ====================
    p_p4 = doc.add_paragraph()
    p_p4.paragraph_format.space_before = Pt(12)
    p_p4.paragraph_format.space_after = Pt(4)
    add_run(p_p4, "PHẦN IV. Câu tự luận.", bold=True, size=Pt(12.5))
    p_p4_note = doc.add_paragraph()
    p_p4_note.paragraph_format.space_after = Pt(6)
    add_run(p_p4_note, "Thí sinh trình bày chi tiết lời giải vào giấy làm bài. (Hướng dẫn chấm được in đậm màu đỏ)", italic=True)
    
    # Q1: Khối chóp không gian Oxyz
    p_p4_q1 = doc.add_paragraph()
    p_p4_q1.paragraph_format.space_before = Pt(3)
    p_p4_q1.paragraph_format.space_after = Pt(2)
    add_run(p_p4_q1, "Câu 1 (1,5 điểm): ", bold=True)
    add_run(p_p4_q1, "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, cạnh bên SA vuông góc với mặt phẳng đáy và SA = a√3. Tính theo a thể tích khối chóp S.ABCD.")
    p_p4_q1_gd = doc.add_paragraph()
    p_p4_q1_gd.paragraph_format.space_before = Pt(1)
    p_p4_q1_gd.paragraph_format.space_after = Pt(3)
    add_run(p_p4_q1_gd, "Hướng dẫn chấm:\n", bold=True, is_red=True)
    add_run(p_p4_q1_gd, "• Diện tích đáy hình vuông: S_ABCD = a² (0,5 điểm).\n", is_red=True)
    add_run(p_p4_q1_gd, "• Chiều cao hình chóp: h = SA = a√3 (0,5 điểm).\n", is_red=True)
    add_run(p_p4_q1_gd, "• Thể tích: V = (1/3) * S_ABCD * h = (a³√3)/3 (0,5 điểm).", bold=True, is_red=True)

    # Q2: Ứng dụng tích phân tính quãng đường
    p_p4_q2 = doc.add_paragraph()
    p_p4_q2.paragraph_format.space_before = Pt(3)
    p_p4_q2.paragraph_format.space_after = Pt(2)
    add_run(p_p4_q2, "Câu 2 (1,0 điểm): ", bold=True)
    add_run(p_p4_q2, "Một ô tô đang chạy với vận tốc v₀ = 10 m/s thì người lái xe đạp phanh; từ thời điểm đó ô tô chuyển động chậm dần đều với gia tốc a(t) = -2t (m/s²). Tính quãng đường s ô tô di chuyển được từ lúc đạp phanh đến khi dừng hẳn.")
    p_p4_q2_gd = doc.add_paragraph()
    p_p4_q2_gd.paragraph_format.space_before = Pt(1)
    p_p4_q2_gd.paragraph_format.space_after = Pt(3)
    add_run(p_p4_q2_gd, "Hướng dẫn chấm:\n", bold=True, is_red=True)
    add_run(p_p4_q2_gd, "• Vận tốc v(t) = 10 - t² (m/s). Xe dừng lại khi v(t) = 0 <=> t = √10 (s) (0,5 điểm).\n", is_red=True)
    add_run(p_p4_q2_gd, "• Quãng đường: s = ∫(10 - t²)dt từ 0 đến √10 = (20√10)/3 ≈ 21,08 mét (0,5 điểm).", bold=True, is_red=True)

    # Student exam footer
    p_end = doc.add_paragraph()
    p_end.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_end.paragraph_format.space_before = Pt(16)
    p_end.paragraph_format.space_after = Pt(2)
    add_run(p_end, "------------------ HẾT ------------------", bold=True)
    
    p_note = doc.add_paragraph()
    p_note.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_note.paragraph_format.space_before = Pt(2)
    p_note.paragraph_format.space_after = Pt(6)
    add_run(p_note, "• Thí sinh không được sử dụng tài liệu. Cán bộ coi thi không giải thích gì thêm.", italic=True, size=Pt(10))

    # ==================== PAGE BREAK ====================
    doc.add_page_break()

    # ==================== BẢNG ĐÁP ÁN VÀ HƯỚNG DẪN CHẤM (RIÊNG BIỆT) ====================
    p_ans_head = doc.add_paragraph()
    p_ans_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ans_head.paragraph_format.space_before = Pt(10)
    p_ans_head.paragraph_format.space_after = Pt(2)
    r_ah1 = add_run(p_ans_head, "BẢNG ĐÁP ÁN VÀ HƯỚNG DẪN CHẤM ĐỀ KIỂM TRA MẪU\n", bold=True, size=Pt(15))
    r_ah1.font.color.rgb = BLUE_COLOR
    r_ah2 = add_run(p_ans_head, "MÔN: TOÁN (LỚP 12) - MÃ ĐỀ: 000", bold=True, size=Pt(12))

    # --- BẢNG ĐÁP ÁN PHẦN I ---
    p_t1 = doc.add_paragraph()
    p_t1.paragraph_format.space_before = Pt(12)
    p_t1.paragraph_format.space_after = Pt(4)
    add_run(p_t1, "I. BẢNG ĐÁP ÁN PHẦN I (TRẮC NGHIỆM 4 LỰA CHỌN)", bold=True, size=Pt(12))

    tbl_p1 = doc.add_table(rows=2, cols=7)
    tbl_p1.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_p1.style = 'Table Grid'

    hdr_cells_p1 = tbl_p1.rows[0].cells
    hdr_cells_p1[0].paragraphs[0].add_run("Câu")
    format_cell(hdr_cells_p1[0], bg_hex="1E40AF", bold=True)
    hdr_cells_p1[0].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)

    ans_p1 = ["B", "B", "B", "B", "A", "A"]
    for idx, ans_val in enumerate(ans_p1, start=1):
        hdr_cells_p1[idx].paragraphs[0].add_run(str(idx))
        format_cell(hdr_cells_p1[idx], bg_hex="1E40AF", bold=True)
        hdr_cells_p1[idx].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)

    ans_row_cells = tbl_p1.rows[1].cells
    ans_row_cells[0].paragraphs[0].add_run("Chọn")
    format_cell(ans_row_cells[0], bg_hex="F9FAFB", bold=True)
    for idx, ans_val in enumerate(ans_p1, start=1):
        ans_row_cells[idx].paragraphs[0].add_run(ans_val)
        format_cell(ans_row_cells[idx], bg_hex="F9FAFB", bold=True)
        ans_row_cells[idx].paragraphs[0].runs[0].font.color.rgb = RED_COLOR

    # --- BẢNG ĐÁP ÁN PHẦN II ---
    p_t2 = doc.add_paragraph()
    p_t2.paragraph_format.space_before = Pt(14)
    p_t2.paragraph_format.space_after = Pt(4)
    add_run(p_t2, "II. BẢNG ĐÁP ÁN PHẦN II (TRẮC NGHIỆM ĐÚNG / SAI)", bold=True, size=Pt(12))

    p2_data = [
        ("1", "a", "Đ"), ("1", "b", "Đ"), ("1", "c", "S"), ("1", "d", "S"),
        ("2", "a", "Đ"), ("2", "b", "Đ"), ("2", "c", "S"), ("2", "d", "S")
    ]
    tbl_p2 = doc.add_table(rows=1 + len(p2_data), cols=3)
    tbl_p2.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_p2.style = 'Table Grid'

    hdr2 = tbl_p2.rows[0].cells
    hdr2[0].paragraphs[0].add_run("Câu")
    format_cell(hdr2[0], bg_hex="047857", bold=True)
    hdr2[0].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)

    hdr2[1].paragraphs[0].add_run("Lệnh hỏi")
    format_cell(hdr2[1], bg_hex="047857", bold=True)
    hdr2[1].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)

    hdr2[2].paragraphs[0].add_run("Đáp án")
    format_cell(hdr2[2], bg_hex="047857", bold=True)
    hdr2[2].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)

    for r_i, (q_n, itm, tf) in enumerate(p2_data, start=1):
        row = tbl_p2.rows[r_i].cells
        bg = "F0FDF4" if r_i % 2 == 0 else "FFFFFF"
        row[0].paragraphs[0].add_run(f"Câu {q_n}")
        format_cell(row[0], bg_hex=bg, bold=True)
        row[1].paragraphs[0].add_run(f"Ý {itm})")
        format_cell(row[1], bg_hex=bg, bold=True)
        row[2].paragraphs[0].add_run(tf)
        format_cell(row[2], bg_hex=bg, bold=True)
        if tf == "Đ":
            row[2].paragraphs[0].runs[0].font.color.rgb = RGBColor(4, 120, 87)
        else:
            row[2].paragraphs[0].runs[0].font.color.rgb = RED_COLOR

    # --- BẢNG ĐÁP ÁN PHẦN III ---
    p_t3 = doc.add_paragraph()
    p_t3.paragraph_format.space_before = Pt(14)
    p_t3.paragraph_format.space_after = Pt(4)
    add_run(p_t3, "III. BẢNG ĐÁP ÁN PHẦN III (TRẢ LỜI NGẮN)", bold=True, size=Pt(12))

    p3_data = [("1", "9"), ("2", "12"), ("3", "3")]
    tbl_p3 = doc.add_table(rows=1 + len(p3_data), cols=2)
    tbl_p3.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_p3.style = 'Table Grid'

    hdr3 = tbl_p3.rows[0].cells
    hdr3[0].paragraphs[0].add_run("Câu hỏi")
    format_cell(hdr3[0], bg_hex="B45309", bold=True)
    hdr3[0].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
    hdr3[1].paragraphs[0].add_run("Đáp án")
    format_cell(hdr3[1], bg_hex="B45309", bold=True)
    hdr3[1].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)

    for r_i, (q_n, ans) in enumerate(p3_data, start=1):
        row = tbl_p3.rows[r_i].cells
        bg = "FFFBEB" if r_i % 2 == 0 else "FFFFFF"
        row[0].paragraphs[0].add_run(f"Câu {q_n}")
        format_cell(row[0], bg_hex=bg, bold=True)
        row[1].paragraphs[0].add_run(ans)
        format_cell(row[1], bg_hex=bg, bold=True)
        row[1].paragraphs[0].runs[0].font.color.rgb = RED_COLOR

    # --- HƯỚNG DẪN CHẤM PHẦN IV ---
    p_t4 = doc.add_paragraph()
    p_t4.paragraph_format.space_before = Pt(14)
    p_t4.paragraph_format.space_after = Pt(4)
    add_run(p_t4, "IV. HƯỚNG DẪN CHẤM PHẦN IV (TỰ LUẬN)", bold=True, size=Pt(12))

    p4_1 = doc.add_paragraph()
    p4_1.paragraph_format.space_before = Pt(3)
    p4_1.paragraph_format.space_after = Pt(2)
    add_run(p4_1, "Câu 1 (1,5 điểm): ", bold=True)
    add_run(p4_1, "Cho hình chóp S.ABCD đáy hình vuông cạnh a, SA ⊥ (ABCD) và SA = a√3. Thể tích V khối chóp:")
    p4_1_sub = doc.add_paragraph()
    p4_1_sub.paragraph_format.space_before = Pt(1)
    p4_1_sub.paragraph_format.space_after = Pt(2)
    add_run(p4_1_sub, "• Diện tích đáy hình vuông: S_ABCD = a² (0,5 điểm).\n")
    add_run(p4_1_sub, "• Chiều cao hình chóp: h = SA = a√3 (0,5 điểm).\n")
    add_run(p4_1_sub, "• Thể tích: V = (1/3) * S_ABCD * h = (a³√3)/3 (0,5 điểm).", is_red=True)

    p4_2 = doc.add_paragraph()
    p4_2.paragraph_format.space_before = Pt(3)
    p4_2.paragraph_format.space_after = Pt(2)
    add_run(p4_2, "Câu 2 (1,0 điểm): ", bold=True)
    add_run(p4_2, "Ô tô v₀ = 10 m/s đạp phanh với gia tốc a(t) = -2t (m/s²). Quãng đường s ô tô di chuyển đến khi dừng hẳn:")
    p4_2_sub = doc.add_paragraph()
    p4_2_sub.paragraph_format.space_before = Pt(1)
    p4_2_sub.paragraph_format.space_after = Pt(2)
    add_run(p4_2_sub, "• Vận tốc v(t) = 10 - t² (m/s). Xe dừng lại khi v(t) = 0 <=> t = √10 (s) (0,5 điểm).\n")
    add_run(p4_2_sub, "• Quãng đường: s = ∫(10 - t²)dt từ 0 đến √10 = (20√10)/3 ≈ 21,08 mét (0,5 điểm).", is_red=True)

    doc.save(output_path)
    print(f"Standard Math 12 Sample DOCX created at: {output_path}")

def get_unicode_font_paths():
    """Find available TrueType fonts supporting Vietnamese diacritics across Windows and Linux."""
    candidates_reg = [
        "C:/Windows/Fonts/times.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    candidates_bold = [
        "C:/Windows/Fonts/timesbd.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    reg_path = next((p for p in candidates_reg if os.path.exists(p)), None)
    bold_path = next((p for p in candidates_bold if os.path.exists(p)), reg_path)
    return reg_path, bold_path

def create_sample_pdf_from_docx(docx_path="samples/de_thi_mau_chuan.docx", pdf_path="samples/de_thi_mau_chuan.pdf"):
    """
    Generate matching Math 12 sample PDF with PyMuPDF.
    Page 1: Student exam (clean, 2 choices per line).
    Page 2: Answer key table and grading rubric.
    Embeds TrueType fonts (CID Type0) for flawless Vietnamese rendering in all PDF viewers.
    """
    import pymupdf
    doc_pdf = pymupdf.open()
    
    font_reg_path, font_bold_path = get_unicode_font_paths()
    fn_reg = "F_REG" if font_reg_path else "helv"
    fn_bold = "F_BOLD" if font_bold_path else "helv"
    
    c_black = (0, 0, 0)
    c_red = (0.86, 0.15, 0.15)
    c_blue = (0.1, 0.3, 0.6)
    c_gray = (0.4, 0.4, 0.4)
    
    # ---------------- PAGE 1: EXAM WITH BOLD RED ANSWERS ----------------
    page1 = doc_pdf.new_page(width=595, height=842)
    if font_reg_path:
        page1.insert_font(fontname=fn_reg, fontfile=font_reg_path)
    if font_bold_path:
        page1.insert_font(fontname=fn_bold, fontfile=font_bold_path)

    page1.insert_text((40, 32), "SỞ GIÁO DỤC VÀ ĐÀO TẠO              KỲ THI THỬ TỐT NGHIỆP THPT NĂM HỌC 2026 - 2027", fontsize=9, fontname=fn_bold, color=c_black)
    page1.insert_text((40, 45), "TRƯỜNG THPT LONG CANG               BÀI THI: TOÁN (LỚP 12) - ĐỀ MẪU CÓ ĐÁP ÁN ĐỎ", fontsize=9, fontname=fn_bold, color=c_blue)
    page1.draw_line((40, 52), (555, 52), color=c_gray, width=0.7)
    
    y = 65
    page1.insert_text((40, y), "Họ và tên thí sinh: .....................................................................     Lớp: .......................   MÃ ĐỀ: 000", fontsize=9, fontname=fn_reg, color=c_black)
    y += 16
    
    # PHẦN I
    page1.insert_text((40, y), "PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn (Đáp án đúng in đậm màu đỏ)", fontsize=9.5, fontname=fn_bold, color=c_black)
    y += 13
    page1.insert_text((40, y), "Câu 1: Hàm số y = f(x) có f'(x) = x(x - 2)(x + 1). Hàm số đồng biến trên khoảng nào?", fontsize=8.5, fontname=fn_reg, color=c_black)
    y += 11
    page1.insert_text((55, y), "A. (-1; 0).", fontsize=8.5, fontname=fn_bold, color=c_black)
    page1.insert_text((300, y), "B. (2; +∞).", fontsize=8.5, fontname=fn_bold, color=c_red)
    y += 11
    page1.insert_text((55, y), "C. (0; 2).", fontsize=8.5, fontname=fn_bold, color=c_black)
    page1.insert_text((300, y), "D. (-∞; -1).", fontsize=8.5, fontname=fn_bold, color=c_black)
    y += 14
    
    page1.insert_text((40, y), "Câu 2: Đồ thị hàm số y = (2x - 1)/(x + 1) có đường tiệm cận đứng là:", fontsize=8.5, fontname=fn_reg, color=c_black)
    y += 11
    page1.insert_text((55, y), "A. x = 2.", fontsize=8.5, fontname=fn_bold, color=c_black)
    page1.insert_text((300, y), "B. x = -1.", fontsize=8.5, fontname=fn_bold, color=c_red)
    y += 11
    page1.insert_text((55, y), "C. y = 2.", fontsize=8.5, fontname=fn_bold, color=c_black)
    page1.insert_text((300, y), "D. y = -1.", fontsize=8.5, fontname=fn_bold, color=c_black)
    y += 14

    page1.insert_text((40, y), "Câu 3: Điểm cực đại của đồ thị hàm số y = x³ - 3x + 2 là:", fontsize=8.5, fontname=fn_reg, color=c_black)
    y += 11
    page1.insert_text((55, y), "A. M(1; 0).", fontsize=8.5, fontname=fn_bold, color=c_black)
    page1.insert_text((300, y), "B. N(-1; 4).", fontsize=8.5, fontname=fn_bold, color=c_red)
    y += 11
    page1.insert_text((55, y), "C. P(0; 2).", fontsize=8.5, fontname=fn_bold, color=c_black)
    page1.insert_text((300, y), "D. Q(2; 4).", fontsize=8.5, fontname=fn_bold, color=c_black)
    y += 14

    page1.insert_text((40, y), "Câu 4: Họ nguyên hàm của hàm số f(x) = 3x² + cos x là:", fontsize=8.5, fontname=fn_reg, color=c_black)
    y += 11
    page1.insert_text((55, y), "A. F(x) = x³ - sin x + C.", fontsize=8.5, fontname=fn_bold, color=c_black)
    page1.insert_text((300, y), "B. F(x) = x³ + sin x + C.", fontsize=8.5, fontname=fn_bold, color=c_red)
    y += 11
    page1.insert_text((55, y), "C. F(x) = 6x + sin x + C.", fontsize=8.5, fontname=fn_bold, color=c_black)
    page1.insert_text((300, y), "D. F(x) = x³ + cos x + C.", fontsize=8.5, fontname=fn_bold, color=c_black)
    y += 14

    page1.insert_text((40, y), "Câu 5: Mặt cầu (S): (x - 1)² + (y + 2)² + (z - 3)² = 16 có tâm I và bán kính R là:", fontsize=8.5, fontname=fn_reg, color=c_black)
    y += 11
    page1.insert_text((55, y), "A. I(1; -2; 3), R = 4.", fontsize=8.5, fontname=fn_bold, color=c_red)
    page1.insert_text((300, y), "B. I(-1; 2; -3), R = 4.", fontsize=8.5, fontname=fn_bold, color=c_black)
    y += 11
    page1.insert_text((55, y), "C. I(1; -2; 3), R = 16.", fontsize=8.5, fontname=fn_bold, color=c_black)
    page1.insert_text((300, y), "D. I(-1; 2; -3), R = 16.", fontsize=8.5, fontname=fn_bold, color=c_black)
    y += 14

    page1.insert_text((40, y), "Câu 6: Trong không gian Oxyz, cho vectơ a = (1; 2; -1) và vectơ b = (2; 0; 1). Tọa độ vectơ u = a + 2b là:", fontsize=8.5, fontname=fn_reg, color=c_black)
    y += 11
    page1.insert_text((55, y), "A. u = (5; 2; 1).", fontsize=8.5, fontname=fn_bold, color=c_red)
    page1.insert_text((300, y), "B. u = (3; 2; 0).", fontsize=8.5, fontname=fn_bold, color=c_black)
    y += 11
    page1.insert_text((55, y), "C. u = (5; 4; 1).", fontsize=8.5, fontname=fn_bold, color=c_black)
    page1.insert_text((300, y), "D. u = (4; 2; -1).", fontsize=8.5, fontname=fn_bold, color=c_black)
    y += 16

    # PHẦN II
    page1.insert_text((40, y), "PHẦN II. Câu trắc nghiệm đúng sai (Ý Đúng/Sai in đậm màu đỏ)", fontsize=9.5, fontname=fn_bold, color=c_black)
    y += 13
    page1.insert_text((40, y), "Câu 1: Cho hàm tổng chi phí C(x) = x³ - 30x² + 400x + 500 (nghìn đồng) với 0 ≤ x ≤ 25:", fontsize=8.5, fontname=fn_reg, color=c_black)
    y += 10
    page1.insert_text((55, y), "a) Chi phí cố định khi x = 0 là 500 nghìn đồng. (Đúng)", fontsize=8.5, fontname=fn_bold, color=c_red)
    y += 10
    page1.insert_text((55, y), "b) Chi phí biên tại mức sản lượng x = 10 là C'(10) = 100 nghìn đồng. (Đúng)", fontsize=8.5, fontname=fn_bold, color=c_red)
    y += 10
    page1.insert_text((55, y), "c) Chi phí trung bình luôn giảm khi sản lượng tăng từ 0 đến 25. (Sai)", fontsize=8.5, fontname=fn_bold, color=c_red)
    y += 10
    page1.insert_text((55, y), "d) Tổng chi phí sản xuất nhỏ nhất khi x = 20 sản phẩm. (Sai)", fontsize=8.5, fontname=fn_bold, color=c_red)
    y += 13

    page1.insert_text((40, y), "Câu 2: Trong không gian Oxyz, cho A(1; 0; 2), B(-1; 1; 3), C(3; 2; 1) và (P): 2x - y + 2z - 5 = 0:", fontsize=8.5, fontname=fn_reg, color=c_black)
    y += 10
    page1.insert_text((55, y), "a) Trọng tâm G của tam giác ABC là G(1; 1; 2). (Đúng)", fontsize=8.5, fontname=fn_bold, color=c_red)
    y += 10
    page1.insert_text((55, y), "b) Mặt phẳng (P) có vectơ pháp tuyến n = (2; -1; 2). (Đúng)", fontsize=8.5, fontname=fn_bold, color=c_red)
    y += 10
    page1.insert_text((55, y), "c) Điểm A(1; 0; 2) nằm trên mặt phẳng (P). (Sai)", fontsize=8.5, fontname=fn_bold, color=c_red)
    y += 10
    page1.insert_text((55, y), "d) Khoảng cách từ O đến mặt phẳng (P) bằng 1. (Sai)", fontsize=8.5, fontname=fn_bold, color=c_red)
    y += 15

    # PHẦN III
    page1.insert_text((40, y), "PHẦN III. Câu trắc nghiệm trả lời ngắn (Đáp án in đậm màu đỏ)", fontsize=9.5, fontname=fn_bold, color=c_black)
    y += 12
    page1.insert_text((40, y), "Câu 1: Tìm giá trị lớn nhất của hàm số y = -x² + 4x + 5 trên [0; 3].", fontsize=8.5, fontname=fn_reg, color=c_black)
    page1.insert_text((370, y), "Đáp án: 9", fontsize=8.5, fontname=fn_bold, color=c_red)
    y += 12
    page1.insert_text((40, y), "Câu 2: Tính tích phân I = ∫(2x + 1)dx từ 0 đến 3.", fontsize=8.5, fontname=fn_reg, color=c_black)
    page1.insert_text((370, y), "Đáp án: 12", fontsize=8.5, fontname=fn_bold, color=c_red)
    y += 12
    page1.insert_text((40, y), "Câu 3: Mặt cầu (S) tâm I(1; 1; 2) đi qua A(2; -1; 4) có bán kính R bằng bao nhiêu?", fontsize=8.5, fontname=fn_reg, color=c_black)
    page1.insert_text((370, y), "Đáp án: 3", fontsize=8.5, fontname=fn_bold, color=c_red)
    y += 15

    # PHẦN IV
    page1.insert_text((40, y), "PHẦN IV. Câu tự luận (Hướng dẫn chấm in đậm màu đỏ)", fontsize=9.5, fontname=fn_bold, color=c_black)
    y += 12
    page1.insert_text((40, y), "Câu 1 (1,5 điểm): Cho hình chóp S.ABCD có đáy là hình vuông cạnh a, SA vuông góc với (ABCD) và SA = a√3. Tính theo a thể tích V.", fontsize=8.5, fontname=fn_reg, color=c_black)
    y += 10
    page1.insert_text((55, y), "Hướng dẫn chấm: V = (1/3) * a² * a√3 = (a³√3)/3 (1,5 điểm)", fontsize=8.5, fontname=fn_bold, color=c_red)
    y += 12
    page1.insert_text((40, y), "Câu 2 (1,0 điểm): Một ô tô chạy v₀ = 10 m/s đạp phanh với a(t) = -2t (m/s²). Tính quãng đường đến khi dừng hẳn.", fontsize=8.5, fontname=fn_reg, color=c_black)
    y += 10
    page1.insert_text((55, y), "Hướng dẫn chấm: Dừng khi v(t) = 0 <=> t = √10; s = ∫(10 - t²)dt = (20√10)/3 ≈ 21,08 mét (1,0 điểm)", fontsize=8.5, fontname=fn_bold, color=c_red)
    y += 16
    page1.insert_text((220, y), "------------------ HẾT ------------------", fontsize=8.5, fontname=fn_bold, color=c_black)

    # ---------------- PAGE 2: SEPARATE ANSWER KEY ----------------
    page2 = doc_pdf.new_page(width=595, height=842)
    if font_reg_path:
        page2.insert_font(fontname=fn_reg, fontfile=font_reg_path)
    if font_bold_path:
        page2.insert_font(fontname=fn_bold, fontfile=font_bold_path)

    page2.insert_text((130, 45), "BẢNG ĐÁP ÁN VÀ HƯỚNG DẪN CHẤM ĐỀ THI MẪU", fontsize=12, fontname=fn_bold, color=c_blue)
    page2.insert_text((180, 62), "MÔN: TOÁN (LỚP 12) - MÃ ĐỀ: 000", fontsize=10, fontname=fn_bold, color=c_black)
    page2.draw_line((40, 75), (555, 75), color=c_gray, width=0.7)

    y2 = 95
    page2.insert_text((40, y2), "I. BẢNG ĐÁP ÁN PHẦN I (TRẮC NGHIỆM 4 LỰA CHỌN)", fontsize=10, fontname=fn_bold, color=c_black)
    y2 += 16
    page2.insert_text((55, y2), "Câu 1: B       Câu 2: B       Câu 3: B       Câu 4: B       Câu 5: A       Câu 6: A", fontsize=10, fontname=fn_bold, color=c_red)
    y2 += 25

    page2.insert_text((40, y2), "II. BẢNG ĐÁP ÁN PHẦN II (TRẮC NGHIỆM ĐÚNG / SAI)", fontsize=10, fontname=fn_bold, color=c_black)
    y2 += 16
    page2.insert_text((55, y2), "Câu 1:   a) Đúng   |   b) Đúng   |   c) Sai   |   d) Sai", fontsize=9.5, fontname=fn_bold, color=c_black)
    y2 += 14
    page2.insert_text((55, y2), "Câu 2:   a) Đúng   |   b) Đúng   |   c) Sai   |   d) Sai", fontsize=9.5, fontname=fn_bold, color=c_black)
    y2 += 25

    page2.insert_text((40, y2), "III. BẢNG ĐÁP ÁN PHẦN III (TRẢ LỜI NGẮN)", fontsize=10, fontname=fn_bold, color=c_black)
    y2 += 16
    page2.insert_text((55, y2), "Câu 1: 9                Câu 2: 12                Câu 3: 3", fontsize=10, fontname=fn_bold, color=c_red)
    y2 += 25

    page2.insert_text((40, y2), "IV. HƯỚNG DẪN CHẤM PHẦN IV (TỰ LUẬN)", fontsize=10, fontname=fn_bold, color=c_black)
    y2 += 16
    page2.insert_text((40, y2), "Câu 1 (1,5 điểm):", fontsize=9.5, fontname=fn_bold, color=c_black)
    y2 += 13
    page2.insert_text((55, y2), "• Diện tích đáy: S_ABCD = a² (0,5 điểm). Chiều cao: SA = a√3 (0,5 điểm).", fontsize=9, fontname=fn_reg, color=c_black)
    y2 += 12
    page2.insert_text((55, y2), "• Thể tích: V = (1/3) * a² * a√3 = (a³√3)/3 (0,5 điểm).", fontsize=9, fontname=fn_bold, color=c_red)
    y2 += 18

    page2.insert_text((40, y2), "Câu 2 (1,0 điểm):", fontsize=9.5, fontname=fn_bold, color=c_black)
    y2 += 13
    page2.insert_text((55, y2), "• v(t) = 10 - t² (m/s). Xe dừng khi v(t) = 0 <=> t = √10 (s) (0,5 điểm).", fontsize=9, fontname=fn_reg, color=c_black)
    y2 += 12
    page2.insert_text((55, y2), "• s = ∫(10 - t²)dt từ 0 đến √10 = (20√10)/3 ≈ 21,08 mét (0,5 điểm).", fontsize=9, fontname=fn_bold, color=c_red)

    doc_pdf.save(pdf_path)
    doc_pdf.close()
    print(f"Standard Math 12 Sample PDF created at: {pdf_path}")

if __name__ == "__main__":
    create_sample_docx()
    create_sample_pdf_from_docx()
