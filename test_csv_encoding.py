import pandas as pd
import ftfy
import sys
import chardet
import codecs
from datetime import datetime
import csv

# Configuration de l'encodage pour Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def fix_text_encoding(text):
    """
    Corrige l'encodage du texte en utilisant plusieurs méthodes.
    """
    if not text:
        return text

    # Méthode 1: UTF-8 -> Latin1 -> UTF-8
    try:
        fixed_text = text.encode('latin1').decode('utf-8')
        if fixed_text != text:
            return fixed_text
    except Exception:
        pass

    # Méthode 2: Utiliser ftfy
    try:
        fixed_text = ftfy.fix_text(text)
        if fixed_text != text:
            return fixed_text
    except Exception:
        pass

    # Méthode 3: CP1252 -> UTF-8
    try:
        fixed_text = text.encode('cp1252').decode('utf-8')
        if fixed_text != text:
            return fixed_text
    except Exception:
        pass

    return text

def detect_encoding(file_path):
    """Détecte l'encodage d'un fichier"""
    try:
        with open(file_path, 'rb') as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            return result['encoding']
    except Exception:
        return 'utf-8'

def process_csv_file(input_file, output_file=None):
    """
    Traite un fichier CSV pour corriger les problèmes d'encodage.
    """
    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'output_{timestamp}.txt'

    # Détection de l'encodage
    encoding = detect_encoding(input_file)
    print(f"Encodage détecté: {encoding}")

    try:
        # Lecture du fichier CSV avec pandas
        df = pd.read_csv(input_file, encoding=encoding)
        
        # Appliquer la correction d'encodage à chaque colonne de type string
        for column in df.select_dtypes(include=['object']).columns:
            df[column] = df[column].apply(lambda x: fix_text_encoding(str(x)) if pd.notnull(x) else x)
        
        # Sauvegarder le fichier corrigé
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"Fichier sauvegardé: {output_file}")
        return True
        
    except Exception as e:
        print(f"Erreur lors du traitement du fichier: {str(e)}")
        
        # Essayer une approche ligne par ligne si pandas échoue
        try:
            with codecs.open(input_file, 'r', encoding=encoding) as f_in, \
                 codecs.open(output_file, 'w', encoding='utf-8-sig', newline='') as f_out:
                
                csv_reader = csv.reader(f_in)
                csv_writer = csv.writer(f_out)
                
                for row in csv_reader:
                    fixed_row = [fix_text_encoding(str(cell)) for cell in row]
                    csv_writer.writerow(fixed_row)
                
                print(f"Fichier sauvegardé (méthode alternative): {output_file}")
                return True
                
        except Exception as e2:
            print(f"Erreur lors du traitement alternatif: {str(e2)}")
            return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python script.py input_file [output_file]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    process_csv_file(input_file, output_file)
