import re
from copy import deepcopy
from xml.etree import ElementTree as ET
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

# Namespace definitions
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"

def is_color_red(hex_or_name: str) -> bool:
    if not hex_or_name:
        return False
    val = str(hex_or_name).strip().upper()
    if val in ["FF0000", "RED", "C00000", "ED1C24", "EE0000", "FF3333", "CC0000", "E00000", "DC2626"]:
        return True
    # If 6-character hex code, check if red channel is dominant
    if len(val) == 6:
        try:
            r = int(val[0:2], 16)
            g = int(val[2:4], 16)
            b = int(val[4:6], 16)
            return r >= 170 and g <= 90 and b <= 90
        except ValueError:
            return False
    return False

def is_run_element_red(run_elem) -> bool:
    """Check if a <w:r> element has red font color or red highlight."""
    try:
        rPr = run_elem.find(qn("w:rPr"))
        if rPr is not None:
            color = rPr.find(qn("w:color"))
            if color is not None:
                val = color.get(qn("w:val"), "")
                if is_color_red(val):
                    return True
            highlight = rPr.find(qn("w:highlight"))
            if highlight is not None:
                val = highlight.get(qn("w:val"), "").lower()
                if val in ["red", "darkred"]:
                    return True
    except Exception:
        pass
    return False

def is_math_element_red(math_elem) -> bool:
    """Check if any run inside an <m:oMath> element has red color."""
    try:
        for r in math_elem.iter(qn("w:r")):
            if is_run_element_red(r):
                return True
        for mr in math_elem.iter(qn("m:r")):
            rPr = mr.find(qn("w:rPr"))
            if rPr is None:
                rPr = mr.find(qn("m:rPr"))
            if rPr is not None:
                color = rPr.find(qn("w:color"))
                if color is not None and is_color_red(color.get(qn("w:val"), "")):
                    return True
    except Exception:
        pass
    return False

def strip_red_from_element(elem):
    """Remove red font color and highlight from an OpenXML element (<w:r> or <m:oMath>)."""
    try:
        for rPr in elem.iter(qn("w:rPr")):
            color = rPr.find(qn("w:color"))
            if color is not None and is_color_red(color.get(qn("w:val"), "")):
                rPr.remove(color)
            highlight = rPr.find(qn("w:highlight"))
            if highlight is not None:
                val = highlight.get(qn("w:val"), "").lower()
                if is_color_red(val) or val in ["red", "darkred"]:
                    rPr.remove(highlight)
        for mrPr in elem.iter(qn("m:rPr")):
            color = mrPr.find(qn("w:color"))
            if color is not None and is_color_red(color.get(qn("w:val"), "")):
                mrPr.remove(color)
    except Exception:
        pass

def strip_bold_from_element(elem):
    """Remove bold formatting from an OpenXML element (<w:r> or <m:oMath>)."""
    try:
        for b in elem.iter(qn("w:b")):
            parent = b.getparent()
            if parent is not None:
                parent.remove(b)
        for bCs in elem.iter(qn("w:bCs")):
            parent = bCs.getparent()
            if parent is not None:
                parent.remove(bCs)
    except Exception:
        pass

