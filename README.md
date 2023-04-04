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