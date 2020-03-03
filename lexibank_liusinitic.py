from __future__ import unicode_literals, print_function
from collections import OrderedDict, defaultdict

import attr
from clldutils.misc import slug
from pathlib import Path
from pylexibank.forms import FormSpec
from pylexibank import Dataset as BaseDataset
from pylexibank import Concept, Language
from pylexibank.util import progressbar

from lingpy import *

@attr.s
class CustomConcept(Concept):
    Chinese_Gloss = attr.ib(default=None)

@attr.s
class CustomLanguage(Language):
    Latitude = attr.ib(default=None)
    Longitude = attr.ib(default=None)
    ChineseName = attr.ib(default=None)
    SubGroup = attr.ib(default='Sinitic')
    Family = attr.ib(default='Sino-Tibetan')
    Source_ID = attr.ib(default=None)
    DialectGroup = attr.ib(default=None)
    Pinyin = attr.ib(default=None)
    AltName = attr.ib(default=None)


class Dataset(BaseDataset):
    id = 'liusinitic'
    dir = Path(__file__).parent
    concept_class = CustomConcept
    language_class = CustomLanguage

    def cmd_makecldf(self, args):
        # add source
        args.writer.add_sources()
        # read in data
        ds = self.raw_dir / "words-new.tsv"
        wl = Wordlist(ds.as_posix())
        # add languages
        languages = args.writer.add_languages(lookup_factory="Name")
        # add concepts
        concepts = {}
        for concept in self.conceptlists[0].concepts.values():
            args.writer.add_concept(
                ID=concept.id,
                Name=concept.english,
                Chinese_Gloss=concept.attributes["chinese"],
                Concepticon_ID=concept.concepticon_id,
                Concepticon_Gloss=concept.concepticon_gloss)
            concepts[concept.english] = concept.id
        # add the concepts which appear in the word list but do not appear in the concepticon list.
        concepts['heart [compound]'] = 'Liu-2007-201-158'
        concepts['river_2'] = 'Liu-2007-201-50'
        concepts['river'] = 'Liu-2007-201-49'
         # add forms
        for idx in progressbar(wl, desc="cldfify the data"):
            cogid = idx
            if wl[idx, "concept"]:
                args.writer.add_form_with_segments(
                    Language_ID=languages[wl[idx, "doculect"]],
                    Parameter_ID=concepts[wl[idx, "concept"]],
                    Value=wl[idx, "value"],
                    Form=wl[idx,"value"],
                    Segments=wl[idx,"segments"],
                    Source=['Liu2007']
                )