def heal_omath_element(elem):
    """
    Heals OMML <m:oMath> and <m:oMathPara> elements so that <m:nary> (integral, sigma)
    never has an empty base <m:e/>. If <m:e/> is empty, Word renders an empty square placeholder □.
    This function:
    1. If subsequent siblings exist in <m:oMath>, moves them inside <m:e>.
    2. If no subsequent siblings exist, inserts a zero-width space <m:r><m:t>&#x200B;</m:t></m:r> into <m:e>.
    """
    try:
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag in ["oMathPara"]:
            for child in list(elem):
                heal_omath_element(child)
            return

        if tag != "oMath":
            for omath in elem.iter(qn("m:oMath")):
                heal_omath_element(omath)
            return

        children = list(elem)
        n = len(children)
        i = 0
        while i < n:
            child = children[i]
            c_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if c_tag == "nary":
                e_elem = child.find(qn("m:e"))
                if e_elem is None:
                    e_elem = OxmlElement("m:e")
                    child.append(e_elem)

                e_text = "".join(e_elem.itertext()).strip()
                if not e_text and len(list(e_elem)) == 0:
                    j = i + 1
                    siblings_to_move = []
                    while j < n:
                        sib = children[j]
                        sib_tag = sib.tag.split("}")[-1] if "}" in sib.tag else sib.tag
                        if sib_tag == "nary":
                            break
                        siblings_to_move.append(sib)
                        j += 1

                    if siblings_to_move:
                        for sib in siblings_to_move:
                            elem.remove(sib)
                            e_elem.append(sib)
                        children = list(elem)
                        n = len(children)
                    else:
                        r = OxmlElement("m:r")
                        t = OxmlElement("m:t")
                        t.text = "\u200B"
                        r.append(t)
                        e_elem.append(r)
            i += 1
    except Exception:
        pass


def set_red_on_element(elem):
    """Set red font color (#DC2626) on an OpenXML element (<w:r> or <m:oMath>)."""
    try:
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag == "r":
            rPr = elem.find(qn("w:rPr"))
            if rPr is None:
                rPr = OxmlElement("w:rPr")
                elem.insert(0, rPr)
            color = rPr.find(qn("w:color"))
            if color is None:
                color = OxmlElement("w:color")
                rPr.append(color)
            color.set(qn("w:val"), "DC2626")
        elif tag in ["oMath", "oMathPara"]:
            for r in elem.iter(qn("w:r")):
                set_red_on_element(r)
            for mr in elem.iter(qn("m:r")):
                rPr = mr.find(qn("w:rPr"))
                if rPr is None:
                    rPr = mr.find(qn("m:rPr"))
                if rPr is None:
                    rPr = OxmlElement("m:rPr")
                    mr.insert(0, rPr)
                color = rPr.find(qn("w:color"))
                if color is None:
                    color = OxmlElement("w:color")
                    rPr.append(color)
                color.set(qn("w:val"), "DC2626")
    except Exception:
        pass

def sanitize_latex_string(s: str) -> str:
    """Sanitize and repair common malformed LaTeX strings."""
    if not s:
        return ""
    # 1. Clean nested \left\{ and \right. around \begin{cases} or \begin{aligned}
    s = re.sub(r"\\left\\{\s*\\begin\{(cases|aligned)\}", r"\\begin{\1}", s)
    s = re.sub(r"\\end\{(cases|aligned)\}\s*\\right\.?", r"\\end{\1}", s)

    # 2. Convert \begin{aligned} to \begin{cases}
    s = re.sub(r"\\begin\{aligned\}([\s\S]*?)\\end\{aligned\}", r"\\begin{cases}\1\\end{cases}", s)

    # 3. Clean malformed wraps like ${\$\begin{cases} ... \end{cases}$$ or ${\begin{cases} ... \end{cases}$
    s = re.sub(
        r"(?:\\left\\{|\{)?\s*\\?\$*\s*(?:\\left\\{|\{)?\s*\\?\$*\s*\\begin\{cases\}([\s\S]*?)\\end\{cases\}\s*(?:\\right\.?|\})?\s*\\?\$*\s*(?:\\right\.?|\})?\s*\\?\$*",
        r"$\\begin{cases}\1\\end{cases}$",
        s
    )

    # 4. Ensure space around $\begin{cases} if abutting regular letters
    s = re.sub(r"([^\s\$])(\$\\begin\{cases\})", r"\1 \2", s)
    s = re.sub(r"(\\end\{cases\}\$)([^\s\$\.\,\;\:\?\!])", r"\1 \2", s)

    return s

