# Managing the Server Content

## Microblog Post File
A microblog post can contain any text content.  All text will be encoded as
UTF8 and lower case letters will be shifted to upper case on transmission.

The post file name must start with the blog ID and a date like this:

`nnnn - yyyy-mm-dd - Your chosen summary text`

Although we show four digits above for the reference (nnnn), the server
supports any number of digits up to a value of 2000000000.

## Weather File
MbServer can deliver weather information, which the user requests with `M.WX`.
The file name must be:

`0000 - 2026-01-27 - Current Weather.txt`

The content can be any text supported by JS8Call.  The sample directory
contains an example of a current weather file.

## Post File Store
The posts delivered by MbServer are held in a local directory on the computer
running the server.  These can be created locally using our favourite
text editor.  Alternatively, we can store the posts in an upstream store,
and have our MbServer check the store for new posts and download them into
the local directory.

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

## Making a New Post Live
You don't need to stop the server to add a new post to the posts directory;
the server will check the list of posts on each request and update the latest
post information in the next @MB announcement.

## Upstream Store
You can create the content of your posts directly in the posts directory of
you MbServer computer.  Alternatively, you can pull the posts from and upstream
store:

* The upstream store must be a web server
* The blogs must be stored as text file with an extension of `.txt`
* A text file called post.lst contains a list of all the posts you want to
make available to users

The root location of the upstream store is defined in `config.ini` as
`posts_url_root`

e.g. https://pauloffordracing.com/wp-content/uploads/microblog_posts/

The url shown above is a live store and can be used for testing.  Excuse
the rather confusing site name - this is the only website I have available.

The MbServer operates like this:

1. The @MB Announcement timer expires
2. MbServer gets the `post.lst` file from the upstream server
3. MbServer checks the list in `post.lst` against its local store to see if
there are new posts to get
4. MbServer gets new posts from the upstream server
5. MbServer sends the @MB Announcement with the new status

# Logging

MbServer uses the Python standard library `logging` module.

Logging configuration lives in `config.ini`:

- `LOG_LEVEL` (e.g. `logging.INFO`, `logging.DEBUG`)
- `LOG_TO_FILE` (True/False)
- `LOG_FILE` (default `logs/mbserver.log`)
- `LOG_MAX_BYTES` (rotate when file reaches this size)
- `LOG_BACKUP_COUNT` (how many rotated logs to keep)
