# Microblog Server (MbServer) Overview
In a video published in January 2023, Julian (OH8STN) shared an idea
he had regarding the use of data mode radio to share information in the
same way as you might share using social media.  Julian has a particular
interest in emergency comms and his idea is to provide a microblogging
facility that's decentralised and does not require the Internet.

The code here is a very simple (maybe simplistic) server.  MbServer supports
several request types:

* List the microblog posts available
* List the posts with the date of each in the listing
* Get the contents of a post
* Get a weather report
* Ask all MbServers to announce themselves

The server uses JS8Call to provide the transport mechanism.  The server
interfaces with JS8Call using the latter's API, accessed via TCP, i.e.
MbServer makes a TCP connection to JS8Call.  By default, the API is at
IP address 127.0.0.1 and TCP port 2442.

# Before you get started
Before you try this code, there are three videos you are going to want
to watch:
* Off Grid Ham Radio Micro Blogging with JS8Call &
VARAC - https://youtu.be/szZlPL2h534
* Microblogging playlist on
YouTube - https://www.youtube.com/playlist?list=PLSTO76Gp9qydUZA8euqe7O9Fd_O0U8yST

# Using a Microblog Server

To access te content of a blog, you send requests to the server, and it
responds with the information requested. Requests can be in one of
two formats:

* Command Line Interface (CLI) - typically sent from the Outgoing
Message Box of JS8Call on a client machine
* Application Program Interface (API) - typically sent from an
application (such as MbClient) running on the client
machine and communicating using JS8

The client SHOULD NOT switch between formats during a conversation.
Although this may work, there is no guarantee it
will work in the future.

The commands must be directed to the server, i.e. prefixed with the
server station callsign.  An exception is use of the callsign group @MB.
We'll cover this later in this document under header MB Server Query.
@ALLCALL is not supported.  JS8Call can be used by the server station
operator in the normal way, albeit once any outstanding microblog requests
have been satisfied.  MbServer simply ignores all received
messages that don't match the defined command formats.  This is an
important point as **the requestor will not receive an error message
if the command is incorrect**.  This is intentional to allow for the
widest range of normal JS8Call messages.

## Command Line Interface (CLI)
An operator can use the standard JS8Call Outgoing Message Area to send the
following commands to a microblog server:

* `M.L` - list the five most recent blogs
  * The range of this list can be changed by changing lst_limit in config.ini
* `M.L yyyy-mm-dd` - list all posts dated yyyy-mm-dd
* `M.E` - as per M.L but with list entries that include the date of the post
* `M.E yyyy-mm-dd` - as per M.L but with list entries that include the date
of the post
* `M.G n` - get the post with the id n
* `M.WX` - get the post with the id 0 which contains weather information


M.LST, M.EXT and M.GET are no longer supported.  The MB.xxx form has also
been dropped to reduce the amount of code to maintain.  All M.L commands
are deprecated to M.E; in other words if the server receives an M.L command
it will translate it to an M.E command.

Earlier versions of the CLI included a CLI parser and parameter checking.
Revision 9 included a significant rewrite of the CLI such that the CLI now
just translates requests into the API form and checking is done in the API.
This provides better code layering and reduces the amount of code to maintain.

## Application Program Interface (API)
Command formats are as follows:

* `E~` - return a listing of the five most recent posts on the server
  * e.g. `E~`
* `En~` - return a listing for the post id n
  * e.g. `E405~`
* `Ex,y,z~` - return a listing for posts with post IDs x, y and z
  * e.g. `E24,25,26~`
  * e.g. `E24,27,28~`
* `Eyyyy-mm-dd~` - return a listing for posts with post date of yyyy-mm-dd
  * e.g. `E2026-01-25~`
* `Gn~` - return the content of post id n
  * e.g. `G405~`
* `WX~` - return the content of post id 0

## MbServer Announcement
The server can send an announcement to the @MB call group.
An announcement contains the ID of the latest post and its date in
yymmdd format.

An example is - `@MB 29 260127`

The @MB announcement mechanism is controlled by two configuration
parameters in config.ini:

* `announce` - switches the mechanism on and off; default is True which
means on
* `mb_announcement_timer` - sets the delay, in minutes, between
announcements; default is 60 mins

For a user to receive these announcements, they must add the @MB group
to the Call Activity list in JS8Call. To do this, right click in the list
and choose *Add new Station or Group...* then enter @MB into the pop-up box
and click OK.

## MB Server Query

Depending on the announcement timers used, an operator may have to wait
some considerable time before discovering contactable servers.  To avoid this
wait, the user can send the letter Q (for Query) to the @MB group.  Servers
receiving this command will immediately send an @MB announcement.

e.g. `@MB Q`