def extract_element_text_with_formatting(elem) -> tuple[str, bool]:
    """
    Extract text from a <w:r> or <m:oMath> or <m:oMathPara> element.
    Returns (formatted_text, is_red).
    Preserves subscript <sub>, superscript <sup> and math symbols.
    """
    tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
    is_red = False
    
    if tag == "r":
        is_red = is_run_element_red(elem)
        # Check vertAlign (subscript / superscript)
        rPr = elem.find(qn("w:rPr"))
        valign = ""
        if rPr is not None:
            va = rPr.find(qn("w:vertAlign"))
            if va is not None:
                valign = va.get(qn("w:val"), "")
        
        # Get text
        texts = []
        for child in elem:
            c_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if c_tag == "t" and child.text:
                texts.append(child.text)
            elif c_tag in ["br", "cr"]:
                texts.append("<br>")
            elif c_tag == "tab":
                texts.append("    ")
        txt = "".join(texts)
        if any(c in txt for c in ["\u20d7", "\u20d6", "\u2192", "⃗"]):
            txt = re.sub(r"([A-Za-z]{1,3})[\u20D7\u2192\u20D6⃗]", r"$\\vec{\1}$", txt)
        
        if valign == "subscript":
            txt = f"<sub>{txt}</sub>"
        elif valign == "superscript":
            txt = f"<sup>{txt}</sup>"
            
        return txt, is_red

    elif tag in ["oMath", "oMathPara"]:
        is_red = is_math_element_red(elem)
        math_text = extract_math_text(elem).strip()
        if math_text:
            math_text = sanitize_latex_string(math_text)
            if re.match(r"^\-?\d+$", math_text):
                return math_text, is_red
            if not math_text.startswith("$"):
                return f"${math_text}$", is_red
            return math_text, is_red
        return "", is_red

    elif tag == "t":
        return elem.text or "", False

    return "", False

