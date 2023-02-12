import datetime
import os
from time import sleep
from tempfile import mkdtemp
import csv
import subprocess
from subprocess import PIPE, TimeoutExpired

import pysrt

debug = print

SCRATCH = mkdtemp() + '/'

class MovieAudio:
    def __init__(self, movie) -> None:
        self.wav_file = SCRATCH + 'main_wavfile.wav'
        debug('Extracting audio from movie')
        subprocess.run(['ffmpeg', '-loglevel', '-0', '-y', '-i', movie, '-ar', '16000',
         '-ac', '1', '-c:a', 'pcm_s16le', self.wav_file], check=True)

    def get_excerpt(self, start, end):
        duration = end - start
        start, end, duration = str(start), str(end), str(duration)
        try: os.unlink(SCRATCH + 'splice.wav')
        except FileNotFoundError: pass
        subprocess.run(['ffmpeg', 
        # '-loglevel', '-0',
         '-i', self.wav_file, '-ss', start, '-t', duration,
                '-c', 'copy', SCRATCH + 'splice.wav'], check=True)
        return SCRATCH + 'splice.wav'

class Model:
    def __init__(self):
        fifo = SCRATCH + 'modelfifo'
        os.mkfifo(fifo)
        self.model = subprocess.Popen(
                args=f'./whisper --language en --model ./model --files-from-stdin --output-srt < {fifo}',
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
        try: os.unlink(file + '.srt')
        except FileNotFoundError: pass
        self.fifo.write(file.strip() + '\n')
        debug('Sending to model:')
        self.fifo.flush()
        while(True):
            if(e := self._model_errored_out()):
                raise Exception(f'Model Error {e}')
            if os.path.isfile(file + '.srt'):
                return self._interpret_model_output_srt(file)
            sleep(0.3)
        
    def _interpret_model_output_srt(self, file):
        file += '.srt'
        return pysrt.open(file)

    def _interpret_model_output_csv(self, file):
        file = file + '.csv'
        with open(file, "r") as file:
            return [row for row in csv.DictReader( file,
                    fieldnames='start end text'.split(), skipinitialspace=True)
            ]
        
    def _model_errored_out(self):
        return self.model.poll() != None

def print_srt_collection(srt):
    for i in srt:
        print(f'[{i.start} --> {i.end}]   ' + i.text.replace("\n", " | "))

def total_seconds(self):
    return self.ordinal / 1000

pysrt.SubRipTime.total_seconds = total_seconds
