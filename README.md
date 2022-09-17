# Intercom-Project
Instructions for building an open-source intercom adapter using Python and a Raspberry Pi. This adapter lets you turn your old-fashioned, hard-wired intercom into one that can call your cell phone :) This project is renter-friendly, and doesn't require any modification of the internals of your intercom (either the tenant station in your apartment, or the intercom system in the walls of your building). It is intended for audio intercoms and does not support video. I used this on an Aiphone GT system with an Aiphone GT-1D tenant station.

<img style="margin:20px;" alt="A close up photo of an audio injector sound card on a raspberry pi. The sound card has two pairs of stereo outputs, each plugged into one end of a headphone splitter cable. The combined cable is offscreen. The pi is connected to ethernet." src="https://user-images.githubusercontent.com/14968521/190834301-ecb9578c-10d8-40ad-82fb-b8db9862faf7.png"><img height="300" hspace="20"/><img width="300" alt="A zoomed out photo of the setup. An Aiphone GT-1D is mounted in a phone nook. The pi rests in the nook, hooked up to the Aiphone through its handset port. Two switchbots sit on the Aiphone, one on the door release button and one on the hang-up mechanism." src="https://user-images.githubusercontent.com/14968521/190834314-01664069-7df7-4a9a-a826-82079b421d65.png"><img height="300" hspace="20"/><img width="300" alt="A close up of the switchbots on the phone body. There is still enough space to press the door release button manually, or to press the hang-up mechanism." src="https://user-images.githubusercontent.com/14968521/190834410-d5173d8d-c83e-487c-b0ee-807801235442.png">


## How does this work?

This project connects a Raspberry Pi to your intercom systen via the RJ9 port of the tenant station inside your apartment (this is the port that connects the phone handset to the phone body). Once connected, the Pi continuously monitors the line for a ring signal. If a ring is detected, it generates a phone call to the given cell phone number and relays the audio from your intercom. Pressing "9" will activate the door release and let someone into your building. Hanging up the phone call on your cell phone will also hang up the call from the station in your apartment, and it will set the Pi back to audio-monitoring mode.

## Hardware
The basics:
- A Raspberry Pi (I used a 3B)
- A compatible sound card with a line-in input (I used an audio-injector stereo card)
- Two SwitchBots -- one for controlling the door release button, and one controlling the phone hook/hang-up mechanism.

To send and recieve audio I used:
- Two stereo-to-3.5mm adapters, one for handling input and one for handling output on the sound card
- A headphone splitter (turns one female 3.5mm input into two male 3.5mm outputs: one mic-only, one speakers-only)
- A custom-made male RJ9-to-3.5mm male cable.

You'll plug the RJ9 cable into the tenant station's RJ9 port (unplugging the handset). Then, you'll plug the 3.5mm output from the RJ9 cable into the splitter. Each end of the splitter should go into a stereo adapter, and those stereo adapters should go into the sound card. You want the "speaker" part of the cable to go to the "input" stereo ports on the soundcard, and the "mic" cable to go to the "output" stereo ports on the sound card.

## Creating the RJ9-to-3.5mm Cable:

While we won't need to modify any of the phone internals for this project, we will need to look at them in order to create our audio cable. If you open your phone, you should have four main wires for audio. In the GT-D1, they're labelled and colored like this:

<img width="300" alt="Four wires, with labels screen printed on the PCB. Red = R-, Green = R+, Yellow = Mic-, Black = Mic+" src="https://user-images.githubusercontent.com/14968521/190833269-2da68aee-7ab4-4d85-8a18-f4b0f807d317.png">

If these aren't labelled, you might need to open up your phone handset and trace the speaker and mic wires there. Ultimately, we want to create a map for the output of the phone jack. This will help us correctly line up the wires in the audio cable. My phone jack is organised like this: 

<img width="300" alt="Pins from left to right, with RJ9 clip pointing down. 1. Black (Mic+) 2. Red (R-) 3. Green (R+) 4. Yellow (Mic-)" src="https://user-images.githubusercontent.com/14968521/190833614-0ee609cc-7712-490e-875f-48a3236c1d4f.png">