def omml_to_latex(elem) -> str:
    """
    Recursively convert an OMML math element into clean, KaTeX-compliant LaTeX.
    Preserves integrals (\\int), vectors (\\vec), fractions (\\frac), roots (\\sqrt),
    subscripts, superscripts, limits, and delimiters.
    """
    if elem is None:
        return ""

    tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

    if tag in ["oMath", "oMathPara"]:
        parts = [omml_to_latex(child) for child in elem]
        return "".join(parts)

    elif tag == "r":
        texts = []
        for t in elem.findall(qn("m:t")):
            if t.text:
                texts.append(t.text)
        for t in elem.findall(qn("w:t")):
            if t.text:
                texts.append(t.text)
        return "".join(texts)

    elif tag == "t":
        return elem.text or ""

    elif tag == "f": # Fraction: \frac{num}{den}
        num = elem.find(qn("m:num"))
        den = elem.find(qn("m:den"))
        num_str = omml_to_latex(num) if num is not None else ""
        den_str = omml_to_latex(den) if den is not None else ""
        return f"\\frac{{{num_str}}}{{{den_str}}}"

    elif tag == "rad": # Radical: \sqrt[deg]{e} or \sqrt{e}
        deg = elem.find(qn("m:deg"))
        e = elem.find(qn("m:e"))
        e_str = omml_to_latex(e) if e is not None else ""
        deg_str = omml_to_latex(deg) if deg is not None else ""
        if deg_str.strip():
            return f"\\sqrt[{deg_str}]{{{e_str}}}"
        return f"\\sqrt{{{e_str}}}"

    elif tag == "sSup": # Superscript: {e}^{sup}
        e = elem.find(qn("m:e"))
        sup = elem.find(qn("m:sup"))
        e_str = omml_to_latex(e) if e is not None else ""
        sup_str = omml_to_latex(sup) if sup is not None else ""
        return f"{{{e_str}}}^{{{sup_str}}}"

    elif tag == "sSub": # Subscript: {e}_{sub}
        e = elem.find(qn("m:e"))
        sub = elem.find(qn("m:sub"))
        e_str = omml_to_latex(e) if e is not None else ""
        sub_str = omml_to_latex(sub) if sub is not None else ""
        return f"{{{e_str}}}_{{{sub_str}}}"

    elif tag == "sSubSup": # Subscript and Superscript: {e}_{sub}^{sup}
        e = elem.find(qn("m:e"))
        sub = elem.find(qn("m:sub"))
        sup = elem.find(qn("m:sup"))
        e_str = omml_to_latex(e) if e is not None else ""
        sub_str = omml_to_latex(sub) if sub is not None else ""
        sup_str = omml_to_latex(sup) if sup is not None else ""
        return f"{{{e_str}}}_{{{sub_str}}}^{{{sup_str}}}"

    elif tag == "nary": # N-ary operator (integral, summation, product)
        naryPr = elem.find(qn("m:naryPr"))
        chr_val = "∫"
        if naryPr is not None:
            chr_elem = naryPr.find(qn("m:chr"))
            if chr_elem is not None:
                chr_val = chr_elem.attrib.get(qn("m:val"), "∫")
        
        sub = elem.find(qn("m:sub"))
        sup = elem.find(qn("m:sup"))
        e = elem.find(qn("m:e"))
        
        sub_str = omml_to_latex(sub) if sub is not None else ""
        sup_str = omml_to_latex(sup) if sup is not None else ""
        e_str = omml_to_latex(e) if e is not None else ""
        
        op_map = {
            "∫": "\\int",
            "∬": "\\iint",
            "∭": "\\iiint",
            "∮": "\\oint",
            "∑": "\\sum",
            "∏": "\\prod"
        }
        latex_op = op_map.get(chr_val, chr_val)
        limits = ""
        if sub_str.strip():
            limits += f"_{{{sub_str}}}"
        if sup_str.strip():
            limits += f"^{{{sup_str}}}"
        
        sep = " " if e_str.strip() else ""
        return f"{latex_op}{limits}{sep}{e_str}"

    elif tag == "limUpp": # Limit upper or Vector arrow
        e = elem.find(qn("m:e"))
        lim = elem.find(qn("m:lim"))
        e_str = omml_to_latex(e) if e is not None else ""
        lim_str = omml_to_latex(lim) if lim is not None else ""
        if any(c in lim_str for c in ["→", "\\to", ">", "⃗"]):
            return f"\\vec{{{e_str}}}"
        return f"\\overset{{{lim_str}}}{{{e_str}}}"

    elif tag == "limLow": # Limit lower (e.g. \lim_{x \to 0})
        e = elem.find(qn("m:e"))
        lim = elem.find(qn("m:lim"))
        e_str = omml_to_latex(e) if e is not None else ""
        lim_str = omml_to_latex(lim) if lim is not None else ""
        return f"\\lim_{{{lim_str}}} {e_str}"

    elif tag == "acc": # Accent (vector, bar, hat, tilde)
        accPr = elem.find(qn("m:accPr"))
        chr_val = "⃗"
        if accPr is not None:
            chr_elem = accPr.find(qn("m:chr"))
            if chr_elem is not None:
                chr_val = chr_elem.attrib.get(qn("m:val"), "⃗")
        e = elem.find(qn("m:e"))
        e_str = omml_to_latex(e) if e is not None else ""
        if chr_val in ["⃗", "→", "\u20d7"]:
            return f"\\vec{{{e_str}}}"
        elif chr_val in ["¯", "-", "_", "\u0304"]:
            return f"\\overline{{{e_str}}}"
        elif chr_val in ["^", "\u0302"]:
            return f"\\hat{{{e_str}}}"
        elif chr_val in ["~", "\u0303"]:
            return f"\\tilde{{{e_str}}}"
        return f"\\bar{{{e_str}}}"

    elif tag == "d": # Delimiters (brackets, parentheses, absolute value)
        dPr = elem.find(qn("m:dPr"))
        beg_chr = "("
        end_chr = ")"
        if dPr is not None:
            b_elem = dPr.find(qn("m:begChr"))
            if b_elem is not None:
                beg_chr = b_elem.attrib.get(qn("m:val"), "(")
            e_elem = dPr.find(qn("m:endChr"))
            if e_elem is not None:
                end_chr = e_elem.attrib.get(qn("m:val"), ")")
        
        e_list = elem.findall(qn("m:e"))
        
        # System of equations: left curly brace '{' with no right brace
        if beg_chr == "{" and (not end_chr or end_chr in ["", " ", "."]):
            rows = []
            for e_item in e_list:
                eq_arrs = list(e_item.iter(qn("m:eqArr")))
                if eq_arrs:
                    for ea in eq_arrs:
                        for r in ea.findall(qn("m:e")):
                            rows.append(omml_to_latex(r))
                else:
                    rows.append(omml_to_latex(e_item))
            clean_rows = []
            for r in rows:
                r_clean = re.sub(r"\\(begin|end)\{(cases|aligned)\}", "", r).strip()
                if r_clean:
                    clean_rows.append(r_clean)
            arr_inner = " \\\\ ".join(clean_rows)
            return f"\\begin{{cases}} {arr_inner} \\end{{cases}}"
        elif beg_chr == "[" and (not end_chr or end_chr in ["", " ", "."]):
            rows = []
            for e_item in e_list:
                eq_arrs = list(e_item.iter(qn("m:eqArr")))
                if eq_arrs:
                    for ea in eq_arrs:
                        for r in ea.findall(qn("m:e")):
                            rows.append(omml_to_latex(r))
                else:
                    rows.append(omml_to_latex(e_item))
            clean_rows = []
            for r in rows:
                r_clean = re.sub(r"\\(begin|end)\{(cases|aligned)\}", "", r).strip()
                if r_clean:
                    clean_rows.append(r_clean)
            arr_inner = " \\\\ ".join(clean_rows)
            return f"\\left[ \\begin{{aligned}} {arr_inner} \\end{{aligned}} \\right."

        inner = ", ".join(omml_to_latex(e_item) for e_item in e_list)
        if "\\begin{cases}" in inner:
            return re.sub(r"\\left\\{\s*(\\begin\{cases\}[\s\S]*?\\end\{cases\})\s*\\right\.?", r"\1", inner)
        left_b = "\\{" if beg_chr == "{" else ("." if not beg_chr else beg_chr)
        right_b = "\\}" if end_chr == "}" else ("." if not end_chr else end_chr)
        return f"\\left{left_b}{inner}\\right{right_b}"

    elif tag == "func": # Function (sin, cos, log, ln)
        fName = elem.find(qn("m:fName"))
        e = elem.find(qn("m:e"))
        fName_str = omml_to_latex(fName) if fName is not None else ""
        e_str = omml_to_latex(e) if e is not None else ""
        return f"{fName_str} {e_str}"

    elif tag in ["bar", "groupChr"]: # Overline / Underline
        e = elem.find(qn("m:e"))
        e_str = omml_to_latex(e) if e is not None else ""
        return f"\\overline{{{e_str}}}"

    elif tag == "m": # Matrix
        rows = []
        for mr in elem.findall(qn("m:mr")):
            row_cells = [omml_to_latex(c) for c in mr.findall(qn("m:e"))]
            rows.append(" & ".join(row_cells))
        mat_inner = " \\\\ ".join(rows)
        return f"\\begin{{matrix}} {mat_inner} \\end{{matrix}}"

    elif tag == "eqArr": # Equation array
        rows = [omml_to_latex(e_item) for e_item in elem.findall(qn("m:e"))]
        arr_inner = " \\\\ ".join(rows)
        return f"\\begin{{cases}} {arr_inner} \\end{{cases}}"

    else:
        parts = [omml_to_latex(child) for child in elem]
        return "".join(parts)

