import os
import zipfile

class ZipExporter:
    def __init__(self, items: list, output_zip_path: str = "exports/Bo_de_thi_tron.zip"):
        """
        items can be:
        - list of file paths (str)
        - list of tuples: (file_path, arcname)
        """
        self.items = items
        self.output_zip_path = output_zip_path
        os.makedirs(os.path.dirname(output_zip_path), exist_ok=True)

    def create_zip(self) -> str:
        with zipfile.ZipFile(self.output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for item in self.items:
                if isinstance(item, tuple):
                    file_path, arcname = item
                else:
                    file_path = item
                    base = os.path.basename(file_path)
                    if base.startswith("De_thi_"):
                        arcname = f"De_thi_Hoc_sinh/{base}"
                    else:
                        arcname = f"Dap_an_Giao_vien/{base}"
                if os.path.exists(file_path):
                    zipf.write(file_path, arcname=arcname)
        return self.output_zip_path
