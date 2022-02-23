from collections import defaultdict
from pathlib import Path

import attr
import lingpy
import pylexibank


def check_entry(wordlist, index, errors=defaultdict(list)):
    prosody = lingpy.basictypes.lists(wordlist[index, "structure"])
    morphemes = lingpy.basictypes.strings(wordlist[index, "morphemes"])
    tokens = lingpy.basictypes.lists(wordlist[index, "tokens"])
    cogids = lingpy.basictypes.ints(wordlist[index, "cogids"])

    if len(prosody.n) != len(tokens.n):
        errors[index] += ["prostring"]
        print(prosody, tokens)
    if len(morphemes) != len(tokens.n):
        errors[index] += ["morphemes"]
    if len(cogids) != len(tokens.n):
        errors[index] += ["cogids-{0}".format(str(wordlist[index, "cogids"]))]
    for i, (p, t) in enumerate(zip(prosody.n, tokens.n)):
        if len(p) != len(t):
            errors[index] += [
                "prostring-{1}-{2}-{0}".format(
                    i, wordlist[index, "doculect"], wordlist[index, "concept"]
                )
            ]
    return errors


@attr.s
class CustomLexeme(pylexibank.Lexeme):
    Prosody = attr.ib(default="")
    Morphemes = attr.ib(default=None)


@attr.s
class CustomConcept(pylexibank.Concept):
    Chinese_Gloss = attr.ib(default=None)


@attr.s
class CustomCognate(pylexibank.Cognate):
    Segment_Slice = attr.ib(default=None)


@attr.s
class CustomLanguage(pylexibank.Language):
    Latitude = attr.ib(default=None)
    Longitude = attr.ib(default=None)
    ChineseName = attr.ib(default=None)
    SubGroup = attr.ib(default="Sinitic")
    Family = attr.ib(default="Sino-Tibetan")
    Source_ID = attr.ib(default=None)
    DialectGroup = attr.ib(default=None)
    Pinyin = attr.ib(default=None)
    AltName = attr.ib(default=None)


class Dataset(pylexibank.Dataset):
    id = "liusinitic"
    dir = Path(__file__).parent
    concept_class = CustomConcept
    language_class = CustomLanguage
    lexeme_class = CustomLexeme
    cognate_class = CustomCognate
    cross_concept_cognates = True

    def cmd_download(self, args):
        print("updating ...")
        self.raw_dir.download(
            "https://lingulist.de/edictor/triples/get_data.py?file=liusinitic&remote_dbase=liusinitic.sqlite3&columns=DOCULECT|SUBGROUP|CONCEPT|VALUE|IPA|TOKENS|COGIDS|MORPHEMES|STRUCTURE|NOTE|CHARACTERS|CHARACTER_IS",
            "liusinitic.tsv",
        )

    def cmd_makecldf(self, args):
        # add source
        args.writer.add_sources()
        # read in data
        ds = self.raw_dir / "liusinitic.tsv"
        wl = lingpy.Wordlist(str(ds))

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
                Concepticon_Gloss=concept.concepticon_gloss,
            )
            concepts[concept.english] = concept.id
        # add the concepts which appear in the word list but do not appear in the concepticon list.
        concepts["heart [compound]"] = "Liu-2007-201-158"
        concepts["river_2"] = "Liu-2007-201-50"
        concepts["river"] = "Liu-2007-201-49"

        # add forms
        errors = defaultdict(list)
        for idx in pylexibank.progressbar(wl, desc="cldfify the data"):
            # check for mismatch in prosody
            check_entry(wl, idx, errors)
            lexeme = args.writer.add_form_with_segments(
                Language_ID=languages[wl[idx, "doculect"]],
                Parameter_ID=concepts[wl[idx, "concept"]],
                Value=wl[idx, "value"],
                Form=wl[idx, "value"],
                Segments=[y for y in [x.split("/")[0] for x in wl[idx, "tokens"]] if y != "Ø"],
                Prosody=wl[idx, "structure"],
                Source=["Liu2007"],
            )
            for gloss_index, cogid in enumerate(wl[idx, "cogids"]):
                args.writer.add_cognate(
                    lexeme=lexeme, Cognateset_ID=cogid, Segment_Slice=gloss_index + 1
                )
        if errors:
            with open(self.dir.joinpath("errors.md"), "w") as f:
                f.write("# ERRORS found\n")
                for idx, problems in sorted(errors.items()):
                    for error in problems:
                        args.log.warning("{0} {1}".format(idx, error))
                        f.write("* {0} {1}\n".format(error, idx))

        args.writer.cldf["LanguageTable"].tableSchema.columns = [
            col
            for col in args.writer.cldf["LanguageTable"].tableSchema.columns
            if col.name != "ISO639P3code"
        ]
