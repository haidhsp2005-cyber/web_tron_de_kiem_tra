import os
import re
import pymupdf

PART1_REGEX = re.compile(r"^\s*PH[^\s]*N\s+(I|1)[\.\:\s\-]", re.IGNORECASE)
PART2_REGEX = re.compile(r"^\s*PH[^\s]*N\s+(II|2)[\.\:\s\-]", re.IGNORECASE)
PART3_REGEX = re.compile(r"^\s*PH[^\s]*N\s+(III|3)[\.\:\s\-]", re.IGNORECASE)
PART4_REGEX = re.compile(r"^\s*PH[^\s]*N\s+(IV|4)[\.\:\s\-]", re.IGNORECASE)
QUESTION_REGEX = re.compile(r"^\s*(C[^\s]*u|B[^\s]*i)\s+(\d+)[\.\:\-\s]", re.IGNORECASE)
CHOICE_SPLIT_REGEX = re.compile(r"(?=(?:^|\s{2,}|\t)([A-D])[\.\:\)])")
CHOICE_PATTERN = re.compile(r"(?:^|\t|\s{2,}|(?<=[^\s\+\-\*\/\=\~\±\∓\(\[\{\<\>\:\,\.\_])\s+)([A-D])[\.\:\)](?=\s*\S)")
STOP_MARKER_REGEX = re.compile(r"(B[^\s]*NG\s+[^\s]*[AÁ]P\s+[AÁ]N|H[^\s]*NG\s+D[^\s]*N\s+CH[^\s]*M\s+(ĐỀ|MẪU|CHI\s+TIẾT|THI|\-\-)|\-\-+.*H[^\s]*T)", re.IGNORECASE)

def is_rgb_red(color_int: int) -> bool:
    """Check if sRGB integer color is in red range."""
    r = (color_int >> 16) & 255
    g = (color_int >> 8) & 255
    b = color_int & 255
    return r >= 170 and g <= 90 and b <= 90

def smart_join_lines(lines: list[str]) -> str:
    """
    Intelligently joins multi-line text extracted from PDF:
    - Normal prose lines that wrapped across margins are joined with a space.
    - Lines ending in colon ':', bullet points ('-', '•', numbers), or code statements are joined with newline '\n'.
    """
    if not lines:
        return ""
    clean_lines = [l.strip() for l in lines if l and l.strip()]
    if not clean_lines:
        return ""
    if len(clean_lines) == 1:
        return clean_lines[0]
        
    result = clean_lines[0]
    for i in range(1, len(clean_lines)):
        prev = clean_lines[i - 1]
        curr = clean_lines[i]
        
        prev_is_colon = prev.endswith(":") or prev.endswith("：")
        curr_is_bullet = bool(re.match(r"^(\-|\•|\+|\*|\–|[a-d]\)|\d+[\.\)])\s*", curr))
        
        is_code = (
            bool(re.match(r"^[a-zA-Z_]\w*\s*[\+\-\*\/\%]?\s*=", curr)) or
            bool(re.match(r"^[a-zA-Z_]\w*\s*[\+\-\*\/\%]?\s*=", prev)) or
            curr.startswith(("print(", "return ", "def ", "for ", "while ", "if ", "else:", "elif ", "import ")) or
            prev.startswith(("print(", "return ", "def ", "for ", "while ", "if ", "else:", "elif ", "import "))
        )
        
        is_guide_or_ans = bool(re.match(r"^(?:H[^\s]*ng\s*d[^\s]*n\s*ch[^\s]*m|HD\s*ch[^\s]*m|Lời\s*giải|[^\s]*áp\s*án)[\:\s]*", curr, re.IGNORECASE))
        
        if prev.endswith("-") and not prev_is_colon and not curr_is_bullet and len(prev) > 1 and prev[-2].isalpha():
            result = result[:-1] + curr
        elif prev_is_colon or curr_is_bullet or is_code or is_guide_or_ans:
            result += "\n" + curr
        else:
            result += " " + curr
            
    return result

