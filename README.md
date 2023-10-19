# Microblog Server (MbServer)
In a video published in January 2023, Julian (OH8STN) shared an idea he had regarding the use of data mode radio to
share information in the same way as you might share using social media.  Julian has a particular interest in emergency
comms and his idea is to provide a microblogging facility that's decentralised and does not require the Internet.

The code here is a very simple (maybe simplistic) server.  MbServer supports several request types:

* List the microblog posts available
* List the posts with the date of each in the listing
* Get the contents of a post
* Get a weather report
* Ask all MbServers to announce themselves

The server uses JS8Call to provide the transport mechanism.  The server interfaces with JS8Call using the latter's API,
accessed via TCP, i.e. mb_server makes a TCP connection to JS8Call.  By default, the API is at IP address 127.0.0.1 and
TCP port 2442.

I have included brief details of the JS8Call command verbs and response types below.

There's an important note about the state of the Outgoing Messages area in the section Running the Server - please read
this.

## Before you get started
Before you try this code, there are three videos you are going to want to watch:
* Off Grid Ham Radio Micro Blogging with JS8Call & VARAC - https://youtu.be/szZlPL2h534
* Microblogging Quick Start - https://youtu.be/URtUwvGok1Q
* Introduction to MbServer - https://youtu.be/usFkt7Kcs_g

## Microblog Commands

Commands can be in one of two formats:

* Command Line Interface (CLI) - typically sent from the Outgoing Message Box of JS8Call on a client machine
* Application Program Interface (API) - typically sent from an application (such as MbClient) running on the client
* machine and communicating using JS8

The client SHOULD NOT switch between formats during a conversation.  Although this may work, there is no guarantee it
will work in the future.

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

For a user to receive these announcements, they must add the @MB group to the Call Activity list in JS8Call.
To do this, right click in the list and choose Add new Station or Group... then enter @MB into the pop-up box
and click OK.

## MB Server Query

Depending on the announcement timers used, an operator may have to wait
some considerable time before discovering contactable servers.  To avoid this
wait, the user can send the letter Q (for Query) to the @MB group.  Servers
receiving this command will immediately send an @MB announcement.

e.g. `@MB Q`

## Microblog Post File
A microblog post can contain any text content.  All text will be encoded as UTF8 and lower case letters will be shifted
to upper case on transmission.

The post file name must start with the blog ID and a date like this:

`nnnn - yyy-mm-dd - Your chosen summary text`

Although we show four digits above for the reference (nnnn), the server supports any number of digits up to a value
of 2000000000.

## Weather File
MbServer can deliver weather information, which the user requests with `M.WX`.  The file name must be:

`0000 - Current Weather.txt`

The content can be any text supported by JS8Call.  The sample directory contains an example of a
current weather file.

## Post File Store
The posts delivered by MbServer are held in a local directory on the computer running the server.  These can be created
locally using our favourite text editor.  Alternatively, we can store the posts in an upstream store, and have our
MbServer check the store for new posts and download them into the local directory.  The upstream store can be one of
two types:

* A web server - available from version 0.18.0 onwards
* Another MbServer - future

The mechanism doesn't make any change to the Current Weather file.

### Upstream Web Server
The solution has the following characteristics:

* The central store must be a web server
* The blogs are stored as text file with extension of *.txt
* A text file called post.lst contains a list of all the posts in the store

The root location of the upstream store is defined in server_settings as posts_url_root.  The blog name is appended to
the root so that multiple blogs can be stored on a single server at the same root location. The construction of a fully
qualified URL operates like this:

* The root is, say, https://pauloffordracing.com/wp-content/uploads/microblog_posts/
* The blog is, say, M0PXO
* The url for the post list becomes https://pauloffordracing.com/wp-content/uploads/microblog_posts/M0PXO/post.lst

The root shown above is a live store and can be used for testing.  Excuse the rather confusing site name - this was
the only website I had available.

The MbServer operates like this:

1. The @mb Announcement timer expires
1. MbServer gets the post.lst file from the upstream server
1. MbServer checks the list in post.lst against its local store to see if there are new posts to get
1. MbServer gets new posts from the upstream server
1. MbServer sends the @mb Announcement with the new status

