# Prepare for a wild ride

import time
import argparse
import re
import concurrent.futures
import os
import pandas as pd
import os

from pathlib import Path
from glob import glob
from tqdm.auto import tqdm

#
# Argument parsing
#

parser = argparse.ArgumentParser(
    description='check-version - check what version a treebank uses in LassyGroot')
parser.add_argument('sonar_500_split_treebank_path', type=str,
                    help='Path to the SONAR500 split SONAR500 treebank directory')
parser.add_argument('subcorpus', type=str,
                    help='Subcorpus to check')

args = parser.parse_args()

# Start the performance counter
t1 = time.perf_counter()

num_cores = os.cpu_count()

def get_subdirectories(directory):
    return [x.stem for x in Path(directory).iterdir() if x.is_dir()]

# Get all subcorpora in the parent directory
# subcorpora = get_subdirectories(args.sonar_500_split_treebank_path)
#subcorpora.sort()

alpino_version_re = re.compile("version=\"(.*?)\"")

def get_subdirectories(directory):
    return [x.stem for x in Path(directory).iterdir() if x.is_dir()]

def parse_documents(subcorpus_dir, subcorpus, documents):
    rows = []

    for document in documents:
        document_dir = f"{subcorpus_dir}/{document}/"
        sentences = glob(f"{document_dir}/*.xml")
        for sentence in sentences:
            sentence_path = Path(sentence)
            alpino_version = get_alpino_version(sentence_path)
            if alpino_version == "1.3":
                row = (subcorpus, document, sentence_path.stem)
                rows.append(row)

    return rows

def get_alpino_version(pfin):
    # Open the data file
    with pfin.open("rt") as reader:
        # Go over each line (this is still faster than XML parsing)
        for line in reader:
            if line.startswith("<alpino_ds "):
                if match := alpino_version_re.search(line):
                    return match.group(1)
                
        return "unk"

# https://stackoverflow.com/a/2135920
def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))

rows = []


for subcorpus in [ args.subcorpus ]:
    subcorpus_dir = f"{args.sonar_500_split_treebank_path}/{subcorpus}/"
    documents = get_subdirectories(subcorpus_dir)

    # Register a tqdm progress bar
    progress_bar = tqdm(total=len(documents), desc='Documents processed', leave=True)

    # Start a processing pool
    with concurrent.futures.ProcessPoolExecutor() as executor:
        # For each file, spawn a new process
        futures = [executor.submit(parse_documents, subcorpus_dir, subcorpus, [document]) for document in documents]
        # Loop over future results as they become available
        for future in concurrent.futures.as_completed(futures):
            progress_bar.update(n=1)  # Increments counter
            # Unpack the tuple
            inner_rows = future.result()

            rows = rows + inner_rows

    #for document_dir in Path(subcorpus_dir).iterdir():
    #    if not document_dir.is_dir():
    #        continue

# Create a data frame from the results
df = pd.DataFrame(rows, columns=["subcorpus", "document", "sentence"])
df = df.sort_values("subcorpus")

df.to_csv(f"output/{args.subcorpus}.csv", index=None)

t2 = time.perf_counter()

print(f'Finished in {t2-t1} seconds')