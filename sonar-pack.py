import argparse
import re
import time
import concurrent.futures
import os.path

from pathlib import Path
from tqdm.auto import tqdm
from glob import glob

parser = argparse.ArgumentParser(
    description='sonar-pack - pack SoNaR corpus into larger files')
parser.add_argument('sonar_treebank_source_path', type=str,
                    help='Path to the SoNaR Treebank directory')
parser.add_argument('sonar_treebank_destination_path', type=str,
                    help='Path to the where packed SoNaR Treebank directory should be stored')
args = parser.parse_args()

if not os.path.exists(args.sonar_treebank_source_path):
    raise FileNotFoundError("Sonar source directory does not exist")

if not os.path.exists(args.sonar_treebank_destination_path):
    raise FileNotFoundError("Output directory does not exist")

SENTENCES_PER_FILE = 10000

# Start the performance counter
t1 = time.perf_counter()

subcorpora = [ Path(subcorpus).stem for subcorpus in glob(f"{args.sonar_treebank_source_path}/*/") ]

def read_file(pfin):
    buf = []

    # Open the data file
    with pfin.open("rt") as reader:
        # Go over each line (this is still faster than XML parsing)    
        buffer_open = False
        for line in reader:
                # Open the buffer for writing when sentence opening tag has been found
                if line.startswith("<alpino_ds "):
                    buffer_open = True
                elif line.startswith("</alpino_ds"):
                    buf.append(line)

                    # Reset flags
                    buffer_open = False

                    return buf

                # Only add lines if the buffer is open
                if buffer_open:
                    buf.append(line)

def pack_subcorpus(subcorpus):
    files_counter = 1
    files_read = 0

    # Create the output directory first
    subcorpus_output_dir = f"{args.sonar_treebank_destination_path}/{subcorpus}/"
    os.makedirs(subcorpus_output_dir, exist_ok=True)

    # pad to seven digits

    # Find all subcorpus files which we need to pack
    subcorpus_files = list(Path(f"{args.sonar_treebank_source_path}/{subcorpus}/").rglob("*.xml"))

    # upper limit
    # for recovery, we check how many files have already been created
    # this gives us a clue to where we can restart the script
    test_index = 1
    while True:
        pack_id = str(test_index).zfill(7)
        output_filename = f"{subcorpus_output_dir}/{subcorpus}-{pack_id}.xml"
        if os.path.exists(output_filename):
            test_index += 1
        else:
            upper_limit = (test_index - 1) * SENTENCES_PER_FILE
            print(f"Upper limit for {subcorpus} is {upper_limit}")
            break

    pack_buffer = []
    for index, subcorpus_file in enumerate(subcorpus_files):
        if index + 1 <= upper_limit:
            continue

        # We read each file and get its contents
        file_buffer = read_file(Path(subcorpus_file))
        # Append the file buffer to the current buffer
        pack_buffer = pack_buffer + file_buffer
        files_read += 1

        # If total number of files is reached, write output file
        # Or, if at end of queue
        if files_read == SENTENCES_PER_FILE or len(subcorpus_files) == index + 1:
            # Add XML header
            pack_buffer = [ "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" ] + pack_buffer
            pack_id = str(files_counter).zfill(7)

            output_filename = f"{subcorpus_output_dir}/{subcorpus}-{pack_id}.xml"
            with open(output_filename, "wt") as writer:
                writer.write("".join(pack_buffer))

            # Increment files counter
            files_counter += 1
            # Reset files read
            files_read = 0

#progress_bar = tqdm(total=len(subcorpora), desc='Progress')
#for subcorpus in subcorpora:
#    pack_subcorpus(subcorpus)
#    progress_bar.update(n=1)  # Increments counter

# Register a tqdm progress bar
progress_bar = tqdm(total=len(subcorpora), desc='Progress')

## Start a processing pool
with concurrent.futures.ProcessPoolExecutor() as executor:
    # For each file, spawn a new process
    futures = [executor.submit(pack_subcorpus, subcorpus) for subcorpus in subcorpora]
    # Loop over future results as they become available
    for future in concurrent.futures.as_completed(futures):
        progress_bar.update(n=1)  # Increments counter
        future.result()

t2 = time.perf_counter()

print(f'Finished in {t2-t1} seconds')
