import argparse
import re
import time
import concurrent.futures
import os.path

from pathlib import Path
from tqdm.auto import tqdm

parser = argparse.ArgumentParser(
    description='sonar-overwrite - copy correct parses from LassyGroot to SoNaR Treebank')
parser.add_argument('lassy_groot_data_path', type=str,
                    help='Path to the LassyGroot data directory')
parser.add_argument('sonar_treebank_output_path', type=str,
                    help='Path to the SoNaR Treebank directory')
args = parser.parse_args()

if not os.path.exists(args.lassy_groot_data_path):
    raise FileNotFoundError("LassyGroot directory does not exist")

if not os.path.exists(args.sonar_treebank_output_path):
    raise FileNotFoundError("Output directory does not exist")

# Start the performance counter
t1 = time.perf_counter()

data_files = list(Path(args.lassy_groot_data_path).rglob("*.data"))

print("Found", len(data_files), "data files")

# Surprise! There's no need to actually parse the XML files.
# The structure is always exactly the same, so pardon my regular expression heresy
id_re = re.compile("id=\"([A-Za-z-]+)-(\d+)\.(.*?)\"")

def write_file(pfin):
    buf = []

    # Open the data file
    with pfin.open("rt") as reader:
        # Go over each line (this is still faster than XML parsing)    
        should_copy = False
        buffer_open = False
        for line in reader:
                # Open the buffer for writing when sentence opening tag has been found
                if line.startswith("<alpino_ds "):
                    buffer_open = True
                elif line.startswith("  <sentence"):
                    # Look for the sentence ID in this sentence
                    # And extract the document ID from it
                    if match := id_re.search(line):
                        corpus = match.group(1)
                        doc_id = match.group(2)
                        sent_id = match.group(3)
                    else:
                        # Sentence has no valid SoNaR sentence ID...
                        # Tough luck!
                        # We disable adding to buffer because this file is useless anyway
                        buffer_open = False
                        continue

                    # We compose the filename of the SoNaR treebank single file
                    corpus_dir = f"{args.sonar_treebank_output_path}/{corpus}/"
                    doc_dir = f"{corpus_dir}/{doc_id}/"
                    sent_file = f"{doc_dir}/{sent_id}.xml"

                    # Whether the file should be overwritten is dependent on whether it exists
                    # Because Lassy Groot has a better parse, if possible, we will always overwrite
                    should_copy = os.path.exists(sent_file)
                # Close the buffer when closing tag is found
                # In addition, parse the current buffer and get its hits (if allowed)
                elif line.startswith("</alpino_ds"):
                    buf.append(line)

                    # If parsing allowed, write to the sentence file
                    if should_copy:
                        with open(sent_file, "wt") as writer:
                            writer.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" + "".join(buf))

                    # Reset flags
                    buffer_open = False
                    should_copy = False
                    
                    # Reset buffer
                    buf = []

                # Only add lines if the buffer is open
                if buffer_open:
                    buf.append(line)

# Register a tqdm progress bar
progress_bar = tqdm(total=len(data_files), desc='Progress')

data = []

# Start a processing pool
with concurrent.futures.ProcessPoolExecutor() as executor:
    # For each file, spawn a new process
    futures = [executor.submit(write_file, file) for file in data_files]
    # Loop over future results as they become available
    for future in concurrent.futures.as_completed(futures):
        progress_bar.update(n=1)  # Increments counter
        future.result()

t2 = time.perf_counter()

print(f'Finished in {t2-t1} seconds')