### Upstream MbServer
Future development.

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

## RAD Error Detection/Correction
**This functionality has not yet been added to MbServer or MbClient**
### Terminology
* Request - a command flowing from MbClient to MbServer
* Response - data flowing from an MbServer to an MbClient
* Message - a microblog request or response
* Cell - a fixed size fragment of a message and the smallest piece of a message that can be retransmitted
* Segment - a part of a message that comprises up to 36 cells
  * A message comprises one or more segments which, in turn, comprise multiple cells
* Sender - a program (e.g. MbClient or MbServer) that is sending a message
* Receiver - a program (e.g. MbClient or MbServer) that is receiving a message
  * Note that, in this case, receiver doesn't mean your radio/transceiver
* Partners - a pair of sender and receiver programs that are communicating with each other
* RDA-encode - split a message into segments and cells

### Introduction
JS8 over HF radio can be lossy.  When sending keyboard-to-keyboard or messages to an
inbox, the impact of such loss is probably small - humans can tolerate a fair amount
of corruption in a message.  Microblogging is a little different because:
* In an em-comms situation, accurate information is critical
* Microblog messages are quite long and so requesting the retransmission of an entire listing or post is tedious
* Frustration in needing to retransmit entire messages will be exacerbated by the planned support for post uploads 

Here we document a proposed **Reliable Application Data (RAD)** protocol.  I (M0PXO) considered designing RAD as a
transport protocol, similar to TCP, but this would mean enveloping the application messages in another header, and
the overhead would be unacceptable.
<pre>
+--------------------------------------------------------------------------------------------------------------+
|                                                  MESSAGE                                                     |
+--------------------------------------------------------------------------------------------------------------+
|                                SEGEMENT                            |                SEGMENT                  |
+--------------------------------------------------------------------------------------------------------------+
| CELL * CELL *             total of 36 cells          * CELL * CELL | CELL * CELL * CELL * CELL * CELL * CELL |
+--------------------------------------------------------------------------------------------------------------+
</pre>
RAD uses a mechanism whereby
an application message (such as List output) is, ultimately, split into cells.  Each cell has a single character
cell_id plus a fragment of application data.  A receiver detects loss of cells by determining discontiguous cells
based on the cell_id.  The receiver then requests retransmission of the missing cells.

**NB:** Cells are not the same as JS8 frames.  Cells may occasionally align with JS8 frames, but mostly will not.

Cells are grouped into segments to allow for longer messages to be sent without needing to use large cell sizes.  Cell
sizes are covered in more detail below. 

**This is work in progress.**

### Design Considerations
Design considerations are:
* Minimal overhead, bearing in mind the data rates
* Preferably, stateless operation

So that the sending station can retransmits fragments of a message, protocols like TCP hold a copy of the original
fragments (called _segments_ in TCP) until successful reception has been acknowledged.  To allow the server to be
stateless, we should avoid the need for such a mechanism.

The receiving program needs to be able to deal with the following scenarios:
* Loss of a JS8 frame
* Loss of multiple non-contiguous JS8 frames
* Loss of contiguous JS8 frames
* Loss of a segment header
* Loss of multiple segment headers
* Loss of a segment header and the following JS8 frame(s)

Where possible, we send a request to the message sender asking it to **retransmit the missing
cells**. If this is not possible, we need backstops that request:
* Retransmission of a segment
* Retransmission of the entire message

### RAD Protocol
#### Message Format
The format of an application message that has been encoded to use RAD is:
<pre>
+--------------------------------------------------------------------------------------------------------------+
|sender: receiver |seg_id|cell_id|content|cell_id|content| ... |seg_id|cell_id|content| ... |cell_id|content| ♢|
+--------------------------------------------------------------------------------------------------------------+
</pre>
Example:

`M0PXO: 2E0FGO 050+L13~1\n\n13 22023-310-124 GAZA5 - UN6 CONC7ERNS 8OVER 9IDF OARDER  ♢`

**Sender and Receiver**
It's assumed that the sender and receiver strings are correct since (a) we
would not receive the message if they were not correct, and (b) we can't mess with this area as it would cause
problems with JS8Call.  These values, therefore, fall outside the RAD encoding.

