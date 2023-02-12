from collections import Counter
import pandas as pd
import itertools
import pysrt
from thefuzz import fuzz, process
from thefuzz.process import extractOne as fuzzy_match

from utils import Model, MovieAudio, debug, print_srt_collection

def fit_subtitles_to_audio(subtitles: pysrt.SubRipFile, movie_file):
    dense_minutes = find_dense_portions_every_x_mins(subtitles, x=40)
    slices_to_compare = [subtitles.slice(starts_after={'minutes': minute}, starts_before={'minutes': minute + 1}) # add grace?
           for minute in dense_minutes]
    audio = MovieAudio(movie_file)
    model = Model()
    matcher = FuzzyMatcher(subtitles)
    probe = lambda start, end: _probe(start, end, audio, model)
    debug(f"Probing minutes: {dense_minutes}")
    probed_speeches = {minute: probe(minute*60, (minute+1)*60) for minute in dense_minutes}
    #for i in probed_speeches[1:]: probed_speeches[0].extend(i)  # cant use a simple flatten because its a list of SubRipFiles
    #probed_speeches = probed_speeches[0]
    mean_drifts = {minute: matcher.get_mean_drift(probed) for minute, probed in probed_speeches.items()}
    breakpoint()
    matcher.get_mean_drift(list(probed_speeches.values())[0])

        
class FuzzyMatcher:
    def __init__(self, corpus):
        self.original_corpus = corpus
        self.corpus = self.rebuild_corpus(corpus)
        
    def rebuild_corpus(self, corpus):
        return {line.start.total_seconds(): line.text for line in corpus}

    def get_mean_drift(self, probed):
        WINDOW = 5*60
        begin = min(p.start.total_seconds() for p in probed)
        end = max(p.start.total_seconds() for p in probed)
        window = self.rebuild_corpus(self.original_corpus.slice(
            starts_after={'seconds': begin - WINDOW }, starts_before={'seconds': end + WINDOW}
        ))
        drifts = []
        for line in probed:
            match = fuzzy_match(line.text, window)
            if not match: continue
            text, score, corpus_start = match
            drifts.append([line.start.total_seconds() - corpus_start, score])
        drifts = pd.DataFrame(drifts, columns=['drift', 'score'])
        # TODO: use score, line size, cut outliers, expanding window...
        return drifts[drifts.score > 80].drift.median()

        
def _probe(start, end, audio, model): # units are in seconds
    excerpt = audio.get_excerpt(start, end)
    probed_speech = model.process_file(excerpt)
    probed_speech.shift(seconds=start)
    return probed_speech
    

def find_dense_portions_every_x_mins(subtitles, x):
    minutes = (s.start.minutes + s.start.hours*60 for s in subtitles)
    subs_on_minute = Counter(minutes)
    end = max(subs_on_minute)
    out = []
    for window in range(0, end, x):
        mm = max((subs_on_minute.get(i, 0), i) for i in range(window, window+x, 1)) # every min
        if mm[1]: out.append(mm[1])
    return out
