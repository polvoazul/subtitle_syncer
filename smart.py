from thefuzz import fuzz, process

from utils import Model, MovieAudio

def fit_subtitles_to_audio(subtitles, movie_file,):
    audio = MovieAudio(movie_file)
    model = Model()
