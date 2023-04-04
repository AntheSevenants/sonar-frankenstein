import pandas as pd
import argparse
import time
import re
import os
import html
import json
import concurrent.futures

from pathlib import Path
from tqdm.auto import tqdm
from flashtext import KeywordProcessor

from corpus2alpino.converter import Converter
from corpus2alpino.annotators.alpino import AlpinoAnnotator
from corpus2alpino.collectors.filesystem import FilesystemCollector
from corpus2alpino.targets.memory import MemoryTarget
from corpus2alpino.writers.lassy import LassyWriter

#
# Argument parsing
#

parser = argparse.ArgumentParser(
    description='alpino-parse-missing - parse Alpino sentences from a CSV list')
parser.add_argument('alpino_csv', type=str,
                    help='Path to the CSV containing sentences to parse')
parser.add_argument('sonar_500_split_treebank_path', type=str,
                    help='Path to the SONAR500 split SONAR500 treebank directory')
parser.add_argument('sonar_500_output_path', type=str,
                    help='Path to the SONAR500 split SONAR500 treebank directory')
parser.add_argument('closed_items_path', type=str,
					help='Path to the JSON file containing the closed items which will narrow down the search space')

args = parser.parse_args()

# Start the performance counter
t1 = time.perf_counter()

df = pd.read_csv(args.alpino_csv, dtype={'document': str})

sentence_re = re.compile(">(.*)<\/")

# We use the "closed items" class as a way to narrow down the search space
with open(args.closed_items_path, "rt") as reader:
    closed_class_items = json.loads(reader.read())

# Keyword processor
keyword_processor = KeywordProcessor()
keyword_processor.add_keywords_from_dict(closed_class_items)

def parse_sentence(subcorpus, document, sentence_id, alpino_instance):
    sentence_path = f"{args.sonar_500_split_treebank_path}/{subcorpus}/{document}/{sentence_id}.xml"
    sentence_path = Path(sentence_path)
    
    output_dir = f"{args.sonar_500_output_path}/{subcorpus}/{document}/"
    output_file = f"{output_dir}/{sentence_id}.xml"

    if os.path.exists(output_file):
        # Already parsed
        return True

    with sentence_path.open("rt") as reader:
        # Go over each line (this is still faster than XML parsing)
        for line in reader:
            if line.startswith("  <sentence"):
                if match := sentence_re.search(line):
                    sentence = match.group(1)

                    if len(sentence) > 9800:
                        print("Skipping this spam")
                        return True
                    
                    # Needed because special characters are encoded
                    sentence = html.unescape(sentence)

                    if len(keyword_processor.extract_keywords(line)) == 0:
                        return True

                    temp_file = f"temp_{alpino_instance}.txt"

                    with open(temp_file, "wt") as writer:
                        writer.write(sentence)

                    os.makedirs(output_dir, exist_ok=True)

                    #print(sentence)

                    alpino = AlpinoAnnotator("192.168.0.72", 7000 + alpino_instance)

                    converter = Converter(FilesystemCollector([temp_file]),
                                          # Not needed when using the PaQuWriter
                                          annotators=[alpino],
                                          # This can also be ConsoleTarget, FilesystemTarget
                                          target=MemoryTarget(),
                                          # Set to merge treebanks, also possible to use PaQuWriter
                                          writer=LassyWriter(False))

                    # get the Alpino XML output, combined into one treebank XML file
                    parses = converter.convert()

                    output = ''.join(parses)
                    output = output.replace("sentid=\"0-0\"",
                                            f"sentid=\"{subcorpus}-{document}.{sentence_id}\"")

                    with open(output_file, "wt") as writer:
                        writer.write(output)

                    return True
                
    return True


    
# Register a tqdm progress bar
progress_bar = tqdm(total=len(df), desc='Sentences processed')

with concurrent.futures.ProcessPoolExecutor() as executor:
    futures = []
    alpino_instance = 1
    for index, row in df.iterrows():
        if alpino_instance == 9:
            alpino_instance = 1

        # For each file, spawn a new process
        futures.append(executor.submit(parse_sentence, row["subcorpus"], row["document"], row["sentence"], alpino_instance))

        alpino_instance += 1
    # Start a processing pool

    # Loop over future results as they become available
    for future in concurrent.futures.as_completed(futures):
        progress_bar.update(n=1)  # Increments counter
        # Unpack the tuple
        #future.result()

t2 = time.perf_counter()

print(f'Finished in {t2-t1} seconds')
