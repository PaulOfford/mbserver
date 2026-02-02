# Changes

## Release 0.21.0

This release introduces some important changes:

* The server is now started using a Windows batch file mbserver.bat
  * `.\mbserver.bat`
* Settings have been moved to a standard style config.ini file
* The short form listing option (L) has been deprecated
to produce an extended listing (E) 
* The options listing have been reduced, with the discontinuation of 
the "greater than" options
* The WX command is still supported but the name of the weather file
must now include the date like any other post:
  * `0000 - 2026-01-27 - Current Weather.txt`
* The location of the code has been changed such that the main code
has moved to package 
* The development of the RAD protocol has been abandoned

# Installation

* Download the zip file from here - https://github.com/PaulOfford/mbserver
  * Click on the green Code button
* In config.ini, change the posts_dir variable to reflect the location of
your posts directory - note the use of \\\\ in Windows paths\*
* In JS8Call go to *File -> Settings -> Reporting*
* In the API section check Enable TCP Server API and Accept TCP Request
* In JS8Call, go to *File -> Settings -> General -> Networking & Autoreply -> Idle timeout - 
  disable autoreply after:* Click and hold the down arrow scroll icon until the value shows as Disabled
* In JS8Call, go to *File -> Settings -> General -> Station -> Callsign Groups (comma separated)* add
  `@MB`
* Click OK to save all JS8Call settings
* In JS8Call, click the **Deselect** button to ensure no stations are selected.
* Open a command box, `cd` to the directory containing the MbServer code
* Start the server with `.\mbserver.bat`

Your station is now ready to accept calls for microblog posts.

# Command-line overrides

You can override logging at runtime:

- `--log-level DEBUG|INFO|WARNING|ERROR|CRITICAL` (or a numeric level)
- `--log-file /path/to/mbserver.log`
- `--no-log-file`
- `--max-log-bytes N`
- `--log-backups N`

You can also override the TCP port that MbServer connects to:

- `--tcp-port _port_no_`

This is useful if you have JS8Call TCP Server Port set to something other than 2442 during testing.
