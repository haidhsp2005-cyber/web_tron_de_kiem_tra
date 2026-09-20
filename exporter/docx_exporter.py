import os
import re
import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import qn, nsdecls
from parser.formula_helper import (
    deserialize_oxml_elements, 
    strip_red_from_element, 
    set_red_on_element,
    strip_bold_from_element,
    heal_omath_element
)

RED_COLOR = RGBColor(220, 38, 38)
BLUE_COLOR = RGBColor(30, 64, 175)
GRAY_COLOR = RGBColor(107, 114, 128)

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

class DocxExporter:
    def __init__(self, shuffled_result: dict, output_dir: str = "exports"):
        self.result = shuffled_result
        self.metadata = shuffled_result.get("metadata", {})
        self.variants = shuffled_result.get("variants", [])
        self.summary = shuffled_result.get("summary", {})
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def export_all(self) -> dict:
        """
        Exports:
        1. Test files for each variant (without answers revealed)
        2. Detailed answer keys for each variant (answers in red)
        3. Comprehensive summary answer table docx
        """
        test_files = []
        key_files = []
        
        for variant in self.variants:
            code = variant["code"]
            # 1. Exam paper (student)
            test_path = os.path.join(self.output_dir, f"De_thi_{code}.docx")
            self._generate_exam_docx(variant, test_path, is_answer_key=False)
            test_files.append(test_path)
            
            # 2. Detailed answer paper
            key_path = os.path.join(self.output_dir, f"Dap_an_chi_tiet_{code}.docx")
            self._generate_exam_docx(variant, key_path, is_answer_key=True)
            key_files.append(key_path)

        # 3. Summary answers DOCX
        summary_path = os.path.join(self.output_dir, "Bang_dap_an_tong_hop.docx")
        self._generate_summary_docx(summary_path)

        return {
            "test_files": test_files,
            "key_files": key_files,
            "summary_file": summary_path
        }

    def _parse_agency_and_school(self, school_str: str) -> tuple[str, str]:
        """
        Parses agency and school cleanly from metadata string to avoid duplicate
        'SỞ GIÁO DỤC VÀ ĐÀO TẠO' headers.
        """
        raw = school_str.strip() if school_str else "TRƯỜNG THPT LONG CANG"
        agency = "SỞ GIÁO DỤC VÀ ĐÀO TẠO"
        school = raw

        if " - " in raw:
            parts = [p.strip() for p in raw.split(" - ") if p.strip()]
            if len(parts) >= 2:
                if any(k in parts[0].upper() for k in ["SỞ", "PHÒNG", "BỘ"]):
                    agency = parts[0]
                    school = " - ".join(parts[1:])
                else:
                    agency = parts[0]
                    school = parts[1]
        elif "\n" in raw:
            lines = [l.strip() for l in raw.split("\n") if l.strip()]
            if len(lines) >= 2:
                agency = lines[0]
                school = lines[1]
        elif re.search(r"^(SỞ\s+GD[^\s]*\s+[^\-]+?)\s+(TRƯỜNG.*)$", raw, re.IGNORECASE):
            m = re.search(r"^(SỞ\s+GD[^\s]*\s+[^\-]+?)\s+(TRƯỜNG.*)$", raw, re.IGNORECASE)
            agency = m.group(1).strip()
            school = m.group(2).strip()
        elif raw.upper().startswith("SỞ ") or raw.upper().startswith("PHÒNG ") or raw.upper().startswith("BỘ "):
            agency = raw
            school = ""

        return agency, school

    def _setup_footer(self, doc, code: str, title_prefix: str = "Mã đề thi"):
        """Sets up exam footer: left = {title_prefix}: {code}, right = Trang {PAGE}/{NUMPAGES} across all pages."""
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

            left_text = f"{title_prefix}: {code}" if code else title_prefix
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

    def _generate_exam_docx(self, variant: dict, file_path: str, is_answer_key: bool = False):
        doc = docx.Document()
        for sec in doc.sections:
            sec.top_margin = Inches(0.70)
            sec.bottom_margin = Inches(0.70)
            sec.left_margin = Inches(0.70)
            sec.right_margin = Inches(0.70)

        style = doc.styles['Normal']
        font = style.font
        font.name = 'Times New Roman'
        font.size = Pt(12)
        style.paragraph_format.line_spacing = 1.15

        code = variant["code"]
        self._setup_footer(doc, code)

        school = self.metadata.get("school") or "THPT Long Cang"
        subject = self.metadata.get("subject") or "Toán"
        time_str = self.metadata.get("time") or "90 phút"
        year = self.metadata.get("year") or "2026 - 2027"

        # 1. Header Table (1 row, 2 cols, no borders) - Total width 6.70" (A4 width 8.27" - 1.40" = 6.87" printable)
        tbl = doc.add_table(rows=1, cols=2)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.autofit = False
        set_table_no_borders(tbl)

        # Left Column (Agency + School + School Year)
        c0 = tbl.cell(0, 0)
        c0.width = Inches(3.1)
        p0 = c0.paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p0.paragraph_format.space_before = Pt(0)
        p0.paragraph_format.space_after = Pt(1)
        p0.paragraph_format.line_spacing = 1.15

        agency, school_clean = self._parse_agency_and_school(school)
        if agency:
            r_agency = p0.add_run(f"{agency.upper()}\n")
            r_agency.font.name = "Times New Roman"
            r_agency.font.size = Pt(10)
            r_agency.bold = True
        
        if school_clean:
            r_sch = p0.add_run(f"{school_clean.upper()}\n")
            r_sch.font.name = "Times New Roman"
            r_sch.font.size = Pt(11)
            r_sch.bold = True
        
        r_yr = p0.add_run(f"NĂM HỌC {year}")
        r_yr.font.name = "Times New Roman"
        r_yr.font.size = Pt(10)
        r_yr.bold = True

        # Right Column (Exam title + Subject + Time)
        c1 = tbl.cell(0, 1)
        c1.width = Inches(3.6)
        p1 = c1.paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p1.paragraph_format.space_before = Pt(0)
        p1.paragraph_format.space_after = Pt(1)
        p1.paragraph_format.line_spacing = 1.15
        
        title_prefix = "HƯỚNG DẪN CHẤM & ĐÁP ÁN CHI TIẾT" if is_answer_key else "ĐỀ KIỂM TRA CHÍNH THỨC"
        r_tit = p1.add_run(f"{title_prefix}\n")
        r_tit.font.name = "Times New Roman"
        r_tit.font.size = Pt(11)
        r_tit.bold = True
        if is_answer_key:
            r_tit.font.color.rgb = RED_COLOR
            
        r_sub = p1.add_run(f"MÔN: {subject.upper()}\n")
        r_sub.font.name = "Times New Roman"
        r_sub.font.size = Pt(12)
        r_sub.bold = True
        
        r_time = p1.add_run(f"Thời gian làm bài: {time_str} (không kể thời gian phát đề)\n")
        r_time.font.name = "Times New Roman"
        r_time.font.size = Pt(10)
        r_time.italic = True

        r_code = p1.add_run(f"MÃ ĐỀ THI: {code}")
        r_code.font.name = "Times New Roman"
        r_code.font.size = Pt(11.5)
        r_code.bold = True
        if is_answer_key:
            r_code.font.color.rgb = RED_COLOR

        # 2. Student Info Section (Clean 2-line layout matching official exam template)
        if not is_answer_key:
            p_info1 = doc.add_paragraph()
            p_info1.paragraph_format.space_before = Pt(8)
            p_info1.paragraph_format.space_after = Pt(2)
            p_info1.paragraph_format.line_spacing = 1.15
            r1 = p_info1.add_run("Họ và tên thí sinh: .................................................... Lớp: .....................")
            r1.font.name = "Times New Roman"
            r1.font.size = Pt(11)

            p_info2 = doc.add_paragraph()
            p_info2.paragraph_format.space_before = Pt(2)
            p_info2.paragraph_format.space_after = Pt(8)
            p_info2.paragraph_format.line_spacing = 1.15
            r2 = p_info2.add_run("Số báo danh: ....................................................")
            r2.font.name = "Times New Roman"
            r2.font.size = Pt(11)
        else:
            p_key_note = doc.add_paragraph()
            p_key_note.paragraph_format.space_before = Pt(6)
            p_key_note.paragraph_format.space_after = Pt(8)
            r_kn = p_key_note.add_run("BẢN ĐÁP ÁN CHI TIẾT DÀNH CHO GIÁO VIÊN (KHÔNG PHÁT CHO HỌC SINH)")
            r_kn.font.name = "Times New Roman"
            r_kn.font.size = Pt(10)
            r_kn.bold = True
            r_kn.font.color.rgb = RED_COLOR

        # ----------------- PHẦN I -----------------
        if variant.get("part1"):
            p_head = doc.add_paragraph()
            p_head.paragraph_format.space_before = Pt(8)
            p_head.paragraph_format.space_after = Pt(2)
            p_head.paragraph_format.keep_with_next = True
            r = p_head.add_run("PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn.")
            r.bold = True
            r.font.size = Pt(12.5)

            p_sub = doc.add_paragraph()
            p_sub.paragraph_format.space_after = Pt(6)
            r = p_sub.add_run("Thí sinh trả lời từ câu 1 đến câu {}. Mỗi câu hỏi thí sinh chỉ chọn một phương án.".format(len(variant["part1"])))
            r.italic = True

            for q in variant["part1"]:
                p_q = doc.add_paragraph()
                p_q.paragraph_format.space_before = Pt(5)
                p_q.paragraph_format.space_after = Pt(2)
                p_q.paragraph_format.line_spacing = 1.15
                p_q.paragraph_format.keep_with_next = True
                r_num = p_q.add_run(f"Câu {q['num']}: ")
                r_num.bold = True
                
                self._append_elements_or_text(
                    p_q, 
                    q.get("xml_strings", []), 
                    q["question"], 
                    is_red=False, 
                    strip_red=not is_answer_key,
                    strip_bold=not is_answer_key
                )

                # Choices layout:
                # Standard format for Math exams: 2 choices per line (2x2 borderless table: A & B on line 1; C & D on line 2)
                # 4 separate lines only if any choice is unusually long (> 55 chars or multiline)
                choices = q["choices"]
                choice_xmls = q.get("choice_xmls", {})
                correct_k = q["correct"]
                
                lengths = [len(re.sub(r"<[^>]+>", "", str(choices.get(k, "")))) for k in ["A", "B", "C", "D"]]
                max_len = max(lengths) if lengths else 0
                has_newlines = any(('\n' in str(choices.get(k, '')) or '<br' in str(choices.get(k, ''))) for k in ["A", "B", "C", "D"])

                if max_len <= 55 and not has_newlines:
                    # Standard: 2 choices per line (2x2 borderless table: A & B on row 0; C & D on row 1)
                    tbl_c = doc.add_table(rows=2, cols=2)
                    tbl_c.alignment = WD_TABLE_ALIGNMENT.CENTER
                    tbl_c.autofit = False
                    set_table_no_borders(tbl_c)

                    for r in tbl_c.rows:
                        trPr = r._tr.get_or_add_trPr()
                        trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

                    cells_map = [
                        (tbl_c.cell(0, 0), "A"),
                        (tbl_c.cell(0, 1), "B"),
                        (tbl_c.cell(1, 0), "C"),
                        (tbl_c.cell(1, 1), "D"),
                    ]
                    for cell, k in cells_map:
                        cell.width = Inches(3.35)
                        cp = cell.paragraphs[0]
                        cp.paragraph_format.space_before = Pt(1)
                        cp.paragraph_format.space_after = Pt(2)
                        cp.paragraph_format.line_spacing = 1.15
                        is_corr = (k == correct_k and is_answer_key)
                        r_k = cp.add_run(f"{k}. ")
                        r_k.bold = True
                        if is_corr:
                            r_k.font.color.rgb = RED_COLOR
                        self._append_elements_or_text(
                            cp, 
                            choice_xmls.get(k, []), 
                            choices.get(k, ""), 
                            is_red=is_corr, 
                            strip_red=not is_answer_key,
                            strip_bold=not is_answer_key
                        )
                else:
                    # 4 separate lines (each choice on its own line)
                    for k in ["A", "B", "C", "D"]:
                        p_c = doc.add_paragraph()
                        p_c.paragraph_format.space_before = Pt(1)
                        p_c.paragraph_format.space_after = Pt(1)
                        p_c.paragraph_format.line_spacing = 1.15
                        if k != "D":
                            p_c.paragraph_format.keep_with_next = True
                        is_corr = (k == correct_k and is_answer_key)
                        r_k = p_c.add_run(f"{k}. ")
                        r_k.bold = True
                        if is_corr:
                            r_k.font.color.rgb = RED_COLOR
                        self._append_elements_or_text(
                            p_c, 
                            choice_xmls.get(k, []), 
                            choices.get(k, ""), 
                            is_red=is_corr, 
                            strip_red=not is_answer_key,
                            strip_bold=not is_answer_key
                        )

        # ----------------- PHẦN II -----------------
        if variant.get("part2"):
            p_head = doc.add_paragraph()
            p_head.paragraph_format.space_before = Pt(12)
            p_head.paragraph_format.space_after = Pt(2)
            p_head.paragraph_format.keep_with_next = True
            r = p_head.add_run("PHẦN II. Câu trắc nghiệm đúng sai.")
            r.bold = True
            r.font.size = Pt(12.5)

            p_sub = doc.add_paragraph()
            p_sub.paragraph_format.space_after = Pt(6)
            r = p_sub.add_run("Thí sinh trả lời từ câu 1 đến câu {}. Trong mỗi ý a), b), c), d) ở mỗi câu, thí sinh chọn Đúng hoặc Sai.".format(len(variant["part2"])))
            r.italic = True

            for q in variant["part2"]:
                p_q = doc.add_paragraph()
                p_q.paragraph_format.space_before = Pt(5)
                p_q.paragraph_format.space_after = Pt(2)
                p_q.paragraph_format.line_spacing = 1.15
                p_q.paragraph_format.keep_with_next = True
                r_num = p_q.add_run(f"Câu {q['num']}: ")
                r_num.bold = True
                self._append_elements_or_text(
                    p_q, 
                    q.get("xml_strings", []), 
                    q["question"], 
                    is_red=False, 
                    strip_red=not is_answer_key,
                    strip_bold=not is_answer_key
                )

                items = q.get("items", {})
                for k in ["a", "b", "c", "d"]:
                    item = items.get(k, {})
                    p_item = doc.add_paragraph()
                    p_item.paragraph_format.space_before = Pt(1)
                    p_item.paragraph_format.space_after = Pt(1)
                    p_item.paragraph_format.line_spacing = 1.15
                    if k in ["a", "b"]:
                        p_item.paragraph_format.keep_with_next = True
                    
                    is_true = item.get("correct", False)
                    r_k = p_item.add_run(f"{k}) ")
                    if is_answer_key and is_true:
                        r_k.bold = True
                        r_k.font.color.rgb = RED_COLOR
                        
                    self._append_elements_or_text(
                        p_item, 
                        item.get("xml_strings", []), 
                        item.get("text", ""), 
                        is_red=(is_true and is_answer_key), 
                        strip_red=not is_answer_key,
                        strip_bold=not is_answer_key
                    )
                    
                    if is_answer_key:
                        p_item.add_run(" ")
                        r_tag = p_item.add_run(f"[{'ĐÚNG' if is_true else 'SAI'}]")
                        r_tag.bold = True
                        r_tag.font.color.rgb = RED_COLOR if is_true else GRAY_COLOR

        # ----------------- PHẦN III -----------------
        if variant.get("part3"):
            p_head = doc.add_paragraph()
            p_head.paragraph_format.space_before = Pt(12)
            p_head.paragraph_format.space_after = Pt(2)
            p_head.paragraph_format.keep_with_next = True
            r = p_head.add_run("PHẦN III. Câu trắc nghiệm trả lời ngắn.")
            r.bold = True
            r.font.size = Pt(12.5)

            p_sub = doc.add_paragraph()
            p_sub.paragraph_format.space_after = Pt(6)
            r = p_sub.add_run("Thí sinh trả lời từ câu 1 đến câu {}. Thí sinh điền kết quả vào ô tương ứng.".format(len(variant["part3"])))
            r.italic = True

            for q in variant["part3"]:
                p_q = doc.add_paragraph()
                p_q.paragraph_format.space_before = Pt(5)
                p_q.paragraph_format.space_after = Pt(2)
                p_q.paragraph_format.line_spacing = 1.15
                p_q.paragraph_format.keep_with_next = True
                r_num = p_q.add_run(f"Câu {q['num']}: ")
                r_num.bold = True
                self._append_elements_or_text(
                    p_q, 
                    q.get("xml_strings", []), 
                    q["question"], 
                    is_red=False, 
                    strip_red=not is_answer_key,
                    strip_bold=not is_answer_key
                )

                # Explicit Answer Box for Part III
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
                r0 = p0.add_run("Đáp án:")
                r0.bold = True
                r0.font.name = "Times New Roman"
                r0.font.size = Pt(11)

                c1 = tbl_ans.cell(0, 1)
                c1.width = Inches(2.2)

                if not is_answer_key:
                    # Student Exam: neat bordered box for student handwriting
                    set_cell_box_border(c1, color="4B5563", sz="8")
                    p1 = c1.paragraphs[0]
                    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p1.paragraph_format.space_before = Pt(3)
                    p1.paragraph_format.space_after = Pt(3)
                    p1.paragraph_format.line_spacing = Pt(14)
                    r1 = p1.add_run("")
                else:
                    # Teacher Key: red bordered box with centered bold red answer
                    r0.font.color.rgb = RED_COLOR
                    set_cell_box_border(c1, color="DC2626", sz="10")
                    p1 = c1.paragraphs[0]
                    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p1.paragraph_format.space_before = Pt(3)
                    p1.paragraph_format.space_after = Pt(3)
                    ans_val = str(q.get("answer", ""))
                    r1 = p1.add_run(ans_val)
                    r1.bold = True
                    r1.font.name = "Times New Roman"
                    r1.font.size = Pt(11.5)
                    r1.font.color.rgb = RED_COLOR

        # ----------------- PHẦN IV -----------------
        if variant.get("part4"):
            p_head = doc.add_paragraph()
            p_head.paragraph_format.space_before = Pt(12)
            p_head.paragraph_format.space_after = Pt(2)
            p_head.paragraph_format.keep_with_next = True
            r = p_head.add_run("PHẦN IV. Câu tự luận.")
            r.bold = True
            r.font.size = Pt(12.5)

            p_sub = doc.add_paragraph()
            p_sub.paragraph_format.space_after = Pt(6)
            r = p_sub.add_run("Thí sinh trình bày chi tiết lời giải vào giấy làm bài.")
            r.italic = True

            for q in variant["part4"]:
                p_q = doc.add_paragraph()
                p_q.paragraph_format.space_before = Pt(5)
                p_q.paragraph_format.space_after = Pt(2)
                p_q.paragraph_format.line_spacing = 1.15
                if is_answer_key and q.get("guide"):
                    p_q.paragraph_format.keep_with_next = True
                r_num = p_q.add_run(f"Câu {q['num']}: ")
                r_num.bold = True
                self._append_elements_or_text(
                    p_q, 
                    q.get("xml_strings", []), 
                    q["question"], 
                    is_red=False, 
                    strip_red=not is_answer_key,
                    strip_bold=not is_answer_key
                )

                if is_answer_key and q.get("guide"):
                    p_gd = doc.add_paragraph()
                    p_gd.paragraph_format.space_before = Pt(2)
                    p_gd.paragraph_format.space_after = Pt(4)
                    r_glbl = p_gd.add_run("Hướng dẫn chấm:\n")
                    r_glbl.italic = True
                    r_glbl.bold = True
                    r_glbl.font.color.rgb = RED_COLOR
                    self._insert_formatted_text(p_gd, q["guide"], is_red=True)

        # Footer for student exam
        if not is_answer_key:
            p_end = doc.add_paragraph()
            p_end.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_end.paragraph_format.space_before = Pt(16)
            p_end.paragraph_format.space_after = Pt(2)
            r_end = p_end.add_run("------------------ HẾT ------------------")
            r_end.bold = True
            
            p_note = doc.add_paragraph()
            p_note.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_note.paragraph_format.space_before = Pt(2)
            p_note.paragraph_format.space_after = Pt(6)
            r_note = p_note.add_run("• Thí sinh không được sử dụng tài liệu. Cán bộ coi thi không giải thích gì thêm.")
            r_note.italic = True
            r_note.font.size = Pt(10)

        doc.save(file_path)

    def _append_elements_or_text(self, paragraph, xml_strings: list[str], fallback_text: str, is_red: bool = False, strip_red: bool = False, strip_bold: bool = False):
        """Appends native OMML/docx runs from xml_strings, or falls back to formatted text."""
        if xml_strings:
            elements = deserialize_oxml_elements(xml_strings)
            for elem in elements:
                heal_omath_element(elem)
                if strip_red:
                    strip_red_from_element(elem)
                elif is_red:
                    set_red_on_element(elem)
                if strip_bold:
                    strip_bold_from_element(elem)
                paragraph._p.append(elem)
        else:
            self._insert_formatted_text(paragraph, fallback_text, is_red=is_red)


    def _insert_formatted_text(self, paragraph, html_text: str, is_red: bool = False):
        """Splits HTML into text, math ($...$), and sub/sup tags and inserts corresponding docx runs."""
        clean_str = str(html_text).replace("<br>", "\n").replace("<br/>", "\n")
        tokens = re.split(r"(\$[^\$]+\$|<sub>.*?</sub>|<sup>.*?</sup>)", clean_str, flags=re.IGNORECASE)
        for token in tokens:
            if not token:
                continue
            if token.startswith("$") and token.endswith("$") and len(token) > 2:
                math_inner = token[1:-1]
                math_clean = math_inner.replace("\\frac", "").replace("\\sqrt", "√").replace("\\int", "∫").replace("\\vec", "").replace("{", "").replace("}", "")
                r = paragraph.add_run(math_clean)
                r.italic = True
                if is_red:
                    r.font.color.rgb = RED_COLOR
            elif token.lower().startswith("<sub>"):
                inner = re.sub(r"</?sub>", "", token, flags=re.IGNORECASE)
                r = paragraph.add_run(inner)
                rPr = r._r.get_or_add_rPr()
                va = OxmlElement('w:vertAlign')
                va.set(qn('w:val'), 'subscript')
                rPr.append(va)
                if is_red:
                    r.font.color.rgb = RED_COLOR
            elif token.lower().startswith("<sup>"):
                inner = re.sub(r"</?sup>", "", token, flags=re.IGNORECASE)
                r = paragraph.add_run(inner)
                rPr = r._r.get_or_add_rPr()
                va = OxmlElement('w:vertAlign')
                va.set(qn('w:val'), 'superscript')
                rPr.append(va)
                if is_red:
                    r.font.color.rgb = RED_COLOR
            else:
                r = paragraph.add_run(token)
                if is_red:
                    r.font.color.rgb = RED_COLOR

    def _generate_summary_docx(self, file_path: str):
        """Generates comprehensive summary answer keys DOCX with clear tables for all 4 parts."""
        doc = docx.Document()
        for sec in doc.sections:
            sec.top_margin = Inches(0.70)
            sec.bottom_margin = Inches(0.70)
            sec.left_margin = Inches(0.70)
            sec.right_margin = Inches(0.70)

        self._setup_footer(doc, "", title_prefix="BẢNG ĐÁP ÁN TỔNG HỢP")

        codes = self.summary.get("codes", [])

        # Document Title
        p_title = doc.add_paragraph()
        p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p_title.add_run("BẢNG TỔNG HỢP ĐÁP ÁN CÁC MÃ ĐỀ THI\n")
        r.bold = True
        r.font.size = Pt(16)
        r.font.color.rgb = BLUE_COLOR
        
        subject = self.metadata.get("subject") or "KHOA HỌC TỰ NHIÊN"
        r_sub = p_title.add_run(f"MÔN THI: {subject.upper()}")
        r_sub.bold = True
        r_sub.font.size = Pt(12)

        # ----------------- PHẦN I TABLE -----------------
        p1_rows = self.summary.get("part1", {}).get("rows", [])
        if p1_rows:
            p_p1 = doc.add_paragraph()
            p_p1.paragraph_format.space_before = Pt(14)
            p_p1.paragraph_format.space_after = Pt(4)
            r = p_p1.add_run("I. BẢNG ĐÁP ÁN PHẦN I (TRẮC NGHIỆM KHÁCH QUAN)")
            r.bold = True
            r.font.size = Pt(12.5)

            # Columns: Câu, Code 1, Code 2...
            cols_count = 1 + len(codes)
            tbl1 = doc.add_table(rows=1 + len(p1_rows), cols=cols_count)
            tbl1.alignment = WD_TABLE_ALIGNMENT.CENTER
            tbl1.style = 'Table Grid'

            # Header Row
            hdr = tbl1.rows[0]
            hdr.cells[0].paragraphs[0].add_run("Câu")
            format_cell(hdr.cells[0], bg_hex="1E40AF", bold=True)
            hdr.cells[0].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
            
            for i, c in enumerate(codes, start=1):
                hdr.cells[i].paragraphs[0].add_run(f"Mã {c}")
                format_cell(hdr.cells[i], bg_hex="1E40AF", bold=True)
                hdr.cells[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)

            # Data Rows
            for row_idx, r_data in enumerate(p1_rows, start=1):
                row_cells = tbl1.rows[row_idx].cells
                bg = "F9FAFB" if row_idx % 2 == 0 else "FFFFFF"
                
                row_cells[0].paragraphs[0].add_run(str(r_data["question_num"]))
                format_cell(row_cells[0], bg_hex=bg, bold=True)
                
                for c_idx, c in enumerate(codes, start=1):
                    ans_val = r_data.get(c, "")
                    row_cells[c_idx].paragraphs[0].add_run(ans_val)
                    format_cell(row_cells[c_idx], bg_hex=bg, bold=True)

        # ----------------- PHẦN II TABLE -----------------
        p2_rows = self.summary.get("part2", {}).get("rows", [])
        if p2_rows:
            p_p2 = doc.add_paragraph()
            p_p2.paragraph_format.space_before = Pt(14)
            p_p2.paragraph_format.space_after = Pt(4)
            r = p_p2.add_run("II. BẢNG ĐÁP ÁN PHẦN II (TRẮC NGHIỆM ĐÚNG / SAI)")
            r.bold = True
            r.font.size = Pt(12.5)

            tbl2 = doc.add_table(rows=1 + len(p2_rows), cols=1 + len(codes))
            tbl2.alignment = WD_TABLE_ALIGNMENT.CENTER
            tbl2.style = 'Table Grid'

            hdr2 = tbl2.rows[0]
            hdr2.cells[0].paragraphs[0].add_run("Lệnh hỏi")
            format_cell(hdr2.cells[0], bg_hex="047857", bold=True)
            hdr2.cells[0].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
            
            for i, c in enumerate(codes, start=1):
                hdr2.cells[i].paragraphs[0].add_run(f"Mã {c}")
                format_cell(hdr2.cells[i], bg_hex="047857", bold=True)
                hdr2.cells[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)

            for row_idx, r_data in enumerate(p2_rows, start=1):
                row_cells = tbl2.rows[row_idx].cells
                bg = "F0FDF4" if row_idx % 2 == 0 else "FFFFFF"
                row_cells[0].paragraphs[0].add_run(r_data["label"])
                format_cell(row_cells[0], bg_hex=bg, bold=True)
                
                for c_idx, c in enumerate(codes, start=1):
                    ans_val = r_data.get(c, "")
                    row_cells[c_idx].paragraphs[0].add_run(ans_val)
                    format_cell(row_cells[c_idx], bg_hex=bg, bold=(ans_val == "Đ"))
                    if ans_val == "Đ":
                        row_cells[c_idx].paragraphs[0].runs[0].font.color.rgb = RGBColor(4, 120, 87)

        # ----------------- PHẦN III TABLE -----------------
        p3_rows = self.summary.get("part3", {}).get("rows", [])
        if p3_rows:
            p_p3 = doc.add_paragraph()
            p_p3.paragraph_format.space_before = Pt(14)
            p_p3.paragraph_format.space_after = Pt(4)
            r = p_p3.add_run("III. BẢNG ĐÁP ÁN PHẦN III (TRẢ LỜI NGẮN)")
            r.bold = True
            r.font.size = Pt(12.5)

            tbl3 = doc.add_table(rows=1 + len(p3_rows), cols=1 + len(codes))
            tbl3.alignment = WD_TABLE_ALIGNMENT.CENTER
            tbl3.style = 'Table Grid'

            hdr3 = tbl3.rows[0]
            hdr3.cells[0].paragraphs[0].add_run("Câu")
            format_cell(hdr3.cells[0], bg_hex="B45309", bold=True)
            hdr3.cells[0].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
            
            for i, c in enumerate(codes, start=1):
                hdr3.cells[i].paragraphs[0].add_run(f"Mã {c}")
                format_cell(hdr3.cells[i], bg_hex="B45309", bold=True)
                hdr3.cells[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)

            for row_idx, r_data in enumerate(p3_rows, start=1):
                row_cells = tbl3.rows[row_idx].cells
                bg = "FFFBEB" if row_idx % 2 == 0 else "FFFFFF"
                row_cells[0].paragraphs[0].add_run(f"Câu {r_data['question_num']}")
                format_cell(row_cells[0], bg_hex=bg, bold=True)
                
                for c_idx, c in enumerate(codes, start=1):
                    ans_val = str(r_data.get(c, ""))
                    row_cells[c_idx].paragraphs[0].add_run(ans_val)
                    format_cell(row_cells[c_idx], bg_hex=bg, bold=True)

        doc.save(file_path)