from .formula_helper import sanitize_latex_string

def clean_math_text(text: str) -> str:
    r"""
    Normalizes and repairs math expressions across Grade 6-12 curriculum:
    - Fractions (\frac{a}{b}, a/b, unicode fractions)
    - Roots/Radicals (\sqrt{x}, \sqrt[n]{x}, √x)
    - Superscripts/Powers (x², x³, xⁿ, x^n)
    - Subscripts (x₁, x₂, u_n)
    - Vectors (a⃗, u⃗, AB⃗, \vec{u})
    - Systems of equations (cases, aligned, braces {, unicode ⎧ ⎨ ⎩ ⎪)
    - Calculus (\int, \lim, \sum)
    - Geometry & Set & Logic symbols (⊥, ∥, △, ∠, °, ∈, ∉, ⊂, ∪, ∩, ∅, ∀, ∃, ⇒, ⇔)
    """
    if not text:
        return ""
    s = str(text)

    # 1. Normalize unicode characters & PDF font artifacts
    s = s.replace('\u00ad', '-')      # Soft hyphen
    s = s.replace('\u2212', '-')      # Unicode minus
    s = s.replace('\u00a0', ' ')      # Non-breaking space
    s = s.replace('\u037e', ';')      # Greek question mark / semicolon
    
    # 2. Vectors: a⃗, u⃗, AB⃗, \vec{u}
    s = re.sub(r"([A-Za-z]{1,3})[\u20D7\u2192\u20D6⃗]", r"$\\vec{\1}$", s)
    s = re.sub(r"(?<!\$)\\vec\s*\{([A-Za-z0-9]{1,4})\}(?!\$)", r"$\\vec{\1}$", s)

    # 3. Systems of equations (Unicode brace glyphs: ⎧ ⎨ ⎩ ⎪)
    def repl_unicode_cases(m):
        block = m.group(0)
        raw_lines = re.split(r"<br\s*/?>|[\n\r]+", block)
        clean_lines = []
        for l in raw_lines:
            l_clean = re.sub(r"[⎧⎨⎩⎪\u23a7\u23a8\u23a9\u23aa\u23ab\u23ac\u23ad]", "", l).strip()
            if l_clean:
                clean_lines.append(l_clean)
        if clean_lines:
            joined = ' \\\\ '.join(clean_lines)
            return f"$\\begin{{cases}} {joined} \\end{{cases}}$"
        return block

    pattern_unicode = re.compile(r"[⎧\u23a7][^\n\r<]*(?:(?:<br\s*/?>|[\n\r]+)[^⎩\u23a9\n\r<]*)*[⎩\u23a9][^\n\r<]*")
    s = pattern_unicode.sub(repl_unicode_cases, s)

    # 4. Systems of equations (Text braces: "{ eq1 \n eq2" or "{ eq1 <br> eq2")
    pattern_brace = re.compile(r"\{\s*([^\n\r<]+)(?:<br\s*/?>|[\n\r]+)\s*([^\n\r<]+)(?:(?:<br\s*/?>|[\n\r]+)\s*([^\n\r<]+))?")
    def repl_brace(m):
        eq1 = m.group(1).strip()
        eq2 = m.group(2).strip()
        eq3 = (m.group(3) or "").strip()
        eqs = [eq1, eq2]
        if eq3 and any(op in eq3 for op in ["=", "<", ">", "≤", "≥", "≠"]):
            eqs.append(eq3)
        if any(op in eq1 for op in ["=", "<", ">", "≤", "≥", "≠"]) and any(op in eq2 for op in ["=", "<", ">", "≤", "≥", "≠"]):
            joined_eqs = ' \\\\ '.join(eqs)
            return f"$\\begin{{cases}} {joined_eqs} \\end{{cases}}$"
        return m.group(0)
    s = pattern_brace.sub(repl_brace, s)

    # 5. Convert \left\{\begin{matrix} or \begin{matrix} or \begin{aligned} to \begin{cases}
    s = re.sub(r"\\left\\{\s*\\begin\{(?:cases|aligned|matrix)\}([\s\S]*?)\\end\{(?:cases|aligned|matrix)\}\s*(?:\\right[\.\)]?)?", r"\\begin{cases}\1\\end{cases}", s)
    s = re.sub(r"\{\s*\\begin\{(?:cases|aligned|matrix)\}([\s\S]*?)\\end\{(?:cases|aligned|matrix)\}\s*\}?", r"\\begin{cases}\1\\end{cases}", s)
    s = re.sub(r"\\begin\{aligned\}([\s\S]*?)\\end\{aligned\}", r"\\begin{cases}\1\\end{cases}", s)

    # 6. Standalone LaTeX radicals/fractions/integrals not wrapped in $:
    s = re.sub(r"(?<!\$)\\frac\{([^{}]+)\}\{([^{}]+)\}(?!\$)", r"$\\frac{\1}{\2}$", s)
    s = re.sub(r"(?<!\$)\\sqrt\{([^{}]+)\}(?!\$)", r"$\\sqrt{\1}$", s)
    s = re.sub(r"(?<!\$)\\sqrt\[([^\[\]]+)\]\{([^{}]+)\}(?!\$)", r"$\\sqrt[\1]{\2}$", s)

    # 7. Sanitize latex string
    s = sanitize_latex_string(s)

    return s