**Segments**
The remainder of the message is split into up to 36 segments.  Each segment has a seg_id of
0 to 9 then A to Z.

**Cells**
Each segment is further subdivided into fixed width cells
that can be from 3 to 35 characters in length.  Empty positions in a
cell are padded with blanks, which should only occur in the last cell
of the last segment. Each cell has a cell_id of 0 to 9
then A to Z. Where the cell size appears in a RAD message, it too is
encoded as 0-9 and then A-Z, hence a maximum cell size of 35 characters.

**Terminator**
The standard JS8 terminator (by default space followed by a diamond - ♢)
indicates the end of the message.  The terminator falls outside the
segment and cell structure.

#### List, Extended List & Get
The Reliable Application Data (RAD) protocol requires commands to be modified by suffixing the command with the cell
size. Here are some examples:
* `L24,25,26~5` - a listing request using RAD with a cell size of 5 characters
* `EG405~G` - an extended listing request using RAD with a cell size of 16 characters
* `GE412~8` - a get request using RAD with a cell size of 8 characters

Note that a character immediately after the tilde (~) character specifies the cell size and, by implication,
the use of RAD.

If a retransmission is needed, the request is sent again with a list of segments and cells appended to the command.

`cmd~cell_size seg_id cell_id seg_id cell_id ` - the spaces have been added here for readability.  Here are some
examples:
* `L24,25,26~5020Z1F` - a retransmission request asking that seg 0 cell 2, seg 0 cell 35 and seg 1 cell 15 be resent
* `GE412~80.` - a retransmision request asking that all of segment 0 be resent - period (.) means all cells
* `EG405~G.` - a retransmision request asking that the entire message be resent

Resending the command avoids the server having to hold a copy of a transmitted message until it has been acknowledged,
and so maintains the stateless nature of client requests to the server.

There is one foreseen issue - here is the scenario.
* The command L~ or E~ is sent by the client
* The server responds with a listing accurate at that point in time
* Another post is added to the blog
* The server receives a request to retransmit cells for the L~ or E~ command

Because a new post has been added, the listing will cover different posts and so the cells referenced will be incorrect.
This means that the L~ and E~ commands cannot be used with RAD.

The sender doesn't determine if messages or retransmitted segments have been successfully received.  The receiver is
responsible for all aspects of message reception and the need for retransmission.

#### Upload
This is for development.  Early thoughts are:
* The upload request would include the blog name, file name and file content
  * Maybe use the letter P for Put, i.e. the opposite of Get
* The client would RDA-encode the request (split into segments and cells) and send it
* The server would allocate a post ID and save the message
* The server would send a positive acknowledgement with the original command letter and the allocated post id
  * e.g. +P52
* If frames are lost, the server would hold all received cells and request those missing:
  * e.g. -P0.1A - resend all of seg 0 and seg 1 cell 10 using the original cell size

This means the client would need to:
* Maintain a copy of the upload message
* Wait for a positive acknowledgement before it could send further files.

#### Cell Size and Max Message Length
The maximum application message length is given by:

`max_length = 36 segments * 36 cells * cell_size`

With a cell size of 5, the maximum message length is 6,480.  With a cell size of 35, the maximum message length is
about 42k.  Both of these numbers are plainly much more than is needed.

I (M0PXO) considered abandoning the segment
mechanism as this would greatly simplify the receiver code. With a cell size of 5 and a single segment, the maximum
message length would be 180 characters.  Even with a cell size of 10, the maximum message length would be just 360
characters and I feel this is just not quite enough.

It's not yet clear what the optimum cell size might be, and is likely to vary depending on loss rate. The code is
implemented in a way that allows the cell size to be dynamic, i.e. change as loss rates or SNR varies. It's likely that
the optimum cell size, from a retransmission perspective, will be a length similar to that of a JS8 frame,
and so in the range of 3 to 8 characters.  Such sizes would introduce a large overhead (8-character cells increasing
the message size by about 12%).  Larger cell sizes would reduce the overhead but increase the time taken for
retransmissions.  Here we see the principle trade-off, and the reason why it would be better for the cell size to
adapt to the JS8 frame loss rate.

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
