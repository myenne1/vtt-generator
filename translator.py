import os
import re
import argparse
import time
from argostranslate import package, translate
from logger_util import LogWriter
from seeding import create_timestamped_folder

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
    start_time = time.time()
    output_folder = create_timestamped_folder()
    os.makedirs(output_folder, exist_ok=True)
    
    # Setup logging
    log_path = os.path.join(output_folder, "log.txt")
    logger = LogWriter(log_path)
    logger.write(f"Batch translation started at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.write(f"Input folder: {input_folder}")
    logger.write(f"Output folder: {output_folder}\n")
    
    vtt_files = [f for f in os.listdir(input_folder) if f.endswith(".vtt")]
    total_files = len(vtt_files)

    success_count = 0
    fail_count = 0
    failed_files = []
    
    if total_files == 0:
        print("No VTT files found in the input folder.")
        return
    
    for i, filename in enumerate(vtt_files):
        input_file = os.path.join(input_folder, filename)
        base_name = os.path.splitext(filename)[0]
        output_file = os.path.join(output_folder, f"{base_name}_es.vtt")
        
        msg = f"\nTranslating: {filename} → {base_name}_es.vtt ({total_files - i} file(s) left)"
        print(msg)
        logger.write(msg)
        try:
            translate_vtt_file(input_file, output_file)
            success_count += 1
            logger.write(f"Successfully translated: {filename}")
        except Exception as e:
            print(f"Failed to translate {filename}: {e}")
            error_msg = f"Failed to translate {filename}: {e}"
            print(error_msg)
            logger.write(error_msg)
            fail_count += 1
            failed_files.append(filename)

    print("\nTranslation Summary:")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {fail_count}")
    logger.write("\nTranslation Summary:")
    logger.write(f"  Successful: {success_count}")
    logger.write(f"  Failed: {fail_count}")
    if failed_files:
        print("  Failed files:")
        logger.write("  Failed files:")
        for f in failed_files:
            print(f"    - {f}")
            logger.write(f"    - {f}")
            
    elapsed_time = time.time() - start_time
    logger.write(f"\nTotal time taken: {elapsed_time / 60:.2f} minutes")
    print(f"\nTotal time taken: {elapsed_time / 60:.2f} minutes")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Translate all VTT files in a folder from English to Spanish.")
    parser.add_argument("--input", required=True, help="Path to folder containing English VTT files")
    args = parser.parse_args()

    batch_translate_vtts(args.input)