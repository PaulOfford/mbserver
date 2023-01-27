# Microblog Server (mb_server.py)
In a video published in January 2023, Julian (OH8STN) shared an idea he had regarding the use of data mode radio to share information in the same way as you might share using social media.  Julian has a particular interest in emergency comms and his idea is to provide a microblogging facility that's decentralised and does not require the Internet.

The code here is a very simple (maybe simplistic) server.  mb_server supports two request types; LST to list the microblog posts available, and GET to retrieve a post.  The server uses JS8Call to provide the transport mechanism.  The server interfaces with JS8Call using the latter's API, accessed via TCP, i.e. mb_server makes a TCP connection to JS8Call.  By default, the API is at IP address 127.0.0.1 and TCP port 2442.

I have included brief details of the JS8Call command verbs and response types below.

## Before you get started
Before you try this code, there are three videos you are going to want to watch:
* Off Grid Ham Radio Micro Blogging with JS8Call & VARAC - https://youtu.be/szZlPL2h534
* Micro Blogging with JS8Call - Proof of Concept - https://youtu.be/Nxg5_hiKlqc
* Microblog Server Part #1 - 

PS: My programming skills are self taught and so don't be surprised if my coding standard are poor :-)

# JS8Call API
## Introduction
JS8Call provides an API that allows programmatic control of the JS8Call program.  The interface is provided via a server running within JS8Call and accessed via TCP or UDP.  The API accepts requests and sends responses in JSON formatted messages.  The API also sends asynchronous notifications as JSON messages.

Request, response ad notification messages all have the same format:

{"type": "AS_BELOW", "value": "CAN_BE_NULL", "params": {AN_ARRAY_OF_TYPE-VALUE_PAIRS}}

A common params element is _ID, like this:

"_ID": "1673961458978"

The integer is of an Epoch timestamp value (as in this case), indicating the time of the request.

An example is a request for the station callsign and the response is:

{"type": "STATION.GET_CALLSIGN", "value": "", "params": {"_ID": "1673961458978"}}
{"type": "STATION.CALLSIGN", "value": "M0PXO", "params": {"_ID": "1673961458978"}}

Note how the _ID value in the response matches up to the request, allowing correlation of the two.

The JS8Call code that parses these requests can be found in mainwindow.cpp at around line 13080.

## Requests to JS8Call
INBOX.GET_MESSAGES – Get a list of inbox messages

INBOX.STORE_MESSAGE – Store a message in the inbox

MODE.GET_SPEED – Get the TX speed

MODE.SET_SPEED – Set the TX speed

RIG.GET_FREQ – Get the current dial freq and offset

RIG.SET_FREQ – Set the current dial freq and offset

RX.GET_BAND_ACTIVITY – Get the contents of the band activity window

RX.GET_CALL_ACTIVITY – Get the contents of the call activity window

RX.GET_CALL_SELECTED – Get the currently selected callsign

RX.GET_TEXT – Get the contents of the QSO window

STATION.GET_CALLSIGN – Get the station callsign

STATION.GET_GRID – Get the station grid

STATION.SET_GRID – Set the station grid

STATION.GET_INFO – Get the station QTH/info

STATION.SET_INFO – Set the station QTH/info

STATION.GET_STATUS – Get the station status

STATION.SET_STATUS – Set the station status

TX.SEND_MESSAGE – Send a message via JS8Call

TX.SET_TEXT – Sets the text in the outgoing message box, but does not send it.

WINDOW.RAISE – Focus the JS8Call window

### Responses and Notifications from JS8Call
CLOSE - JS8Call has been closed

INBOX.MESSAGES – A list of inbox messages

INBOX.MESSAGE – A single inbox message

MODE.SPEED – The current TX speed

PING – Keepalive from JS8Call

RIG.FREQ – The rig frequency has been changed

RIG.PTT – PTT has been toggled

RX.ACTIVITY – We received something

RX.BAND_ACTIVITY – The band activity window

RX.CALL_ACTIVITY – The call activity window

RX.CALL_SELECTED – The currently selected callsign

RX.DIRECTED – A complete message

RX.SPOT – A station we have heard

RX.TEXT – Contents of the QSO window

STATION.CALLSIGN – Callsign of the station

STATION.GRID – Grid locator of the station

STATION.INFO – QTH/info of the station

STATION.STATUS – Status of the station

TX.FRAME – Something we are sending

TX.TEXT – Text in the outgoing message window
