import os
import re
import argparse
from argostranslate import package, translate

# Download and install English-Spanish package if not present
available_packages = package.get_available_packages()
en_es_package = next((pkg for pkg in available_packages if pkg.from_code == "en" and pkg.to_code == "es"), None)
if en_es_package:
    package.install_from_path(en_es_package.download())
    
    
# Setup Argos Translate: English → Spanish
langs = translate.get_installed_languages()
en = next(lang for lang in langs if lang.code == "en")
es = next(lang for lang in langs if lang.code == "es")
translator = en.get_translation(es)

def translate_vtt_file(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    translated_lines = []
    for line in lines:
        if re.match(r"\d{2}:\d{2}:\d{2}\.\d{3} -->", line) or line.strip() == "" or "WEBVTT" in line:
            translated_lines.append(line)
        else:
            translated_text = translator.translate(line.strip())
            translated_lines.append(translated_text + "\n")

    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(translated_lines)

def batch_translate_vtts(input_folder):
    output_folder = "output"
    os.makedirs(output_folder, exist_ok=True)
    
    vtt_files = [f for f in os.listdir(input_folder) if f.endswith(".vtt")]
    total_files = len(vtt_files)

    for i, filename in enumerate(vtt_files):
        input_file = os.path.join(input_folder, filename)
        base_name = os.path.splitext(filename)[0]
        output_file = os.path.join(output_folder, f"{base_name}_es.vtt")
        
        print(f"Translating: {filename} → {base_name}_es.vtt ({total_files - i} file(s) left)")
        translate_vtt_file(input_file, output_file)
            

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Translate all VTT files in a folder from English to Spanish.")
    parser.add_argument("--input", required=True, help="Path to folder containing English VTT files")
    args = parser.parse_args()

    batch_translate_vtts(args.input)