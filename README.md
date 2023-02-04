# Microblog Server (mb_server.py)
In a video published in January 2023, Julian (OH8STN) shared an idea he had regarding the use of data mode radio to share information in the same way as you might share using social media.  Julian has a particular interest in emergency comms and his idea is to provide a microblogging facility that's decentralised and does not require the Internet.

The code here is a very simple (maybe simplistic) server.  mb_server supports two request types; LST to list the microblog posts available, EXT to list the posts with the date of each in the listing and GET to retrieve a post.  The server uses JS8Call to provide the transport mechanism.  The server interfaces with JS8Call using the latter's API, accessed via TCP, i.e. mb_server makes a TCP connection to JS8Call.  By default, the API is at IP address 127.0.0.1 and TCP port 2442.

I have included brief details of the JS8Call command verbs and response types below.

There's an important note about the state of the Outgoing Messages area in the section Running the Server - please read this.

## Before you get started
Before you try this code, there are three videos you are going to want to watch:
* Off Grid Ham Radio Micro Blogging with JS8Call & VARAC - https://youtu.be/szZlPL2h534
* JS8Call Microblogging Overview - https://youtu.be/uUsUmD2c2SY

## Microblog Commands
An operator can use the standard JS8Call Outgoing Message Area to send the following commands to a microblog server:

* M.L - list all posts available - the output will be limited to a list of 5
* M.L >n - list all posts with an id greater than n
* M.L yyyy-mm-dd - list all posts dated yyyy-mm-dd
* M.L >yyyy-mm-dd - list all posts created after yyyy-mm-dd
* M.E - as per MB.LST but with list entries that include the date of the post
* M.E >n - as per MB.LST but with list entries that include the date of the post
* M.E yyyy-mm-dd - as per MB.LST but with list entries that include the date of the post
* M.E >yyyy-mm-dd - as per MB.LST but with list entries that include the date of the post
* M.G n - get the post with the id n

Earlier versions of these commands are still supported; MB.LST, MB.L, MB.EXT, MB.E, MB.GET and MB.G.

The commands must be directed to the server, i.e. prefixed with the server station callsign.  @ALLCALL is not supported.  JS8Call can be used by the server station operator in the normal way, albeit once any outstanding microblog requests have been satisfied.  mb_server simply ignores all directed received messages that don't start with M.L, M.E or M.G.  This is an important point as **the requestor will not receive an error message if he/she/they mistype the command**.  This is intentional to allow for the widest range of normal JS8Call messages.

## MB Server Announcement
The server can send announcement to the @MB call group.  An announcement contains:

* The grid location of the server (as set in JS8Call)
* A capabilities field that lists the supported operations
  * L - Listing of posts
  * E - Extended listing of posts
  * G - Get a post
  * U - Upload a post (for future use)
* The ID of the latest post
* The data of the latest post
* A space-separated list of languages used as per RFC5646 Language-Region
  * This is an optional field

An example is - `@MB JO01EV LEG 29 2023-01-27 EN-GB`

The @MB announcement mechanism is controlled by three configuration parameters in settings.py:

* `announce` - switches the mechanism on and off, default is True which means on
* `mb_announcement_timer` - sets the delay between announcements, default is 60 mins
* `languages` - sets the languages listed in th announcement, default is EN-GB
  * Set this to a NULL string if you don't want to send announcements, i.e. delete the characters between the single quotation marks

For a user to receive these announcements, they must add the @MB group to the Call Activity list in JS8Call.  To do this, right click in the list and choose Add new Station or Group... then enter @MB into the pop-up box and click OK.

## Microblog Post File
A microblog post can contain any text content.  All text will be encoded as UTF8 and lower case letters will be shifted to upper case on transmission.

The post file name must start with the blog ID and a date like this:

`nnnn - yyy-mm-dd - Your chosen summary test`

Although we show four digits above for the reference (nnnn), the server supports any number of digits up to a value of 2000000000.

## Installation

* Pull the repo or download the zip file from here
* Create a posts directory on your PC
* Move the sample posts downloaded into the posts directory
* In settings.py, change the posts_dir variable in the script to reflect the location of the directory - note the use of \\\\ in Windows paths
* In JS8Call go to File -> Settings -> Reporting
* In the API section check Enable TCP Server API and Accept TCP Request
* Run the mb_server.py script

Your station is now ready to accept calls for microblog posts.

## Running the server
You don't need to stop the server to add a new post to the posts directory; the server will check the list of posts on each request and update the latest post information in the next @MB announcement.

**Important:** The Outgoing Message area in the server JS8Call **must not be** in the DIRECTED MESSAGE mode.  If it is, all messages, including @MB announcements, will be prefixed with the callsign of whichever station you have selected. 

**Draft text (subject to confirmation):** If a JS8Call user does not interact with the program via the keyboard for a period of time, an idle timer pops and the user gets a dialog box warning "You have been idle for more than 60 minutes".  Unless you respond to the dialog box, JS8Call stops transmitting, including the sending of messages pushed through its API.  I believe this timeout is controlled by File -> Settings -> General -> Networking & Autoreply -> Idle timeout - disable autoreply after: The default value is 60 minutes of inactivity.  The maximum value is 1440 minutes or 24 hours.  Obviously, this could be a limiting factor in locations where unattended operation is permissible.

PS: My programming skills are self-taught and so don't be surprised if my coding standard are poor :-)

# JS8Call API
## Introduction
JS8Call provides an API that allows programmatic control of the JS8Call program.  The interface is provided via a server running within JS8Call and accessed via TCP or UDP.  The API accepts requests and sends responses in JSON formatted messages.  The API also sends asynchronous notifications as JSON messages.

Request, response ad notification messages all have the same format:

`{"type": "AS_BELOW", "value": "CAN_BE_NULL", "params": {AN_ARRAY_OF_TYPE-VALUE_PAIRS}}`

A common params element is _ID, like this:

`"_ID": "1673961458978"`

The integer is of an Epoch timestamp value (as in this case), indicating the time of the request.

An example is a request for the station callsign and the response is:

`{"type": "STATION.GET_CALLSIGN", "value": "", "params": {"_ID": "1673961458978"}}`
`{"type": "STATION.CALLSIGN", "value": "M0PXO", "params": {"_ID": "1673961458978"}}`

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