A 3.5mm audio jack has (from tip inward) four "pins": Left speaker, right speaker, ground, and mic. **We need to map R- to the left speaker, R+ to the right speaker, Mic+ to ground, and Mic- to mic. **
I cut open an old aux cable that I wasn't using and crimped a RJ9 head onto it. The cables inside my aux cord were organised like this: 

<img width="300" alt="Pins from left to right, with the thin part of the 3.5mm cable pointing left. 1. White (Left) 2. Green (Right) 3. Red (Ground) 4. Black (Mic)" src="https://user-images.githubusercontent.com/14968521/190833943-73a91532-b4f0-4c26-b8bd-77b1acefbe44.png">

Using the aux cord's wire colors, the RJ9 head on my final cable was organised like this:

<img width="300" alt="Pins from left to right with RJ9 clip pointing down. 1. Red (Ground) 2. White (Left) 3. Green (Right) 4. Black (Mic)" src="https://user-images.githubusercontent.com/14968521/190834103-481de252-76e1-4492-b41e-2bde7fdde3c4.png">

This is horribly confusing. 

## Creating a Twilio SIP Account
I followed [this tutorial](https://github.com/eric-brechemier/how-i-replaced-skype-with-twilio/issues/5) -- I chose to not use TLS or make encryption mandatory, because I found it difficult to set up reliably with PJSIP, and I'm not extremely worried about the security of my intercom calls.

## Account Configuration
Open `intercom.py` and adjust the following variables with the specifics of your Twilio account:
```python
SIP_USERNAME = "" # The username in your Twilio SIP credentials
SIP_PASSWORD = "" # The plain-text password in your Twilio SIP credentials
SIP_DOMAIN = "" # Your Twilio SIP domain, with regional subdomain (ie. us1), ending in ";transport=tcp" with no "sip" prefix
SIP_DISPLAY = "" # Your Twilio SIP domain, with regional subdomain (ie. us1), with no "sip" prefix

CELL_PHONE_ENDPOINT = "" # The phone number you want to call, in SIP format: "sip:PHONE_NUMBER@SIP_DISPLAY"
```

## Webhook Configuration
Originally, I tried to use [this SwitchBot python library](https://github.com/RoButton/switchbotpy) to integrate the "answer phone" and "buzz door" commands into this script. Unfortunately, the Bluetooth on my Pi was unreliable at best (even after disabling the WiFi in `rfkill`), and so I elected to integrate the SwitchBots into my [Home Assistant](home-assistant.io/) setup where my Bluetooth is more reliable. The bots are triggered via web hooks using HA's automations system. If you go this route, you'll want to replace the following variables with the appropriate web hook URLs:
```python
DOOR_RELEASE_HOOK = ""
ANSWER_HOOK = ""
HANG_UP_HOOK = ""
```

My "answer" hook simulates picking up the phone by telling the SwitchBot on the phone hook to press once. My "hang up" hook does that same action, but twice for redundancy.
My "door release" hook tells the SwitchBot on the door release button to press twice, waiting three seconds between presses. This ensures delivery people have enough time to get through the security gate and the front door. You may wish to adjust these routines depending on your intercom's behaviour.

## Environment Setup
This setup assumes you're starting fresh on a new Pi. If you're not, some of these installs might be redundant. SSH in and, as always: `sudo apt update && sudo apt upgrade` (if you're me, you'll also wanna `sudo apt install vim`)

To start, let's set up our sound card. You should follow the [latest instructions for setting up an audio-injector stereo card](https://github.com/Audio-Injector/stereo-and-zero). At the time of writing this, those instructions involve adding `dtoverlay=audioinjector-wm8731-audio` to the end of `/boot/config.txt ` and rebooting. Then, open `alsamixer` and enable "Output Mixer HiFi". We'll also want to set "Line" to "CAPTURE L R" and set "Input MUX" to "LINE IN".

This project uses PyAudio which requires the following libraries, lest you get a PortAudio.h error.
`sudo apt-get install libportaudio0 libportaudio2 libportaudiocpp0 portaudio19-dev` After doing that, you can `pip install pyaudio`.

This project also uses [PJSIP](https://github.com/pjsip/pjproject) and [PJSUA](https://www.pjsip.org/python/pjsua.htm). Clone pjsip via `https://github.com/pjsip/pjproject`. We'll need to make a file change before building (this may not apply if you're using a different sound card). Open `pjproject/pjlib/include/pj/config_site.h.` (or create it if it doesn't exist) and add the following content:
```c
#define PJMEDIA_AUDIO_DEV_HAS_PORTAUDIO 0
#define PJMEDIA_AUDIO_DEV_HAS_ALSA 1
#include <pj/config_site_sample.h>
```
Save and return to the `pjproject` directory. Then run:
`./configure`
`make dep && make clean && make`

Using [Jamie's fork of PJSUA](https://github.com/jcsteh/python3-pjsip) follow the install instructions for the python bindings:
`cd pjproject/pjsip-apps/src/`
`git clone https://github.com/jcsteh/python3-pjsip`
`cd cloned_repo`
`python3 setup.py build`
`sudo python3 setup.py install`

Verify you can `import pjsua` into a python environment.

If you're only using this Pi for this project, you may find it helpful to set the soundcard as your default ALSA device. First, find the index of your card by running `aplay -l` and/or `arecord -l`. Then set that index (for me, it's 2) in the following file:
```shell
> sudo vim /usr/share/alsa/alsa.conf
...
defaults.ctl.card 2
defaults.pcm.card 2
```

## Configuring Ring Detection

Your Pi will always monitor a low level of noise on your intercom line. When the intercom rings, though, that noise level will change. In this section, we'll sample a ring on the line and use that to create a `RING_THRESHOLD`. When the noise level surpasses that threshold, the Pi will assume the phone is ringing and generate a call. Otherwise, it'll continue to monitor audio until that threshold is reached or the program is exited. You'll need a stopwatch.

To start, set `CONFIGURING_RING` to `True`. This will also enable logging.
Run the program with `python3 intercom.py > samples.out`. This will redirect the output to a file, which will make it easier to access later :) Start a stopwatch when you start the program. This will help you figure out exactly _when_ the ring occurred, in case the ambient noise on your line makes it difficult to tell later on.

Once the program has started running, head down to your intercom and buzz your apartment. Hit "lap" on your stopwatch when you press the button. Don't answer this call, or attempt to buzz anyone in in this process. We're trying to isolate the ring signal, and performing other actions can muddy our data. Head back to your apartment and stop both your stopwatch and the program (Ctrl+C).

Open `samples.out` and copy the noise values into a spreadsheet (you'll need to delete the PJSIP logging in the beginning, we're just interested in the numbers that get printed after PJSIP and PyAudio are instantiated). If you're working in Google Sheets, you can turn these values into a line graph by selecting the column and clicking "Insert > Chart".

Your graph might look something like this.

<img width="1129" alt="Y axis tracks amplitudes from 0 to 800, X axis is time (0 to 300). There are two peaks at time 0 and time 50 showing an amplitude of 700 and 150 respectively. Then the graph is largely flat. There is a mid-sized (~20 amplitude) peak around time 150." src="https://user-images.githubusercontent.com/14968521/190830636-a4e6e2bf-c766-45f6-ac41-fd8327a04dc7.png">

I've got a few different spikes on my graph, which makes it hard to tell exactly when the ring occurred. This is where the stopwatch comes in handy. Look at the final time on your stopwatch -- this should be the cumulative amount of time elapsed from the start of your program to the end of your program. Convert this value to seconds. Then, compute N/T where N is the number of samples taken during the run of your program and T is the total time elapsed in seconds. As an example, it took me 1 minute and 17 seconds to start my program, ring the intercom, and stop the program. This is 77 seconds. In that time, my program logged 293 samples. This means there was roughly 293/77 ~ 4 samples logged per second. I lapped my stopwatch at 49 seconds -- this is when the ring occurred. Based on the samples-per-second rate we just computed, I should see the ring show up around the 49*4 = 196th sample.

Once you've identified the ring in your data, set `RING_THRESHOLD` to a value just below the ring's peak. My ring peaked at 18, so I set my threshold to 16.

You may need to repeat this process a few times in order to get an appropriate value. Set this value too high and you'll miss some rings, too low and you'll get alerted when the phone isn't ringing at all.

You should also set the `MONITOR_THRESHOLD` using your graph above. This value represents the amount of samples to throw away before we start listening for rings. The two early peaks on my graph occur when I start audio monitoring, regardless of the intercom state. The second peak occurs at sample number 52, so to be safe I've set my `MONITOR_THRESHOLD` to 60.

**Set `CONFIGURING_RING` to `False` before continuing**

## Running the Program

You can run the program with `python3 intercom.py`. The program will run until it is stopped by the user or hits an exception. If you want to run this in the background (and leave it running after you close your SSH session) you can use:
```shell
$> nohup python3 -u phone.py &
```
Output should automatically log to `nohup.out`. Be careful this file doesn't get too big. You may want to disable debugging.

## Debugging the Program

To log various program states, set `DEBUG` to `True`. This should print stuff to stdout.

### Debugging Audio

If you're having trouble with audio, you may find [PJSIP's audio debugging](https://trac.pjsip.org/repos/wiki/audio-problem-local-no-audio) helpful.

If you want to test audio locally (ie. rule out any funniness from your intercom), you can plug a pair of headphones into your headphone splitter instead of the RJ9 cable. To use the on-board mic, you'll want to open `alsamixer` and (after selecting the sound card from the F6 menu) change the Input MUX to "Mic" and set "MIC" to "CAPTURE L R". If you can't see these options, try pressing F5.

For other audio problems, you may want to play around with the `MediaConfig` parameters:
```python
mc.snd_auto_close_time = 0 # don't delay closing devices
mc.ec_tail_len = 0 # don't use echo cancellation
mc.no_vad = True # disable Voice Activity Detector
mc.channel_count = 2 # use stereo
```

If PJSIP can't find your sound device, it may have a different name than the default I've provided. Enable `DEBUG` and check the output from `get_audio_injector_index`. You can manually hard code the index of your sound card, or you can alter the `SOUND_CARD_NAME` variable so the dynamic fetch works approrpiately. Keep in mind, these indicies change between restarts, so if you hard code it and restart, you'll need to verify/hard code it again.

### Debugging Ring Detection

If you don't get any meaningful data from the ring detection configuration section above, try swapping the input and output lines to your sound card (ie. send the speaker end of your splitter to the sound card output and the mic end to the soundcard input). You may also want to remake your cable. If you have a multimeter, it may also be useful to do a conductivity test to ensure the wires inside your cable aren't broken.

If you've changed your PyAudio parameters (ie. from `pyaudio.paInt16` format to `pyaudio.paInt32` format), your old ring detection values may no longer be accurate. Redo the calibration above.

Your intercom may also generate different ring thresholds depending on your ring volume, or whether or not you have silent mode enabled. When in doubt, try to recalibrate with the instructions above.

If you ring the intercom too soon after starting the program, the ring may be ignored. Decrease the `MONITOR_THRESHOLD` value to start monitoring closer to startup. You may encounter noise that generates false rings on startup, this value is a bit of a balancing act.

## Thank you!

This project wouldn't have been possible without the limitless patience of my partner Sonia and technical help and encouragement from @jteh. Thank you :)

If you give this a shot, I'd love to hear from you, and if you run into trouble please don't hesitate to file an issue. In the meantime, I'm working on adding support for call forwarding to multiple numbers, and troubleshooting what to do when the intercom gets your voicemail ;)
