import sys
sys.stdout.reconfigure(encoding='utf-8')
from parser.docx_parser import DocxParser
from shuffler.exam_shuffler import ExamShuffler
from exporter.docx_exporter import DocxExporter
from exporter.excel_exporter import ExcelExporter
from exporter.zip_exporter import ZipExporter

print("1. Parsing sample docx...")
p = DocxParser('samples/de_thi_mau_chuan.docx')
parsed = p.parse()
print("   Parsed total questions:", parsed['stats']['total_questions'])

print("2. Shuffling exam into 4 variants...")
shuffler = ExamShuffler(parsed, {'num_variants': 4, 'start_code': 101})
result = shuffler.shuffle()
print("   Variants generated:", [v['code'] for v in result['variants']])

print("3. Exporting DOCX files...")
docx_exp = DocxExporter(result, output_dir='exports')
exported_docx = docx_exp.export_all()
print("   Exam files:", len(exported_docx['test_files']))
print("   Key files:", len(exported_docx['key_files']))
print("   Summary DOCX:", exported_docx['summary_file'])

print("4. Exporting Excel matrix...")
excel_exp = ExcelExporter(result, output_path='exports/Bang_dap_an_tong_hop.xlsx')
excel_file = excel_exp.export()
print("   Excel file:", excel_file)

print("5. Creating ZIP package...")
all_files = exported_docx['test_files'] + exported_docx['key_files'] + [exported_docx['summary_file'], excel_file]
zip_exp = ZipExporter(all_files, output_zip_path='exports/Bo_de_thi_tron.zip')
zip_file = zip_exp.create_zip()
print("   ZIP created:", zip_file)
print("ALL EXPORT PIPELINE TESTS PASSED!")
