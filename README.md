# sonar-frankenstein
How I built a SoNaR treebank

If you download [SoNaR](https://taalmaterialen.ivdnt.org/download/tstc-sonar-corpus/), a text corpus of Dutch consisting of more than 500 million words, you will immediately notice that the corpus does not ship with syntactic annotations (a so-called "treebank"). If you want to do research on morphosyntactic alternations, this is a big problem.

The reasoning behind this exclusion is that the SoNaR corpus is already included in [Lassy Groot](https://taalmaterialen.ivdnt.org/download/tstc-lassy-groot-corpus/), another corpus for Dutch. Lassy Groot *does* feature syntactic annotations, parsed by the [Alpino parser](https://www.let.rug.nl/vannoord/alp/Alpino/). This means that, in theory, if you need SoNaR syntactic data, you can 'borrow' it from Lassy Groot.

There are two issues with this approach:
1. It is unclear which parts in Lassy come from SoNaR. According to the Lassy webpage, the corpus actually contains several other corpora as well:
    - Eindhoven corpus. 40 thousand sentences, 713 thousand tokens.
    - EMEA corpus. Over 1 million sentences, 13 million tokens.
    - Europarl corpus. Over 1 million sentences, 37 million tokens.
    - Wikipedia dump of 2011. 9 million sentences, 145 million tokens.
    - Senseval corpus of Dutch. 12 thousand sentences, 156 thousand tokens.
    - _SONAR500 corpus. 41 million sentences, 510 million tokens._
    - Small corpus including the annual "Troonrede" of Queen Beatrix since 1990.

    Lassy's structure, however, is unmistakingly SoNaR's. The subcorpora are named after SoNaR parts, and there are no separations between the SoNaR material and other content. In practice, then, fetching a treebank from Lassy does not guarantee that the corpus material you use is homogenously SoNaR. This, in turn, is problematic for reproducability.
2. Not _all_ parts from SoNaR are included in Lassy. The [SoNaR New Media Corpus](https://taalmaterialen.ivdnt.org/download/tstc-sonar-nieuwe-media-corpus-1/) in particular was never added to Lassy. Other material missing from Lassy includes magazines and subtitles.

I found a version of SoNaR, fully parsed with Alpino, on KU Leuven servers. Unfortunately, this version was parsed using an older version of Alpino (1.3), which means the annotations are of poor quality. The same sentences in *Lassy*, on the other hand, were parsed using a more recent version of Alpino (1.5) and were parsed correctly.

My idea, then, was to take the sentences shared by SoNaR and Lassy from the Lassy Groot corpus (= the *good* parses) to bootstrap a 'sound' basis for a SoNaR treebank. The remaining sentences (those not found in Lassy) would be parsed using a recent version of Alpino in order to complete the treebank.

## Step 1: Split the SoNaR treebank into separate files

Alpino treebanks by default come in large files with multiple sentences. Each sentence is an XML file, and multiple XML files are concatenated together in chunks of around ~ 40 MB. Given how slow IO operations can be in Windows, this is good design, because it means you can open one file and begin to read thousands of sentences immediately within that same file.

For my purpose, however, it was best to split up individual sentences into individual files. With each sentence in a separate file, I could overwrite a sentence by itself without having to rewrite the entire chunk it belongs to, or without keeping it in memory. Since I would be copying individual sentences from Lassy Groot to SoNaR, this one-by-one replacement mechanism was vital.

## Step 2: Copy sentences from Lassy Groot to SoNaR

With all sentences split, I could start copying material from Lassy Groot to SoNaR. The program I wrote followed this logic:

* Open each chunk in the Lassy Groot corpus
* Check for each sentence in the chunk whether it exists in SoNaR
    * If it exists, overwrite the parse of that sentence with the Lassy parse

## Step 3: Find remaining old sentences

With all overlapping sentences copied, it was time to find the sentences which were *not* replaced by better parses. I did this simply by checking the Alpino version in the parse of each sentence. This yielded several CSV files with subcorpora, document ids and sentence ids for the remaining sentences.

## Step 4: Parsing remaining sentences

To parse the remaining sentences, I used my own [alpino-server Docker container](https://github.com/AntheSevenants/alpino-server). To accelerate the parses, I ran several Docker containers in parallel.

## Step 5: Putting everything together

I copied the parses of the remaining sentences to the 'original' split SoNaR corpus. Then, I concatenated the sentences of each subcorpus in groups of 10,000 sentences to obtain workable files. This finally resulted in a fully Alpino-parsed and complete SoNaR corpus.