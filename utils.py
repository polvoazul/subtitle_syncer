from time import sleep
from tempfile import mkdtemp
import csv
import subprocess
from subprocess import PIPE, TimeoutExpired

SCRATCH = mkdtemp()

class MovieAudio:
    def __init__(self, movie) -> None:
        self.wav_file = SCRATCH + '/main_wavfile.wav'
        subprocess.run(['ffmpeg', '-loglevel', '-0', '-y', '-i', movie, '-ar', '16000',
         '-ac', '1', '-c:a', 'pcm_s16le', self.wav_file], check=True)

    def get_excerpt(self, start, end):
        duration = end - start
        subprocess.run(['ffmpeg', '-loglevel', '-0', '-i', self.wav_file, '-ss', start, '-t', duration,
                '-c', 'copy', SCRATCH + 'splice.wav'], check=True)
        return SCRATCH + 'splice.wav'
        
    

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
