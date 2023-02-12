#!/usr/bin/env python3
import csv
import os
import subprocess
from subprocess import PIPE, TimeoutExpired
from tempfile import mkdtemp
from time import sleep
import pysrt
import click
from langdetect import detect

debug = print
SCRATCH = mkdtemp()


@click.command(help='Resync the subtitles of a movie file')
@click.argument('movie_file', type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True))
def main(movie_file):
    click.echo('Resyncing subtitles for movie file: {}'.format(movie_file))
    validate(movie_file)
    subtitles : pysrt.SubRipFile = read_subtitles(movie_file)
    language = detect_language(subtitles.text)
    model = Model()
    breakpoint()
    output = subprocess.run(['ffmpeg', ''])

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
    
class Model:
    def __init__(self):
        fifo = SCRATCH + '/' + 'modelfifo'
        os.mkfifo(fifo)
        self.model = subprocess.Popen(
                args=f'./whisper --language en --model ./model --files-from-stdin --output-csv < {fifo}',
                shell=True
                )
        self.fifo = open(fifo, 'w')

    def __del__(self):
        self.fifo.close()
        try: self.model.wait(15)
        except TimeoutExpired: self.model.kill()
        
    def process_file(self, file):
        if not os.path.isfile(file):
            raise Exception(f'file doesnt exist {file=}')
        os.unlink(file + '.csv')
        self.fifo.write(file.strip() + '\n')
        debug('Sending to model:')
        self.fifo.flush()
        while(True):
            if(e := self._model_errored_out()):
                raise Exception(f'Model Error {e}')
            if os.path.isfile(file + '.csv'):
                return self._interpret_model_output(file)
            sleep(0.3)
        
    def _interpret_model_output(self, file):
        file = file + '.csv'
        with open(file, "r") as file:
            return [row for row in csv.DictReader( file,
                    fieldnames='start end text'.split(), skipinitialspace=True)
            ]
        
    def _model_errored_out(self):
        return self.model.poll() != None




  

if __name__ == '__main__':
    main()
