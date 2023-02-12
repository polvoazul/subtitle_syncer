#!/usr/bin/env python3
import atexit
import os
import shutil
import pysrt
import click
from langdetect import detect

from smart import fit_subtitle_to_audio
from utils import SCRATCH

debug = print
def cleanup():
    shutil.rmtree(SCRATCH)

@click.command(help='Resync the subtitles of a movie file')
@click.argument('movie_file', type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True))
def main(movie_file):
    click.echo('Resyncing subtitles for movie file: {}'.format(movie_file))
    validate(movie_file)
    subtitles: pysrt.SubRipFile = read_subtitles(movie_file)
    language = detect_language(subtitles.text)
    fit_subtitle_to_audio(subtitles, movie_file)

def detect_language(text):
    language = detect(text)
    return language

    
def validate(movie_file):
    is_movie(movie_file)
    get_subtitle_file(movie_file)
    
def is_movie(movie_file):
    video_extensions = [".mp4", ".mkv", ".avi", ".flv", ".wmv", ".mov", ".3gp", ".m4v", ".ts"]
    return any(movie_file.endswith(extension) for extension in video_extensions)

def get_subtitle_file(movie_file):
    subtitle_extensions = [".srt"]
    base_file, _ = os.path.splitext(movie_file)
    for extension in subtitle_extensions:
        if os.path.exists(base_file + extension):
            return base_file + extension
    
def read_subtitles(movie_file):
    return pysrt.open(get_subtitle_file(movie_file))
    
if __name__ == '__main__':
    atexit.register(cleanup)
    main()
