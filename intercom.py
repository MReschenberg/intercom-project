import os
import re
import asyncio
import pjsua
import pyaudio, math, struct
import requests, sys, time, threading
import audioop

SIP_USERNAME = ""
SIP_PASSWORD = ""
SIP_DOMAIN = ""
SIP_DISPLAY = ""

CELL_PHONE_ENDPOINT = ""

DOOR_RELEASE_HOOK = ""
ANSWER_HOOK = ""
HANG_UP_HOOK = ""

SOUND_CARD_NAME = b'plughw:CARD=audioinjectorpi,DEV=0'

CONFIGURING_RING = False
DEBUG = False or CONFIGURING_RING
CHANNELS = 2
BUF_SIZE = 4096
RING_THRESHOLD = 16
CALL_FINISHED = threading.Event()
MEDIA_CONNECTED = threading.Event()
AMPLITUDE = 0
MONITOR_COUNT = 0
MONITOR_THRESHOLD = 60

class CallCB(pjsua.CallCallback):
    def __init__(self, call=None):
        self.call = call
        if (call):
            call.set_callback(self)

    def on_incoming_call(self, call):
        # We don't really need this unless we want to
        # accept calls but /shrug it's boilerplate
        self.call = call

    def on_dtmf_digit(self, digit):
        if (DEBUG):
               print("DTMF " + digit)
        if (digit == "9"):
            requests.post(DOOR_RELEASE_HOOK)
        elif (digit == "1"):
            requests.post(ANSWER_HOOK)

    def on_media_state(self):
        if (self.call.info().media_state == pjsua.MediaState.ACTIVE):
            # Notify our main thread that our media connection is active
            # so the conference bridge can be engaged.
            MEDIA_CONNECTED.set()

    def on_state(self):
        if (self.call.info().state == pjsua.CallState.CONNECTING):
            if (DEBUG):
                print("answering call, connected")
            requests.post(ANSWER_HOOK)

        if (self.call.info().state == pjsua.CallState.DISCONNECTED):
            if (DEBUG):
               print("ending call, disconnected")
            requests.post(HANG_UP_HOOK)
            CALL_FINISHED.set()

# This gets called on a separate thread, but the
# main thread needs to remain active so we sleep it
# while we wait for this to return paCompelte. Ideally this
# would use a threading event but... this is implemented via
# a library.
def audioCB(in_data, frame_count, time_info, status):
    global AMPLITUDE, MONITOR_COUNT
    AMPLITUDE = audioop.rms(in_data, CHANNELS)
    MONITOR_COUNT += 1
    if (AMPLITUDE > RING_THRESHOLD and MONITOR_COUNT > MONITOR_THRESHOLD and not CONFIGURING_RING):
        return in_data, pyaudio.paComplete
    return in_data, pyaudio.paContinue

def logCB(level, str, len):
    print(str)

def get_audio_injector_index(pj):
    i = 0
    card_index = None
    for d in pj.enum_snd_dev():
        if (DEBUG):
            print(f'{i}: {d.name}')
        if (d.name == SOUND_CARD_NAME):
            print(f'Got sound device, using index: {i}')
            card_index = i
        i += 1
    if (DEBUG and card_index == None):
      print("Could not locate sound device!")
    return card_index

if __name__ == "__main__":
    mc = pjsua.MediaConfig()
    mc.snd_auto_close_time = 0 # don't delay closing devices
    mc.ec_tail_len = 0 # don't use echo cancellation
    mc.no_vad = True # disable Voice Activity Detector
    mc.channel_count = 2 # use stereo

    lc = pjsua.LogConfig(console_level=6)
    if (DEBUG):
        lc.msg_logging = True
        lc.callback = logCB


    pj = pjsua.Lib()
    pj.init(log_cfg=lc, media_cfg=mc)
    pj.create_transport(pjsua.TransportType.TCP)
    pj.start()
    dev_idx = get_audio_injector_index(pj)
    pjAcc = pj.create_account(pjsua.AccountConfig(SIP_DOMAIN, SIP_USERNAME, SIP_PASSWORD, SIP_DISPLAY))
    while (True):
        CALL_FINISHED.clear()
        MEDIA_CONNECTED.clear()
        AMPLITUDE = 0
        # Create PyAudio instance and stream. This will immediately grab the sound device
        # described by the input device index below. In our case this is the soundcard.
        # This can't be used simultaneously by both pj and PyAudio (even on separate threads) so
        # we create and destroy the audio instance and the thread within this loop. Recreating the
        # stream itself doesn't seem to free the device lock consistently.
        audio = pyaudio.PyAudio()
        stream = audio.open(format=pyaudio.paInt16, rate=44100, channels=CHANNELS, \
                        input_device_index=1, input=True, \
                        frames_per_buffer=BUF_SIZE, stream_callback=audioCB)
        stream.start_stream()
        while (stream.is_active()):
            if (DEBUG):
                print(AMPLITUDE)
                if (AMPLITUDE > RING_THRESHOLD and MONITOR_COUNT > MONITOR_THRESHOLD):
                    print("ringing")
            time.sleep(0.1)
        if (DEBUG):
            print(AMPLITUDE)

        stream.stop_stream()
        stream.close()
        audio.terminate()

        # Give it a second to free the sound device
        time.sleep(1)
        # Have pj steal back the sound devices
        pj.set_snd_dev(dev_idx, dev_idx) # audio injector plughw

        call = pjAcc.make_call(CELL_PHONE_ENDPOINT, CallCB())
        # Wait until the call media is connected, then connect our sound device to the
        # conference bridge in both directions.

        MEDIA_CONNECTED.wait()
        print(call.info().conf_slot)
        pj.conf_connect(0, call.info().conf_slot)
        pj.conf_connect(call.info().conf_slot, 0)

        # Block until the call is finished.
        CALL_FINISHED.wait()

        # Disable sound devices so they're free for pyaudio
        # this is also necessary to ensure the device gets "closed" from one
        # pjsip call to the next, for some reason.
        pj.set_null_snd_dev()

        # Pressing the door release button and/or hanging up the call can
        # generate noise on the line, which can be misconstrued as another ring.
        # Reset our count here to make sure that doesn't happen.
        MONITOR_COUNT = 0
        time.sleep(5)

