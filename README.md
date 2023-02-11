# Subtitle Syncer

## How it works?

* We use Open AI's [Whisper](https://github.com/ggerganov/whisper.cpp) model to detect text from audio.

* We get an input srt file and try to match its timings with the ones detected by the model.

* We adjust the input srt file's timings to make it match the detected one.

* We then output a new srt with adjusted timings.


## How to run?

The easier way is to use docker: just run script `./sync_subtitle_docker.sh "path/to/movie.mp4"`
