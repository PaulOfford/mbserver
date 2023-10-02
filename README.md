# Microblog Server (MbServer)
In a video published in January 2023, Julian (OH8STN) shared an idea he had regarding the use of data mode radio to share information in the same way as you might share using social media.  Julian has a particular interest in emergency comms and his idea is to provide a microblogging facility that's decentralised and does not require the Internet.

The code here is a very simple (maybe simplistic) server.  MbServer supports several request types:

* List the microblog posts available
* List the posts with the date of each in the listing
* Get the contents of a post
* Get a weather report
* Ask all MbServers to announce themselves

The server uses JS8Call to provide the transport mechanism.  The server interfaces with JS8Call using the latter's API, accessed via TCP, i.e. mb_server makes a TCP connection to JS8Call.  By default, the API is at IP address 127.0.0.1 and TCP port 2442.

I have included brief details of the JS8Call command verbs and response types below.

There's an important note about the state of the Outgoing Messages area in the section Running the Server - please read this.

## Before you get started
Before you try this code, there are three videos you are going to want to watch:
* Off Grid Ham Radio Micro Blogging with JS8Call & VARAC - https://youtu.be/szZlPL2h534
* Microblogging Quick Start - https://youtu.be/URtUwvGok1Q
* Introduction to MbServer - https://youtu.be/usFkt7Kcs_g

## Microblog Commands

Commands can be in one of two formats:

* Command Line Interface (CLI) - typically sent from the Outgoing Message Box of JS8Call on a client machine
* Application Program Interface (API) - typically sent from an application (such as MbClient) running on the client machine and communicating using JS8

The client SHOULD NOT switch between formats during a conversation.  Although this may work, there is no guarantee it will work in the future.

The commands must be directed to the server, i.e. prefixed with the server station callsign.  An exception is
use of the callsign group @MB.  We'll cover this later in this document under header MB Server Query.
@ALLCALL is not supported.  JS8Call can be used by the server station operator in the normal way,
albeit once any outstanding microblog requests have been satisfied.  MbServer simply ignores all
directed received messages that don't match the defined command formats.  This is an important point
as **the requestor will not receive an error message if the command is incorrect**.  This is intentional
to allow for the widest range of normal JS8Call messages.

### Command Line Interface (CLI)
An operator can use the standard JS8Call Outgoing Message Area to send the following commands to a microblog server:

* `M.L` - list the five most recent blogs
  * The range of this list can be changed by changing lst_limit in server_settings.py
* `M.L >n` - list all posts with an id greater than n
* `M.L yyyy-mm-dd` - list all posts dated yyyy-mm-dd
* `M.L >yyyy-mm-dd` - list all posts created after yyyy-mm-dd
* `M.E` - as per M.L but with list entries that include the date of the post
* `M.E >n` - as per M.L but with list entries that include the date of the post
* `M.E yyyy-mm-dd` - as per M.L but with list entries that include the date of the post
* `M.E >yyyy-mm-dd` - as per M.L but with list entries that include the date of the post
* `M.G n` - get the post with the id n

M.LST, M.EXT and M.GET are no longer supported.  The MB.xxx form has also been dropped to reduce the
amount of code to maintain.

Earlier versions of the CLI included a CLI parser and parameter checking.  Revision 9 included a
significant rewrite of the CLI such that the CLI now just translates requests into the API form and
checking is done in the API.  This provides better code layering and reduces the amount of code to maintain.

### Application Program Interface (API)
Command formats are as follows:

* `L~` - return a list the most recent posts on the server
  * e.g. `L~`
* `Lx,y,z~` - return a list of posts with post IDs x, y and z
  * e.g. `L24,25,26~`
  * e.g. `L24,27,28~`
* `Ln~` - return a list of posts with the post id n, i.e. just one line
  * e.g. `L405~`
* `LEn~` - return a list of posts with the post id n, i.e. just one line
  * e.g. `LE405~`
  * This format is deprecated in favour of the Ln~ form
* `MEyymdd~` - return a list of posts created on the date yy-m-dd where m is 1 to 9 then A, B & C
  * e.g. `ME22C25~`
* `LGn~` - return a list of all posts starting with an id greater than n
  * e.g. `LG405~`