def extract_math_text(elem) -> str:
    """Extract standard LaTeX from OMML element."""
    return omml_to_latex(elem)

def serialize_oxml_elements(elements) -> list[str]:
    """Serialize a list of oxml elements (runs, math blocks) to XML strings for faithful recreation."""
    from xml.etree.ElementTree import tostring
    result = []
    for elem in elements:
        try:
            xml_str = tostring(elem, encoding="unicode")
            result.append(xml_str)
        except Exception:
            pass
    return result

def deserialize_oxml_elements(xml_strings: list[str]) -> list:
    """Deserialize XML strings back to Word oxml elements."""
    elements = []
    for xml_str in xml_strings:
        try:
            elem = parse_xml(xml_str)
            elements.append(elem)
        except Exception:
            pass
    return elements

def strip_elements_prefix(xml_strings: list[str], pattern: str) -> list[str]:
    """
    Removes leading prefix text (e.g. 'Câu 1:', 'A.', 'a)') from the initial run elements.
    Ensures that when regenerating docx with custom numbers or shuffled choice letters,
    the label is never duplicated.
    """
    if not xml_strings:
        return []
        
    elements = deserialize_oxml_elements(xml_strings)
    regex = re.compile(pattern, re.IGNORECASE)
    
    accumulated_text = ""
    run_indices = []
    
    for idx, elem in enumerate(elements):
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag == "r":
            t_elems = elem.findall(qn("w:t"))
            r_text = "".join(t.text or "" for t in t_elems)
            accumulated_text += r_text
            run_indices.append((idx, elem, t_elems, r_text))
            
            m = regex.match(accumulated_text)
            if m:
                chars_to_remove = m.end()
                for r_idx, r_elem, t_list, original_r_text in run_indices:
                    if chars_to_remove <= 0:
                        break
                    cur_len = len(original_r_text)
                    if chars_to_remove >= cur_len:
                        for t in t_list:
                            t.text = ""
                        chars_to_remove -= cur_len
                    else:
                        rem = chars_to_remove
                        for t in t_list:
                            t_txt = t.text or ""
                            if rem >= len(t_txt):
                                rem -= len(t_txt)
                                t.text = ""
                            else:
                                t.text = t_txt[rem:]
                                rem = 0
                        chars_to_remove = 0
                break
        else:
            # Reached a math element or other non-run block, stop searching
            break

    # Retain non-empty runs or non-run elements (e.g. oMath)
    result = []
    for elem in elements:
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag == "r":
            t_elems = elem.findall(qn("w:t"))
            all_t = "".join(t.text or "" for t in t_elems)
            if all_t != "":
                result.append(elem)
        else:
            result.append(elem)

    return serialize_oxml_elements(result)