def safe_clean_math_text(text: str) -> str:
    """Safely runs clean_math_text while preserving <img> and <div ...> tags with base64 data intact."""
    if not text:
        return ""
    tag_pattern = re.compile(r'(<div[^>]*class=["\']exam-image-wrap["\'][^>]*>[\s\S]*?</div>|<img[^>]+>)', re.IGNORECASE)
    placeholders = []
    def save_tag(m):
        idx = len(placeholders)
        placeholders.append(m.group(0))
        return f"__EXAM_IMAGE_PLACEHOLDER_{idx}__"
    
    masked_text = tag_pattern.sub(save_tag, text)
    cleaned = clean_math_text(masked_text)
    for idx, orig_tag in enumerate(placeholders):
        cleaned = cleaned.replace(f"__EXAM_IMAGE_PLACEHOLDER_{idx}__", orig_tag)
    return cleaned

class PdfParser:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.doc = pymupdf.open(file_path)
        self.metadata = {
            "title": "ĐỀ KIỂM TRA (PDF)",
            "school": "THPT Long Cang",
            "subject": "Toán",
            "time": "90 phút",
            "year": "2026 - 2027"
        }
        self.part1_questions = []
        self.part2_questions = []
        self.part3_questions = []
        self.part4_questions = []

    def parse(self) -> dict:
        paragraphs_data = self._extract_paragraphs_from_pdf()
        
        current_part = 1
        i = 0
        n = len(paragraphs_data)
        
        while i < n:
            p_data = paragraphs_data[i]
            text = p_data["raw_text"].strip()
            
            # Skip instructions if any
            if "HƯỚNG DẪN ĐỊNH DẠNG" in text.upper():
                i += 1
                continue
                
            # Stop if we hit end-of-exam marker or trailing separate answer key section
            if (len(self.part1_questions) > 0 or len(self.part2_questions) > 0) and STOP_MARKER_REGEX.search(text):
                break

            if PART1_REGEX.search(text):
                current_part = 1
                i += 1
                continue
            elif PART2_REGEX.search(text):
                current_part = 2
                i += 1
                continue
            elif PART3_REGEX.search(text):
                current_part = 3
                i += 1
                continue
            elif PART4_REGEX.search(text):
                current_part = 4
                i += 1
                continue
                
            q_match = QUESTION_REGEX.search(text)
            if q_match:
                if current_part == 1:
                    i = self._parse_part1_question(paragraphs_data, i)
                elif current_part == 2:
                    i = self._parse_part2_question(paragraphs_data, i)
                elif current_part == 3:
                    i = self._parse_part3_question(paragraphs_data, i)
                elif current_part == 4:
                    i = self._parse_part4_question(paragraphs_data, i)
                else:
                    i += 1
            else:
                self._check_metadata(text)
                i += 1

        return {
            "metadata": self.metadata,
            "part1": self.part1_questions,
            "part2": self.part2_questions,
            "part3": self.part3_questions,
            "part4": self.part4_questions,
            "stats": {
                "total_questions": len(self.part1_questions) + len(self.part2_questions) + len(self.part3_questions) + len(self.part4_questions),
                "part1_count": len(self.part1_questions),
                "part2_count": len(self.part2_questions),
                "part3_count": len(self.part3_questions),
                "part4_count": len(self.part4_questions)
            }
        }

    def _extract_paragraphs_from_pdf(self) -> list[dict]:
        import base64
        paragraphs = []
        for page in self.doc:
            page_dict = page.get_text("dict")
            page_items = []
            
            for block in page_dict.get("blocks", []):
                btype = block.get("type")
                bbox = block.get("bbox", [0, 0, 0, 0])
                
                # Image block
                if btype == 1:
                    img_bytes = block.get("image")
                    ext = block.get("ext", "png")
                    if img_bytes:
                        b64 = base64.b64encode(img_bytes).decode("ascii")
                        mime = f"image/{ext}" if ext != "jpg" else "image/jpeg"
                        data_uri = f"data:{mime};base64,{b64}"
                        page_items.append({
                            "type": "image",
                            "y0": bbox[1],
                            "x0": bbox[0],
                            "bbox": bbox,
                            "raw_text": "[Hình minh họa]",
                            "formatted_text": f'<div class="exam-image-wrap" style="text-align:center;margin:6px 0;"><img src="{data_uri}" style="max-width:100%;max-height:350px;" class="exam-figure" /></div>',
                            "has_red": False,
                            "is_image": True,
                            "image_data": data_uri,
                            "image_bytes": img_bytes,
                            "image_ext": ext,
                            "spans": []
                        })
                elif btype == 0:
                    for line in block.get("lines", []):
                        line_spans = []
                        raw_line = ""
                        has_red = False
                        for span in line.get("spans", []):
                            txt = span.get("text", "")
                            c = span.get("color", 0)
                            is_red = is_rgb_red(c)
                            if is_red:
                                has_red = True
                            line_spans.append({
                                "text": txt,
                                "is_red": is_red,
                                "bbox": span.get("bbox", [])
                            })
                            raw_line += txt
                        
                        clean_raw = raw_line.strip()
                        # Skip header/footer line markers
                        if clean_raw and not re.search(r"^\s*Mã\s*đề[\:\s]+\d+.*Trang\s+\d+", clean_raw, re.IGNORECASE) and not re.search(r"^\s*Trang\s+\d+/\d+\s*$", clean_raw, re.IGNORECASE):
                            l_bbox = line.get("bbox", [0, 0, 0, 0])
                            page_items.append({
                                "type": "text",
                                "y0": l_bbox[1],
                                "x0": l_bbox[0],
                                "bbox": l_bbox,
                                "raw_text": clean_raw,
                                "formatted_text": clean_raw,
                                "spans": line_spans,
                                "has_red": has_red,
                                "is_image": False
                            })
            # Sort items on each page in natural vertical reading order
            page_items.sort(key=lambda it: (it["y0"], it["x0"]))
            paragraphs.extend(page_items)
            
        return paragraphs

    def _check_metadata(self, text: str):
        if "SỞ" in text.upper() or "TRƯỜNG" in text.upper():
            self.metadata["school"] = text.split("\n")[0].strip()
        if "MÔN:" in text.upper() or "MÔN " in text.upper():
            m = re.search(r"MÔN[\:\s]+([^\n\r]+)", text, re.IGNORECASE)
            if m:
                self.metadata["subject"] = m.group(1).strip()
        if "THỜI GIAN" in text.upper():
            m = re.search(r"(\d+)\s*phút", text, re.IGNORECASE)
            if m:
                self.metadata["time"] = f"{m.group(1)} phút"

    # ================= PART 1 (MCQ) =================
    def _parse_part1_question(self, paragraphs_data, start_idx) -> int:
        p_data = paragraphs_data[start_idx]
        raw_text = p_data["raw_text"]
        fmt_text = p_data.get("formatted_text", raw_text)
        q_match = QUESTION_REGEX.search(raw_text)
        q_num = int(q_match.group(2)) if q_match else len(self.part1_questions) + 1
        
        clean_q_text = re.sub(r"^\s*(Câu|Bài)\s+\d+[\.\:\-\s]+", "", fmt_text).strip()
        choices = {"A": "", "B": "", "C": "", "D": ""}
        correct_answer = "A"
        found_red = False
        images = []
        if p_data.get("is_image"):
            images.append({"data": p_data["image_data"], "ext": p_data["image_ext"]})

        idx = start_idx + 1
        # Check inline choices
        inline_c, inline_splits = self._extract_choices_from_pdf_p(p_data)
        if len(inline_c) >= 2:
            for k, info in inline_c.items():
                choices[k] = safe_clean_math_text(info["text"])
                if info["is_red"]:
                    correct_answer = k
                    found_red = True
            self.part1_questions.append({
                "id": len(self.part1_questions) + 1,
                "original_num": q_num,
                "question": safe_clean_math_text(clean_q_text),
                "choices": choices,
                "correct": correct_answer,
                "has_red": found_red,
                "images": images,
                "xml_strings": []
            })
            return idx

        seen_choice_keys = set()
        last_splits = []
        last_keys = []

        while idx < len(paragraphs_data):
            next_p = paragraphs_data[idx]
            next_text = next_p["raw_text"].strip()
            next_fmt = next_p.get("formatted_text", next_text)
            
            if (QUESTION_REGEX.search(next_text) or PART1_REGEX.search(next_text) or 
                PART2_REGEX.search(next_text) or PART3_REGEX.search(next_text) or 
                PART4_REGEX.search(next_text) or
                STOP_MARKER_REGEX.search(next_text)):
                break
                
            p_choices, p_splits = self._extract_choices_from_pdf_p(next_p)
            if p_choices:
                for k, info in p_choices.items():
                    seen_choice_keys.add(k)
                    choices[k] = info["text"]
                    if info["is_red"]:
                        correct_answer = k
                        found_red = True
                last_splits = p_splits
                last_keys = [k for k, _, _ in p_splits]
                idx += 1
            else:
                if not seen_choice_keys:
                    clean_q_text += "<br>" + next_fmt
                    if next_p.get("is_image"):
                        images.append({"data": next_p["image_data"], "ext": next_p["image_ext"]})
                    idx += 1
                else:
                    # Continuation line for choices!
                    if next_p.get("is_image") and last_keys:
                        choices[last_keys[-1]] += "<br>" + next_fmt
                    elif len(last_keys) >= 2:
                        for s_idx, (k, s_start, s_end) in enumerate(last_splits):
                            seg_start = s_start
                            seg_end = last_splits[s_idx+1][1] if s_idx + 1 < len(last_splits) else len(next_p["raw_text"])
                            seg_text = next_p["raw_text"][seg_start:seg_end].strip() if seg_start < len(next_p["raw_text"]) else ""
                            if seg_text:
                                choices[k] = (choices[k] + "\n" + seg_text).strip()
                    elif len(last_keys) == 1:
                        k = last_keys[0]
                        choices[k] = (choices[k] + "\n" + next_text).strip()
                    if next_p["has_red"] and last_keys:
                        correct_answer = last_keys[0]
                        found_red = True
                    idx += 1

        clean_q_text = safe_clean_math_text(clean_q_text)
        for k in choices:
            choices[k] = safe_clean_math_text(choices[k])

        self.part1_questions.append({
            "id": len(self.part1_questions) + 1,
            "original_num": q_num,
            "question": clean_q_text,
            "choices": choices,
            "correct": correct_answer,
            "has_red": found_red,
            "images": images,
            "xml_strings": []
        })
        return idx

    def _extract_choices_from_pdf_p(self, p_data) -> tuple[dict, list]:
        res = {}
        splits = []
        text = p_data["raw_text"]
        matches = list(CHOICE_PATTERN.finditer(text))
        if not matches:
            m_single = re.match(r"^\s*([A-D])[\.\:\)]\s*(.*)", text)
            if m_single:
                key = m_single.group(1).upper()
                c_text = re.sub(r"^\s*([A-D])[\.\:\)]\s*", "", text).strip()
                res[key] = {
                    "text": c_text,
                    "is_red": p_data["has_red"]
                }
                splits.append((key, 0, len(text)))
            return res, splits

        filtered_matches = []
        last_key_ord = -1
        for m in matches:
            k = m.group(1).upper()
            k_ord = ord(k)
            if k_ord > last_key_ord:
                filtered_matches.append(m)
                last_key_ord = k_ord

        if not filtered_matches:
            return res, splits

        curr_pos = 0
        spans_mapped = []
        for sp in p_data["spans"]:
            s_len = len(sp["text"])
            spans_mapped.append((curr_pos, curr_pos + s_len, sp["is_red"], sp["text"]))
            curr_pos += s_len

        for i, match in enumerate(filtered_matches):
            key = match.group(1).upper()
            m_start = match.start(1)
            m_end = filtered_matches[i+1].start(1) if i + 1 < len(filtered_matches) else len(text)
            c_text_raw = re.sub(r"^[A-D][\.\:\)]\s*", "", text[m_start:m_end]).strip()
            if not c_text_raw:
                continue

            choice_is_red = False
            for s, e, is_red, sp_txt in spans_mapped:
                if max(s, m_start) < min(e, m_end) and is_red:
                    choice_is_red = True
                    break

            res[key] = {
                "text": c_text_raw,
                "is_red": choice_is_red
            }
            splits.append((key, m_start, m_end))
        return res, splits

    # ================= PART 2 (TRUE / FALSE) =================
    def _parse_part2_question(self, paragraphs_data, start_idx) -> int:
        p_data = paragraphs_data[start_idx]
        raw_text = p_data["raw_text"]
        fmt_text = p_data.get("formatted_text", raw_text)
        q_match = QUESTION_REGEX.search(raw_text)
        q_num = int(q_match.group(2)) if q_match else len(self.part2_questions) + 1
        
        clean_q_text = re.sub(r"^\s*(Câu|Bài)\s+\d+[\.\:\-\s]+", "", fmt_text).strip()
        items = {
            "a": {"text": "", "correct": False},
            "b": {"text": "", "correct": False},
            "c": {"text": "", "correct": False},
            "d": {"text": "", "correct": False}
        }
        images = []
        if p_data.get("is_image"):
            images.append({"data": p_data["image_data"], "ext": p_data["image_ext"]})

        last_key = None
        idx = start_idx + 1
        while idx < len(paragraphs_data):
            next_p = paragraphs_data[idx]
            next_text = next_p["raw_text"].strip()
            next_fmt = next_p.get("formatted_text", next_text)
            
            if (QUESTION_REGEX.search(next_text) or PART1_REGEX.search(next_text) or 
                PART2_REGEX.search(next_text) or PART3_REGEX.search(next_text) or 
                PART4_REGEX.search(next_text) or
                STOP_MARKER_REGEX.search(next_text)):
                break
                
            item_match = re.match(r"^\s*([a-d])[\)\.]\s*(.*)", next_text, re.IGNORECASE)
            if item_match:
                key = item_match.group(1).lower()
                last_key = key
                content = re.sub(r"^\s*([a-d])[\)\.]\s*", "", next_text).strip()
                
                # True/False detection
                is_true = next_p["has_red"]
                if re.search(r"(\[|\()(Đ|·|D|đ)úng(\]|\))", next_text, re.IGNORECASE):
                    is_true = True
                elif re.search(r"(\[|\()Sai(\]|\))", next_text, re.IGNORECASE):
                    is_true = False
                    
                clean_content = re.sub(r"(\[|\()(Đ|·|D|đ)úng(\]|\))|(\[|\()Sai(\]|\))", "", content, flags=re.IGNORECASE).strip()
                items[key] = {
                    "text": clean_content,
                    "correct": is_true
                }
                idx += 1
            else:
                if last_key is None:
                    clean_q_text += "<br>" + next_fmt
                    if next_p.get("is_image"):
                        images.append({"data": next_p["image_data"], "ext": next_p["image_ext"]})
                    idx += 1
                else:
                    if next_p.get("is_image"):
                        items[last_key]["text"] += "<br>" + next_fmt
                    else:
                        is_true_cont = next_p["has_red"]
                        if re.search(r"(\[|\()(Đ|·|D|đ)úng(\]|\))", next_text, re.IGNORECASE):
                            items[last_key]["correct"] = True
                        elif re.search(r"(\[|\()Sai(\]|\))", next_text, re.IGNORECASE):
                            items[last_key]["correct"] = False
                        elif is_true_cont:
                            items[last_key]["correct"] = True
                        
                        clean_cont = re.sub(r"(\[|\()(Đ|·|D|đ)úng(\]|\))|(\[|\()Sai(\]|\))", "", next_text, flags=re.IGNORECASE).strip()
                        if clean_cont:
                            items[last_key]["text"] = (items[last_key]["text"] + " " + clean_cont).strip()
                    idx += 1

        clean_q_text = safe_clean_math_text(clean_q_text)
        for k in items:
            items[k]["text"] = safe_clean_math_text(items[k]["text"])

        self.part2_questions.append({
            "id": len(self.part2_questions) + 1,
            "original_num": q_num,
            "question": clean_q_text,
            "items": items,
            "images": images,
            "xml_strings": []
        })
        return idx

    # ================= PART 3 (SHORT ANSWER) =================
    def _parse_part3_question(self, paragraphs_data, start_idx) -> int:
        p_data = paragraphs_data[start_idx]
        raw_text = p_data["raw_text"]
        fmt_text = p_data.get("formatted_text", raw_text)
        q_match = QUESTION_REGEX.search(raw_text)
        q_num = int(q_match.group(2)) if q_match else len(self.part3_questions) + 1
        
        q_parts = [fmt_text]
        images = []
        if p_data.get("is_image"):
            images.append({"data": p_data["image_data"], "ext": p_data["image_ext"]})

        idx = start_idx + 1
        while idx < len(paragraphs_data):
            next_p = paragraphs_data[idx]
            next_text = next_p["raw_text"].strip()
            next_fmt = next_p.get("formatted_text", next_text)
            if (QUESTION_REGEX.search(next_text) or PART1_REGEX.search(next_text) or 
                PART2_REGEX.search(next_text) or PART3_REGEX.search(next_text) or 
                PART4_REGEX.search(next_text) or
                STOP_MARKER_REGEX.search(next_text)):
                break
            q_parts.append(next_fmt)
            if next_p.get("is_image"):
                images.append({"data": next_p["image_data"], "ext": next_p["image_ext"]})
            idx += 1

        full_html = "<br>".join(q_parts)
        full_html = re.sub(r"^\s*(Câu|Bài)\s+\d+[\.\:\-\s]+", "", full_html).strip()
        
        ans_pattern = (
            r"(?:"
            r"(?:<br>|\n|^|\s{2,}|\b)(?:[^\s]*áp\s*án|Đáp\s*án)\s*[:=]?\s*([^\n\r<]+)|"
            r"(?:<br>|\n|^|\s{2,}|\b)(?:Đ\/[aA]|ĐA|Trả\s*lời)\s*[:=]\s*([^\n\r<]+)|"
            r"(?:<br>|\n|^)\s*(?:Kết\s*quả|KQ)\s*[:=]\s*([^\n\r?<]+)"
            r")"
        )
        answer = ""
        m_ans = re.search(ans_pattern, full_html, re.IGNORECASE)
        if m_ans:
            answer = (m_ans.group(1) or m_ans.group(2) or m_ans.group(3) or "").strip()
            clean_q = full_html[:m_ans.start()].strip()
            clean_q = re.sub(r"(<br>|\n)+$", "", clean_q).strip()
        else:
            clean_q = full_html
            if p_data["has_red"]:
                for sp in p_data["spans"]:
                    if sp["is_red"] and sp["text"].strip():
                        answer = sp["text"].strip()
                        break

        clean_q = safe_clean_math_text(clean_q)
        answer = safe_clean_math_text(answer)
        if re.search(r"(\\[a-zA-Z]+|[\^_])", answer) and not (answer.startswith("$") and answer.endswith("$")):
            answer = f"${answer.strip()}$"

        self.part3_questions.append({
            "id": len(self.part3_questions) + 1,
            "original_num": q_num,
            "question": clean_q,
            "answer": answer,
            "images": images,
            "xml_strings": []
        })
        return idx

    # ================= PART 4 (ESSAY) =================
    def _parse_part4_question(self, paragraphs_data, start_idx) -> int:
        p_data = paragraphs_data[start_idx]
        raw_text = p_data["raw_text"]
        fmt_text = p_data.get("formatted_text", raw_text)
        q_match = QUESTION_REGEX.search(raw_text)
        q_num = int(q_match.group(2)) if q_match else len(self.part4_questions) + 1
        
        q_parts = [fmt_text]
        images = []
        if p_data.get("is_image"):
            images.append({"data": p_data["image_data"], "ext": p_data["image_ext"]})

        idx = start_idx + 1
        while idx < len(paragraphs_data):
            next_p = paragraphs_data[idx]
            next_text = next_p["raw_text"].strip()
            next_fmt = next_p.get("formatted_text", next_text)
            if (QUESTION_REGEX.search(next_text) or PART1_REGEX.search(next_text) or 
                PART2_REGEX.search(next_text) or PART3_REGEX.search(next_text) or 
                PART4_REGEX.search(next_text) or
                STOP_MARKER_REGEX.search(next_text)):
                break
            q_parts.append(next_fmt)
            if next_p.get("is_image"):
                images.append({"data": next_p["image_data"], "ext": next_p["image_ext"]})
            idx += 1

        full_html = "<br>".join(q_parts)
        parts = re.split(r"((?:^|\n|<br>|\s{2,}|\b)(?:H[^\s]*ng\s*d[^\s]*n\s*ch[^\s]*m|HD\s*ch[^\s]*m|Lời\s*giải|[^\s]*áp\s*án)[\:\s]*)", full_html, flags=re.IGNORECASE)
        if len(parts) >= 3:
            q_part = parts[0].strip()
            guide_part = "".join(parts[1:]).strip()
        else:
            q_part = full_html
            guide_part = ""

        clean_q = re.sub(r"^\s*(C[^\s]*u|B[^\s]*i)\s+\d+(\s*\([^\)]+\))?[\.\:\-\s]+", "", q_part).strip()
        clean_q = safe_clean_math_text(clean_q)
        guide_part = safe_clean_math_text(guide_part)

        self.part4_questions.append({
            "id": len(self.part4_questions) + 1,
            "original_num": q_num,
            "question": clean_q,
            "guide": guide_part,
            "images": images,
            "xml_strings": []
        })
        return idx