* `MGyymdd~` - return a list of all posts created after yy-m-dd where m is 1 to 9 then A, B & C
  * e.g. `MG22C25~`
* `E~` - return an extended list of the most recent posts on the server
  * e.g. `E~`
  * This format is deprecated in favour of the En~ form
* `Ex,y,z~` - return an extended list of posts with post IDs x, y and z
  * e.g. `E24,25,26~`
  * e.g. `E24,27,28~`
* `En~` - return an extended list of posts with the post id n, i.e. just one line
  * e.g. `E405~`
  * This format is deprecated in favour of the En~ form
* `EEn~` - return an extended list of posts with the post id n, i.e. just one line
  * e.g. `EE405~`
* `FEyymdd~` - return an extended list of posts created on the date yy-m-dd where m is 1 to 9 then A, B & C
  * e.g. `FE22C25~`
* `EGn~` - return an extended format list of all posts starting with an id greater than n; n can be 0 to 200000
  * e.g. `EG405~`
* `FGyymdd~` - return an extended format list of all posts created after yy-m-dd where m is 1 to 9 then A, B & C
  * e.g. `FG22C25~`
* `GEn~` - return the content of the post with the id n
  * e.g. `GE412~`

## MB Server Announcement
The server can send an announcement to the @MB call group.  An announcement contains the ID of the latest post.

An example is - `@MB 29`

The @MB announcement mechanism is controlled by three configuration parameters in settings.py:

* `announce` - switches the mechanism on and off; default is True which means on
* `mb_announcement_timer` - sets the delay, in minutes, between announcements; default is 60 mins

For a user to receive these announcements, they must add the @MB group to the Call Activity list in JS8Call.  To do this, right click in the list and choose Add new Station or Group... then enter @MB into the pop-up box and click OK.

## MB Server Query

Depending on the announcement timers used, an operator may have to wait
some considerable time before discovering contactable servers.  To avoid this
wait, the user can send the letter Q (for Query) to the @MB group.  Servers
receiving this command will immediately send an @MB announcement.

e.g. `@MB Q`

## Microblog Post File
A microblog post can contain any text content.  All text will be encoded as UTF8 and lower case letters will be shifted to upper case on transmission.

The post file name must start with the blog ID and a date like this:

`nnnn - yyy-mm-dd - Your chosen summary test`

Although we show four digits above for the reference (nnnn), the server supports any number of digits up to a value of 2000000000.

## Weather File
MbServer can deliver weather information, which the user requests with `M.WX`.  The file name must be:

`0000 - Current Weather.txt`

The content can be any text supported by JS8Call.  The sample directory contains an example of a
current weather file.

## Installation

* Clone the repo or download the zip file from here - https://github.com/PaulOfford/mbserver
  * Click on the green Clone button
* In settings.py, change the posts_dir variable to reflect the location of your posts
directory - note the use of \\\\ in Windows paths\*
* In JS8Call go to *File -> Settings -> Reporting*
* In the API section check Enable TCP Server API and Accept TCP Request
* In JS8Call, go to *File -> Settings -> General -> Networking & Autoreply -> Idle timeout - 
  disable autoreply after:* Click and hold the down arrow scroll icon until the value shows as Disabled
* In JS8Call, go to *File -> Settings -> General -> Station -> Callsign Groups (comma separated)* add
  `@MB`
* Click OK to save all JS8Call settings
* In JS8Call, click the **Deselect** button to ensure no stations are selected.
* Open a command box, `cd` to the directory containing the MbServer code
* Run the mb_server.py script with the command `python mb_server.py`

Your station is now ready to accept calls for microblog posts.

\* Prior to version 0.17.0, there were additional steps to create a posts directory and then to copy sample
data into that directory.  MbServer now comes pre-configured to deliver sample posts from the sample
posts directory that is in the downloaded package.  This change was made to provide a simpler installation
for those just wanting to try MbServer. You can, of course, move this directory to wherever you prefer and
populate it with your own posts. 

## Running the server
You don't need to stop the server to add a new post to the posts directory; the server will check the list of posts on each request and update the latest post information in the next @MB announcement.

**Important:** The Outgoing Message area in the server JS8Call **must not be** in the DIRECTED MESSAGE mode.  If it is, all messages, including @MB announcements, will be prefixed with the callsign of whichever station you have selected. 

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