def strip_elements_suffix(xml_strings: list[str], pattern: str) -> tuple[list[str], str]:
    """
    Truncates XML runs at the start of a regex match (e.g. 'Đáp án:', 'Hướng dẫn chấm:')
    and returns (clean_xml_strings, extracted_matched_text).
    Guarantees answers/grading rubrics are never included in student exam questions.
    """
    if not xml_strings:
        return [], ""
    elements = deserialize_oxml_elements(xml_strings)
    
    full_text = ""
    spans = []
    for elem in elements:
        t_nodes = elem.findall(".//" + qn("w:t"))
        txt = "".join(t.text or "" for t in t_nodes)
        m_nodes = elem.findall(".//" + qn("m:t"))
        txt += "".join(m.text or "" for m in m_nodes)
        
        start = len(full_text)
        full_text += txt
        end = len(full_text)
        spans.append((start, end, elem, t_nodes))
        
    m = re.search(pattern, full_text, re.IGNORECASE)
    if not m:
        return xml_strings, ""
        
    cut_pos = m.start()
    matched_text = full_text[cut_pos:]
    
    kept_elements = []
    for start, end, elem, t_nodes in spans:
        if end <= cut_pos:
            kept_elements.append(elem)
        elif start < cut_pos < end:
            offset_in_elem = cut_pos - start
            rem = offset_in_elem
            for t in t_nodes:
                cur_len = len(t.text or "")
                if rem >= cur_len:
                    rem -= cur_len
                else:
                    t.text = (t.text or "")[:rem]
                    rem = 0
            kept_elements.append(elem)
        else:
            pass
            
    return serialize_oxml_elements(kept_elements), matched_text

