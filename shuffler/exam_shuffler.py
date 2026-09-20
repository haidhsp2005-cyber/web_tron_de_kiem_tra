import random
from copy import deepcopy

class ExamShuffler:
    def __init__(self, exam_data: dict, config: dict = None):
        self.exam_data = deepcopy(exam_data)
        self.config = config or {}
        
        self.num_variants = int(self.config.get("num_variants", 4))
        self.variant_codes = self._generate_variant_codes()
        
        self.shuffle_p1_questions = self.config.get("shuffle_p1_questions", True)
        self.shuffle_p1_choices = self.config.get("shuffle_p1_choices", True)
        self.shuffle_p2_questions = self.config.get("shuffle_p2_questions", True)
        self.shuffle_p2_items = self.config.get("shuffle_p2_items", True)
        self.shuffle_p3_questions = self.config.get("shuffle_p3_questions", True)
        self.shuffle_p4_questions = self.config.get("shuffle_p4_questions", False)

    def _generate_variant_codes(self) -> list[str]:
        codes = self.config.get("variant_codes")
        if codes and isinstance(codes, list) and len(codes) >= self.num_variants:
            return [str(c).strip() for c in codes[:self.num_variants]]
        
        prefix = self.config.get("code_prefix", "")
        if prefix:
            return [f"{prefix}{i+1:02d}" for i in range(self.num_variants)]
        
        # Standard default: 101, 102, 103, 104... or 201, 202...
        start_code = int(self.config.get("start_code", 101))
        return [str(start_code + i) for i in range(self.num_variants)]

    def shuffle(self) -> dict:
        """
        Executes shuffling for all specified variants.
        Returns generated variants and summary matrices.
        """
        variants = []
        
        for code in self.variant_codes:
            variant = self._generate_single_variant(code)
            variants.append(variant)
            
        summary = self._build_summary_matrices(variants)
        
        return {
            "metadata": self.exam_data.get("metadata", {}),
            "variants": variants,
            "summary": summary
        }

    def _generate_single_variant(self, code: str) -> dict:
        variant = {
            "code": code,
            "metadata": deepcopy(self.exam_data.get("metadata", {})),
            "part1": [],
            "part2": [],
            "part3": [],
            "part4": []
        }
        variant["metadata"]["code"] = code

        # ----------------- PART I -----------------
        p1_pool = deepcopy(self.exam_data.get("part1", []))
        if self.shuffle_p1_questions and len(p1_pool) > 1:
            random.shuffle(p1_pool)

        for new_idx, q in enumerate(p1_pool, start=1):
            original_correct = q.get("correct", "A")
            original_choices = q.get("choices", {})
            choice_keys = ["A", "B", "C", "D"]
            
            # Map choice xmls if present
            orig_choice_xmls = q.get("choice_xmls", {})

            if self.shuffle_p1_choices:
                # Randomly permute the choice keys
                shuffled_keys = list(choice_keys)
                random.shuffle(shuffled_keys)
                
                new_choices = {}
                new_choice_xmls = {}
                new_correct = "A"
                
                for new_key, orig_key in zip(choice_keys, shuffled_keys):
                    new_choices[new_key] = original_choices.get(orig_key, "")
                    if orig_choice_xmls:
                        new_choice_xmls[new_key] = orig_choice_xmls.get(orig_key, [])
                    if orig_key == original_correct:
                        new_correct = new_key
            else:
                new_choices = deepcopy(original_choices)
                new_choice_xmls = deepcopy(orig_choice_xmls)
                new_correct = original_correct

            variant["part1"].append({
                "num": new_idx,
                "original_id": q.get("id"),
                "original_num": q.get("original_num", new_idx),
                "question": q.get("question", ""),
                "choices": new_choices,
                "choice_xmls": new_choice_xmls,
                "correct": new_correct,
                "xml_strings": q.get("xml_strings", [])
            })

        # ----------------- PART II -----------------
        p2_pool = deepcopy(self.exam_data.get("part2", []))
        if self.shuffle_p2_questions and len(p2_pool) > 1:
            random.shuffle(p2_pool)

        for new_idx, q in enumerate(p2_pool, start=1):
            item_keys = ["a", "b", "c", "d"]
            orig_items = q.get("items", {})

            if self.shuffle_p2_items:
                shuffled_keys = list(item_keys)
                random.shuffle(shuffled_keys)
                new_items = {}
                for new_k, orig_k in zip(item_keys, shuffled_keys):
                    new_items[new_k] = deepcopy(orig_items.get(orig_k, {"text": "", "correct": False}))
            else:
                new_items = deepcopy(orig_items)

            variant["part2"].append({
                "num": new_idx,
                "original_id": q.get("id"),
                "original_num": q.get("original_num", new_idx),
                "question": q.get("question", ""),
                "items": new_items,
                "xml_strings": q.get("xml_strings", [])
            })

        # ----------------- PART III -----------------
        p3_pool = deepcopy(self.exam_data.get("part3", []))
        if self.shuffle_p3_questions and len(p3_pool) > 1:
            random.shuffle(p3_pool)

        for new_idx, q in enumerate(p3_pool, start=1):
            variant["part3"].append({
                "num": new_idx,
                "original_id": q.get("id"),
                "original_num": q.get("original_num", new_idx),
                "question": q.get("question", ""),
                "answer": q.get("answer", ""),
                "xml_strings": q.get("xml_strings", [])
            })

        # ----------------- PART IV -----------------
        p4_pool = deepcopy(self.exam_data.get("part4", []))
        if self.shuffle_p4_questions and len(p4_pool) > 1:
            random.shuffle(p4_pool)

        for new_idx, q in enumerate(p4_pool, start=1):
            variant["part4"].append({
                "num": new_idx,
                "original_id": q.get("id"),
                "original_num": q.get("original_num", new_idx),
                "question": q.get("question", ""),
                "guide": q.get("guide", ""),
                "xml_strings": q.get("xml_strings", [])
            })

        return variant

    def _build_summary_matrices(self, variants: list[dict]) -> dict:
        """
        Builds matrix tables for all 4 parts across all generated variants.
        """
        codes = [v["code"] for v in variants]
        
        # --- PART I MATRIX ---
        p1_count = len(variants[0]["part1"]) if variants and variants[0]["part1"] else 0
        # Rows = Question numbers 1..p1_count, Columns = codes
        p1_matrix_rows = []
        for q_idx in range(p1_count):
            row = {"question_num": q_idx + 1}
            for v in variants:
                q = v["part1"][q_idx]
                row[v["code"]] = q["correct"]
            p1_matrix_rows.append(row)

        # Code-by-code answers array: { "101": ["A", "B", ...], ... }
        p1_by_code = {}
        for v in variants:
            p1_by_code[v["code"]] = [q["correct"] for q in v["part1"]]

        # --- PART II MATRIX ---
        # Rows = Câu 1 - a, Câu 1 - b, Câu 1 - c, Câu 1 - d...
        p2_count = len(variants[0]["part2"]) if variants and variants[0]["part2"] else 0
        p2_matrix_rows = []
        for q_idx in range(p2_count):
            for item_k in ["a", "b", "c", "d"]:
                row = {
                    "question_num": q_idx + 1,
                    "item_key": item_k,
                    "label": f"Câu {q_idx + 1}.{item_k}"
                }
                for v in variants:
                    q = v["part2"][q_idx]
                    is_true = q["items"].get(item_k, {}).get("correct", False)
                    row[v["code"]] = "Đ" if is_true else "S"
                p2_matrix_rows.append(row)

        p2_by_code = {}
        for v in variants:
            code_items = {}
            for q in v["part2"]:
                code_items[q["num"]] = {
                    k: ("Đ" if item.get("correct") else "S")
                    for k, item in q["items"].items()
                }
            p2_by_code[v["code"]] = code_items

        # --- PART III MATRIX ---
        p3_count = len(variants[0]["part3"]) if variants and variants[0]["part3"] else 0
        p3_matrix_rows = []
        for q_idx in range(p3_count):
            row = {"question_num": q_idx + 1}
            for v in variants:
                q = v["part3"][q_idx]
                row[v["code"]] = q["answer"]
            p3_matrix_rows.append(row)

        p3_by_code = {}
        for v in variants:
            p3_by_code[v["code"]] = [q["answer"] for q in v["part3"]]

        # --- PART IV MATRIX ---
        p4_count = len(variants[0]["part4"]) if variants and variants[0]["part4"] else 0
        p4_matrix_rows = []
        for q_idx in range(p4_count):
            row = {"question_num": q_idx + 1}
            for v in variants:
                q = v["part4"][q_idx]
                row[v["code"]] = {
                    "question": q["question"],
                    "guide": q["guide"]
                }
            p4_matrix_rows.append(row)

        return {
            "codes": codes,
            "part1": {
                "rows": p1_matrix_rows,
                "by_code": p1_by_code
            },
            "part2": {
                "rows": p2_matrix_rows,
                "by_code": p2_by_code
            },
            "part3": {
                "rows": p3_matrix_rows,
                "by_code": p3_by_code
            },
            "part4": {
                "rows": p4_matrix_rows
            }
        }
