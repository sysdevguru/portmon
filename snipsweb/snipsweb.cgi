#!/usr/local/bin/perl
#
# $Header: /home/cvsroot/snips/snipsweb/snipsweb.cgi,v 1.5 2003/10/20 12:24:06 russell Exp $
#
#			snipsweb.cgi
#
# A CGI script which interfaces with the html generated by the snips web
# script 'genweb.cgi'.
# This script is the companion to genweb.cgi. It allows administrator to add
# status messages and to 'hide' devices as well as rudimentary troubleshooting.
#
####
# IMPORTANT: You MUST RESTRICT ACCESS TO THIS SCRIPT USING .htaccess or
#	the $authfile since this file gives access to various files and
#	programs on your system.
####
# Status Messages:
# 	A status message may be displayed next to a device alerting others
# as to the outage reason and duration. These status messages are, by default
# stored in the file $snipsroot/etc/updates. This file must be writable by
# your web server (often user nobody).
#
# Hiding Devices:
# 	If a device is going to be down for an extended time, you can 'hide'
# it from the critical view to keep it uncluttered. It still shows up in the
# other views. This program inserts a (H) in the 'updates' file to indicate
# that the event should be hidden.
#
# Device history:
#	This script can 'grep' for the devicename + deviceaddr in the snips
# logs (generated by snipslogd). You should set $logfile to point to any
# logfile which has the most complete information about all the events
# (typically the one at the info level since that will have info about
# all the levels).
#
# Troubleshoot:
#	You can do a ping or traceroute or nslookup on the deviceaddr. These
# commands can take a lot of time (and html will not return until the command
# is complete). Customize these commands, and make sure you specify the proper
# options to prevent these commands from running forever (e.g.ping -s on SunOS)
#
# Graph:
#	This is a new option which plots the variables for a device
# using RRDtool. You must have 'rrdtool' installed on the system and
# the 'rrdgraph.cgi' installed in the cgi-bin/ dir (same place this cgi
# is located). You can get RRDtool from http://www.caida.org/Tools/
#
# Device Help:
#	This program searches for helpfiles under $snipsroot/device-help/. It
# searches for $devicename:$deviceaddr, $devicename:default, default:$deviceaddr
# default:$variable default:$sender and finally for default. You should
# create help files (which are HTML files and hence can have html tags
# in them).
#
#
# AUTHOR:
#	Originally written by Richard Beebe (richard.beebe@yale.edu) 1996
#      	Rewritten Vikas Aggarwal (vikas@navya.com) 1998
#
#   This script was distributed as part of the SNIPS package.
#
# INSTALLATION:
#	- Edit $snipsroot/etc/snipsweb-confg  for customizable options.
# 	- Put this in your CGI-BIN directory. If you put it in some other
#	  location, you must update the value of $snipsweb_cgi.
#	- Create a null $updatesfile $cookiefile and ensure that both are
#	  writable by httpd (or owner of your web daemon).
#	- Create a valid $authfile which lists the valid users in it.
#	- Customize the locations and program syntaxes in the routine
#	  doTroubleshoot() below. Disable the commands if you dont want to
#	  offer access to them (search for check_this).
#	- Change $logfile to point to the 'info' or 'critical' level LOG file
#	  You can get this filename from your /snips/etc/snipslogd-conf entry
#	  for info level logging.
#	- If you are using the traditional .htaccess method of access
#	  control, then you should comment out @OK_REFERERS or set it
#	  to an empty list. Else, list the URL of snipsweb.cgi in
#	  @OK_REFERERS so that this script will only trust information
#	  if it comes from these URLs.
#
####
#############################################################################

## CUSTOMIZE THE LOCATION OF THIS CGI-SCRIPT AS SEEN BY httpd. This MUST
## run on the same host as SNIPS since this script needs to access the
## snips data files.
# Remember to create the $updatesfile and the $authfile and also the
# help files.

# Global variables.
use strict;
use vars qw (
	     $snipsroot $etcdir $snipsweb_cgi $rrdgraph_cgi $logfile
	     $helpdir $updatesfile $authfile $cookiefile $debug $ldebug
	     $command $subdevice $devicename $deviceaddr $variable
	     $done_footer $userlevel $cookiehdr $RRD_DBDIR
	     @OK_REFERER %FORM
	    );
BEGIN {
  $snipsroot = "/usr/local/snips"  unless $snipsroot;	# SET_THIS
  push (@INC, "$snipsroot/etc"); push (@INC, "$snipsroot/bin");
  require  "snipsperl.conf" ;		# local customizations
  require  "snipsweb-confg";	# all WEB configurable options
}

# CHECK functions allowed in &doTroubleshoot() subroutine below.

#$snipsweb_cgi = "http://www.host.com/cgi-bin/snipsweb.cgi";
$snipsweb_cgi = "/cgi-bin/snipsweb.cgi" unless $snipsweb_cgi;
$rrdgraph_cgi = "/cgi-bin/rrdgraph.cgi" unless $rrdgraph_cgi;
# this should be the info level snipslogd log file.
$logfile = "$snipsroot/logs/info";		# CHECK_this

# if you have RRDtool installed. Comment out if not needed.
# This invokes the 'graph' option.
$RRD_DBDIR = "$snipsroot/rrddata";	# SET_THIS to dir of rrd data files

## For security, set OK_REFERER to the URL of snipsweb.cgi. This script
# will then only run if its been called from snipsweb.cgi. Comment out
# or set to a null list to ignore.
#
#@OK_REFERER = ($snipsweb_cgi,
#	       "http://localhost/cgi-bin/snipsweb.cgi",
#	       "http://www.host.com/cgi-bin/snipsweb.cgi");	# SET_THIS
@OK_REFERER = () unless @OK_REFERER;

$helpdir = "$snipsroot/device-help";	# dir for device help files
$updatesfile = "$etcdir/updates";	# all update messages
$authfile = "$snipsroot/etc/webusers";	# user:passwd:userlevel
$cookiefile = "$snipsroot/etc/webcookies";

$ldebug = $debug if ($debug);

#------------------------------------------------------------
## Look in authfile for username and determine userlevel. Format of 
# this file is:
#	user : password : userLevel
# If REMOTE_USER is set by the httpd daemon, then assume that the
# user was authenticated already by the .htaccess or equivalent.
# Else if cookie is set, check in 'cookiefile' and use that.
#
# If authfile does not exist it denies access. If not authenticated, it calls
# &print_auth_form(). If browser does not support cookies, then you *must*
# use the httpd daemons authentication method since there is no other choice.
# 
sub set_userlevel {

  if (@OK_REFERER) {
    # quick and fast,, however the HTTP_REFERER needs to be trimmed
    # before checking.
    my $referer = (split('\?', $ENV{'HTTP_REFERER'}))[0];
    $referer = "NoHost" if (! $referer);
    if (grep (/^${referer}$/i, @OK_REFERER) > 0 &&
        $FORM{'userlevel'} ne "" && $FORM{'user'} ne "")
    {
      $userlevel = int($FORM{'userlevel'});
      print STDERR "set_userlevel() HTTP_REFERER = $referer listed in OK_REFERER,",
	"permitting and userlevel = $userlevel\n" if ($ldebug);
      return;
    }
  }

  if ($ENV{'REMOTE_USER'} ne "")	# user already authenticated by httpd
  {
    my $user = $ENV{'REMOTE_USER'};
    $FORM{'user'} = $ENV{'REMOTE_USER'};
    if (! open (AUTH, "< $authfile")) {
      &denyAccess("Cannot open $authfile $!, please contact device admin\n");
    }
    while (<AUTH>) {
      if (/^$user\:/)
      {
	my ($junk, $junk, $file_userlevel) = split /:/;
	$userlevel = int($file_userlevel);
	$FORM{'userlevel'} = $file_userlevel;
	close(AUTH);
	print STDERR "set_userlevel() REMOTE_USER = $user authenticated using .htaccess,",
	  "userlevel = $userlevel\n" if ($ldebug);
	return;
      }
    }
    close(AUTH);
  }

  # See if our cookie is set, check and use that
  my (%cookievars) = ();
  foreach (split(/\s*;\s*/, $ENV{'HTTP_COOKIE'})) {
    chomp;
    my($var, $val) = split('=');
    $cookievars{$var} = $val;
  }
  &print_auth_form if (! defined $cookievars{'snipsauth'} );   # if no cookie
  open(COOKIE, "< $cookiefile") || &print_auth_form;
  my $cookie = $cookievars{'snipsauth'};
  while (<COOKIE>) {
    if (/^$cookie\:/)
    {
      my ($file_cookie, $file_user, $file_userlevel, $file_age) = split /:/;
      $FORM{'user'} = $file_user;
      $userlevel = int($file_userlevel);
      $FORM{'userlevel'} = $file_userlevel;
      print STDERR "set_userlevel() cookie = $cookie, ",
	"userlevel set to $userlevel\n" if ($ldebug);
      close(COOKIE);
      return;
    }
  }
  close(COOKIE);

  # if we reach here, we need to get the user's information since he/she
  # was not authenticated by httpd or with a valid cookie
  print STDERR "set_userlevel() user not authenticated\n" if ($ldebug);
  &print_auth_form;
  return;
}	# authcheck()

#------------------------------------------------------------
## Check username and password and return a cookie if valid
#  Store the cookie in $cookiefile. Also expire old cookies while
#  we are working with the cookie file.
sub doAuthenticate {
  my $user = $FORM{'user'};
  my $found = 0;
  my $localtime = time;
  my $max_cookie_age = 86400;	# delete if one day old

  if ($FORM{'subcommand'} eq "Cancel") { &restoreView; exit 0; }

  &denyAccess('No username specified') if ($user eq "");
  open (AUTH, "< $authfile") || &denyAccess("Cannot open $authfile, contact device administrator $ENV{'SERVER_ADMIN'}");
  while (<AUTH>)
  {
    next if (! /^$user\:/);
    my ($file_user, $file_passwd, $file_userlevel) = split /:/;
    if ($file_passwd eq "")
    {
      $userlevel = int($file_userlevel);
      $found = 1;
    }
    else
    {
      my $salt = substr($file_passwd, 0, 2);
      my $encrypt_pass = crypt($FORM{'password'}, $salt);
      if ($encrypt_pass eq $file_passwd)
      {
	$userlevel = int($file_userlevel);
	$found = 1;
      }
      else { &denyAccess("Invalid password"); }
    }
    last;
  }	# while(AUTH)
  close(AUTH);

  $FORM{'userlevel'} = $userlevel;
  if (!$found) { &print_auth_form; }

  ## now generate a cookie and store in the cookie file
  my $newcookie = $localtime ^ $$ ^ $ENV{'REMOTE_PORT'};
  $newcookie .= "snips";
  # header string used by '&print_button_header'
  $cookiehdr = "Set-Cookie: snipsauth=$newcookie; path=$snipsweb_cgi;";

  my @cookies;
  if (open(COOKIE, "< $cookiefile")) {
    @cookies = <COOKIE>;	# slurp into memory
    close (COOKIE);
  }
  if (! open (COOKIE, ">> $cookiefile"))
  { 
    &denyAccess("Error- cannot open $cookiefile for writing, $!. Report this error to this web device administrator $ENV{'SERVER_ADMIN'}");
  }

  foreach (1..3) {	# try locking the file three times...
    if (flock(COOKIE, 2)) {
      seek(COOKIE, 0, 0);
      truncate(COOKIE, 0);
      last;
    }
    &denyAccess("Error- cannot open $cookiefile for flock access, report error to admin")     if ($_ == 3);
    sleep 1;
  }
  
  foreach (@cookies) {		# clean out old & expired cookies
    chop;
    # skip comments and blank lines
    if (/^\s*\#/ || /^\s*$/) { print COOKIE; next; }
    my ($file_cookie, $file_user, $file_userlevel, $file_age) = split /:/;
    next if ($file_age + $max_cookie_age < $localtime);
    print COOKIE "$file_cookie:$file_user:$file_userlevel:$file_age\n";
  }
  print COOKIE "$newcookie:$user:$userlevel:$localtime\n";
  close (COOKIE);

  ## here if user has been authenticated.
  &print_button_header;
  print "<b>User $user authenticated, user level $userlevel </b>\n";
  &print_footer;
  return;
}	# doAuthenticate()

#------------------------------------------------------------
## generate authentication form that the user has to fill out and EXIT.
sub print_auth_form {
  print "Content-type: text/html\n\n";
  print <<EoX;
  <html> <head> <title>Snips User Authorization </title> </head>
    <body>
      <h4> SNIPS User Authorization required: </h4>
	<FORM action="$snipsweb_cgi" method="post">
EoX
  &print_state_info;

  print <<EoXa;
  <b>Username:</b> &nbsp;
  <input type=text size=12 maxlength=12 name=user value=$FORM{'user'}> <br>
  <b>Password:</b> &nbsp;
  <input type=password size=12 maxlength=20 name=password value=""> <br>
  <input type=hidden name=command value="Authenticate">
  <input type=submit name=subcommand value="Submit">
  <input type=submit name=subcommand value="Cancel">
  </FORM>
EoXa

  &print_footer();
  exit 0;		# dont return, just exit
}

#------------------------------------------------------------
## print deny message and exit.
sub denyAccess {
  my ($denymesg) = @_;

  if ($denymesg =~ /^\s*$/) {
    $denymesg = "Command $command not permitted for $FORM{'user'} at user level $userlevel";
  }

  &print_button_header;
  print <<EoAUTH;
  <p> <center> <font color="red" size="+1">
    <b> $denymesg </b>
  </font></center> </p>
EoAUTH

  &print_footer;
  exit 0;
}

#------------------------------------------------------------
# print form buttons at the top of the page
#
sub print_button_header {
  print "Content-type: text/html\n";
  if ($cookiehdr ne "") {print "$cookiehdr\n"; }
  print "\n";

  print <<EoHeader;
  <html>
    <head><title>Snips View $FORM{devicename} $FORM{subdevice}</title></head>
      <body bgcolor="#ffffff">
	<center>
	  <FORM action="$snipsweb_cgi" method="post">

EoHeader
  &print_state_info;
  print "\t<font size=\"-1\">\n";		# font size for submit buttons
  if ($devicename ne "" || $deviceaddr ne "")	# only if some device
  {
    print <<EoHeadera;
	    <input type=submit name=command value="DeviceHelp">
	    <input type=submit name=command value="Updates">
	    <input type=submit name=command value="Device Logs">
	    <input type=submit name=command value="Troubleshoot">
	    <input type=submit name=command value="Graphs">
	    &nbsp;
EoHeadera
  }
  print <<EoHeaderb;
	    <input type=submit name=command value="SnipsView">
	    &nbsp; &nbsp;
	    <input type=submit name=command value="About Snips">
          </font>
	  </FORM>
          <hr noshade width="100%">
       </center> <P>
       <P align="right">
       <font size=\"+2\" color=\"#003366\">$command</font><p>

EoHeaderb
}	# print_button_header()

#------------------------------------------------------------
#
sub print_footer {
  return if ($done_footer == 1);
  my $foot = "$helpdir" . "/stdfoot";
  print "\n<P> <!-- begin stdfoot -->\n";
  if (open(FILE, "< $foot")) { print while (<FILE>) ; }

  if ($ldebug > 2 && $userlevel < 3) {
    print "<!-- debug output -->\n";
    print "<hr><h3>DEBUG OUTPUT</h3>\n";
    print "<p><b>Current userlevel = $userlevel</b> </p>";
    print "<p><h4>FORM Variables</h4>\n";
    for (keys %FORM) { print "<tt>$_ = $FORM{$_} </tt><br>" ;}
    print "<p><hr>\n <h4>ENV Variables</h4>\n";
    for (keys %ENV) { print "<tt>$_ = $ENV{$_} </tt><br>" ;}
  }

  print "\n </body>\n</html>\n";	# final closing
  $done_footer = 1;
}	# end sub(devicehelp)

#------------------------------------------------------------
# Print out the common FORM lines rquired to preserve the state  info
# across the various screens.
sub print_state_info {
  print <<EoState;
	 <input type=hidden name=devicename value="$FORM{devicename}">
	 <input type=hidden name=deviceaddr value="$FORM{deviceaddr}">
	 <input type=hidden name=subdevice value="$FORM{subdevice}">
	 <input type=hidden name=variable value="$FORM{variable}">
	 <input type=hidden name=sender value="$FORM{sender}">
	 <input type=hidden name=user value="$FORM{user}">
	 <input type=hidden name=userlevel value="$FORM{userlevel}">
	 <input type=hidden name=restoreurl value="$FORM{restoreurl}">
	 <input type=hidden name=displaylevel value="$FORM{displaylevel}">
EoState
}

#------------------------------------------------------------
# The viewer has clicked on a device looking for help on that
# device. Files are named by the devicename : deviceaddr
# If a file is not found for a device, we'll display the file "default:type"
# or just 'default'.
sub doDeviceHelp {
  my $helpfile;
  my $sender   = $FORM{'sender'};

  &denyAccess if ($userlevel > 4);
  &print_button_header();
  return if ($devicename eq "" || $deviceaddr eq "");
  print "<center><H3>$devicename : $deviceaddr : $variable</H3>\n";
  print "  <hr width=50\% align=center> <P>\n</center>\n";

  # find a help file. First a specific one, then try defaults
  foreach ("${devicename}:${deviceaddr}", "${devicename}:default",
	   "default:$deviceaddr", "default:$variable", "default:$sender",
	   "${devicename}", 'default:default', 'default')
  {
    if (-f "$helpdir/$_") { $helpfile = $_; last; }
  }

  if ($helpfile ne "" && open(HELP, "< $helpdir/$helpfile")) {
    print while (<HELP>) ;
  }
  else { print "<H3>Sorry, no device help is available!</H3>\n"; }

  &print_footer;

}  # doDeviceHelp()

#------------------------------------------------------------
## Print out the log entries from the 'info' level file. Cannot
#  grep through all the log files since the syslog style logging
#  means that the same entry might exist in multiple log files.
#
sub doHistory {

  my $cnt = 1;
  my $str;
  my @rowcolor = ("#CCCC99", "#D8D8D8");

  &denyAccess if ($userlevel > 3);
  &print_button_header();
  return if ($devicename eq "" || $deviceaddr eq "");
  print "<center><H3>$devicename : $deviceaddr : $variable</H3>\n";
  print "  <hr width=50\% align=center> <P>\n</center>\n";

  if ( (! -f "$logfile") || (! open(FILE, "< $logfile")) ) {
    print "<H3>Sorry, log file $logfile not available.<H3>\n";
    &print_footer;
    return;
  }
  print "<h4>Logfile: $logfile</h4>\n";
  print "<table cellpadding=3 cellspacing=1 border=0>\n<tr> ";
  foreach $str ('#', 'date', 'monitor', 'variable', 'value',
		'threshold', 'units', 'level')
  {
    print "<td><font face=\"arial,helvetica\" size=\"2\"><b>$str</b></font></td>\n";
  }
  print "</tr> <!-- $devicename $deviceaddr -->\n";

  while (<FILE>)
  {
    if ( /^(.*)\s+\[(.*)\]:\s+(SITE|DEVICE)\s+$devicename.*\s+$deviceaddr.*\s+VAR\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+LEVEL\s+(\S+)\s+/i )
    {
      print "<TR bgcolor=\"$rowcolor[$cnt % 2]\"> \n";
      foreach $str ($cnt, "$1", "$2", "$4", "$5", "$6", "$7", "$8") {
	print "\t <td><font face=\"arial,helvetica\" size=\"2\"> $str </font> </td> \n";
      }
      print "</TR>\n";
      ++$cnt;
    }
  }	# end while(<FILE>)

  print "</table>\n";

  close (FILE);
  &print_footer;

}  # doLogs()

#------------------------------------------------------------
# Edit the updatesFile (used to add a comment or hide a particular device
# from the display.
sub doUpdates {
  my ($junk, $explain) = (undef, '');
  my $ishideChecked = '';
  my $subdev = "";

  &denyAccess if ($userlevel > 1);
  &print_button_header();
  return if ($devicename eq "" || $deviceaddr eq "");
  if ($subdevice ne "") { $subdev = "${subdevice}+"; }
  print "<center><H3>${subdev}${devicename} : $deviceaddr : $variable</H3>\n";
  print "  <hr width=50\% align=center> <P>\n</center>\n";

  # update the status if we have a subcommand.
  if ($FORM{subcommand} ne "") { &updateStatus; }

  # now that we have updated the status file if required, get the
  # latest updated status from the updates file.
  if (open (INPUT, "< $updatesfile")) {
    while (<INPUT>) {
      chop;
      next if (/^\s*\#/);   # skip comments
      next if (/^\s*$/);   # skip blank lines
      ($junk, $explain) = split /\t/;
      last if ($junk =~ /^($subdevice\+)?$devicename\:$deviceaddr\:$variable/);
      $explain = "";	# reset/clear if not matched
    }
    close (INPUT);
  }

  if ($explain =~ /^\(H\)/) {
    $ishideChecked = 'CHECKED';
    $explain =~ s/^\(H\)\s+//o;	# strip out the (H) hidden part
  }
  $explain =~ s/^\s+// ; $explain =~ s/\s+$//;	# clean leading/trailing spaces
  $explain =~ s/\-\S*$//;	# remove -user from the end

  print <<UPDATEFORM;

	<H4>UPDATE STATUS:</H4>
	<P> Enter text that you would like to appear in the 'status' column
	of the snips display. Select the 'Hide' checkbox if this device is
	going to be down for an extended period and you would like to remove
	it from the CRITICAL view. It will still appear in other views.
	<P>
	<FORM action="$snipsweb_cgi" method="post">
	<P><input type=text size=30 maxlength=30 name=status value="$explain">
	<input type=checkbox name=Hide $ishideChecked >
	Hide this entry from Critical view
UPDATEFORM
   &print_state_info;
   print <<UPDATEFORMa;
	<input type=hidden name=command value="$command">
	<P><input type=submit name=subcommand value="change">
		Update this device to use this status
	<P><input type=submit name=subcommand value="clear">
		Remove this status message from this device 
	</FORM>
UPDATEFORMa

  &print_footer();

}	# doupdates()

#------------------------------------------------------------
# The 'action' called by the above form. This is the routine
# that actually updates the 'updates' file. Possibilities are:
#	- change entry (also can be marked as Hide)
#	- clear entry
sub updateStatus {
  my $subdev = "";

  return if ($devicename eq "" || $deviceaddr eq "");

  if (! open(SFILE, "< $updatesfile")) {
      print "<b>Cannot open $updatesfile - $!<b><p>";
      return;
  }

  if ($subdevice ne "") { $subdev = "${subdevice}+"; }
  my $newstatus = $FORM{status};
  $newstatus =~ s/^\s+// ;
  if ($newstatus eq "" && ! $FORM{Hide}) { $FORM{subcommand} = "clear"; }

  my @list = <SFILE>;	# slurp into memory
  close (SFILE);
  if (! open (SFILE, ">> $updatesfile") ) {
    print "<h4> Sorry, error writing $updatesfile - $! </h4>\n";
    return ;
  }
  foreach (1..3) {	# try locking the file three times...
    if (flock(SFILE, 2)) {
      seek(SFILE, 0, 0);
      truncate(SFILE, 0);
      last;
    }
    if ($_ == 3) {
      print "<font color=red><h4> Sorry, error locking $updatesfile </h4>\n";
      return;
    }
    sleep 1;	# try locking after a second
  }

  foreach (@list) {
    # delete/skip old entry
    next if (/^${subdev}${devicename}\:$deviceaddr\:$variable/);
    print SFILE;
  }
  if ($FORM{'subcommand'} =~ /^clear/i) {
    print "<p><b> &nbsp; (entry cleared)</b> Will clear after a minute<p>\n";
  }
  else {
    print SFILE "${subdev}${devicename}\:$deviceaddr\:$variable\t";
    if ($FORM{'Hide'}) { print SFILE "(H) "; }	# value of Hide checkbox
    if ($newstatus ne "") {print SFILE "$newstatus -$FORM{'user'}\n";}
    print "<p> <b> &nbsp; (entry updated)</b> Will display after a minute<p>\n";
  }

  close (SFILE);

}	# updateStatus()

#------------------------------------------------------------
## troubleshooting
# This runs external system commands, so please make sure that the
# external commands dont run forever. e.g ping has an option where it
# runs forever, so DONT use that option. Set the syntax, path.
# The keyword 'DEVICE' will be replaced by $deviceaddr. You can disable any
# command or add new ones by changing $cmdlist.
#
# e.g. on Sun's use '/usr/sbin/ping -s DEVICE 500 3' if you are not using
# multiping
sub doTroubleShoot {
  my $traceroute = "traceroute -m 15 DEVICE";
  my $ping = "$snipsroot/bin/multiping -c 3 -i 2 DEVICE";	# CHECK_this
  my $nslookup = "nslookup -query=any DEVICE";
  $nslookup = ($deviceaddr =~ /^[\d\.]+$/) ?
                         "nslookup DEVICE" : "nslookup -query=any DEVICE";

  my $subcmd;
  my %cmdlist = ("ping", $ping, "traceroute", $traceroute,
		  "nslookup", $nslookup);

  &denyAccess if ($userlevel > 2);
  &print_button_header;
  return if ($devicename eq "" || $deviceaddr eq "");
  print "<center><H3>$devicename : $deviceaddr : $variable</H3>\n";
  print "  <hr width=50\% align=center>\n</center>\n";
  print "<p> <i>Remember that you have to wait (for about 10 secs) while the command executes</i></p>\n";

  select((select(STDOUT), $| = 1)[0]);

  ## if the user has selected a subcommand for us to execute
  ($subcmd = $FORM{'subcommand'}) =~ tr/A-Z/a-z/;	# lowercase
  if ($subcmd ne "")
  {
    my $cmd = $cmdlist{$subcmd};
    my $linecnt = 0;	# to prevent runaway commands

    print "debug ($subcmd) Trying $cmd $deviceaddr<br>" if $ldebug;
    if ($cmd) {
      $deviceaddr =~ tr/[a-zA-Z0-9_.\-]//cd;	# strip unwanted characters
      if (!$deviceaddr || $deviceaddr eq '-') {
        $cmd =~ s/DEVICE/$devicename/ ;	# replace keyword with name
      } else {
        $cmd =~ s/DEVICE/$deviceaddr/ ;	# replace keyword with IP address
      }

      if (! open (CMD, "$cmd 2>&1 |") ) { 
	print "Command $cmd error  <p>\n";
	&print_footer();
	return;
      }
      # break after 10 lines are read to avoid runaway commands.
      print "Running command <tt>$cmd</tt>\n<p>&nbsp;</p>",
            "<table cellpadding=5 cellspacing=0 border = 0> <tr>\n",
            "<td bgcolor=\"#D8D8D8\">  <PRE>";
      while (<CMD>) { print; ++$linecnt; last if ($linecnt > 10); }
      print "</PRE> </td></tr></table>";
      close (CMD);
    }
    else {
      print "<h4><i> Dont know how to handle $subcmd </i></h4>\n";
    }
  }	# if (subcmd ne "")

  ##
  ## Now generate the form
  if ($deviceaddr && $deviceaddr ne '-') {
    $devicename = $deviceaddr;
  }
  $traceroute =~ s/DEVICE/$devicename/ ;	# replace keyword with name
  $ping =~ s/DEVICE/$devicename/;
  $nslookup =~ s/DEVICE/$devicename/;

  print "\t<FORM action=\"$snipsweb_cgi\" method=\"post\">\n";
  &print_state_info;
  print <<TROUBLESHOOT;
	<input type=hidden name=command value="$command">
	<table cellspacing="0" cellpadding="5" border=0>
	  <tr><td align="right">
	   <input type=submit name=subcommand value="traceroute"></td>
	   <td align="left"><tt>$traceroute</tt></td>
	  </tr>
	  <tr><td align="right">
	   <input type=submit name=subcommand value="nslookup"></td>
	   <td align="left"><tt>$nslookup</tt></td>
	  </tr>
	  <tr><td align="right">
	   <input type=submit name=subcommand value="ping"></td>
	   <td align="left"><tt>$ping</tt></td>
	  </tr>
	</table>
	</FORM>
TROUBLESHOOT

  &print_footer();

}	# doTroubleShoot()

#------------------------------------------------------------
## graphs (using $rrdgraph_cgi)
# Currently we look in the subdir $RRD_DBDIR/$deviceaddr and generate
# a GIF for all the variables in that subdir. We should ideally only
# need to generate the gif for the particular variable.
#
sub doGraph {
  my $rrddir;
  my $subdev = "";

  &denyAccess if ($userlevel > 2);
  &print_button_header;

  if (! defined($rrdgraph_cgi) || $rrdgraph_cgi eq "")
  {
    print "<h4> RRD not supported </h4>";
    return;
  }
  return if ($devicename eq "" || $RRD_DBDIR eq "");
  if ($subdevice ne "") { $subdev = "${subdevice}+"; }

  # Location of the RRD files
  $rrddir = "$RRD_DBDIR/" . substr($devicename, 0, 1) . "/$devicename";

  print "<center><H3>$devicename $subdevice : $deviceaddr</H3>\n",
        "  <hr width=\"50\%\" align=center>\n</center>\n";

  if ( (! -d "$rrddir") || (! -r "$rrddir") )
  {
    print "<p><font size=4> <b>No RRD data available under $rrddir</b></font></p>\n";
    print STDERR "Directory $rrddir not readable - $!\n";
    return;
  }

  print <<Eof1;
   <p>Click
    <A href="${rrdgraph_cgi}?rrdsubdir=$devicename&title=${devicename}"> HERE </A>
      to display <b>all variables </b>for $devicename\n</p>
   <p> Click on the image to display <b>historical</b> data for the variable</p>
Eof1

  my $rrdfile = "${variable}.rrd";
  $rrdfile = "${subdev}+${rrdfile}" if ($subdevice !~ /\s*/);
  if (-f "$rrddir/$rrdfile") {
    #$rrdfile =~ tr/[a-zA-Z0-9_.+\-]//cd;
    print <<Eof;
    <h4>${variable}</h4>
    <A href="${rrdgraph_cgi}?rrdsubdir=$devicename&rrdfile=${rrdfile}&title=${devicename}&legend=${variable}&timescale=A&mode=html">
    <IMG SRC="${rrdgraph_cgi}?rrdsubdir=$devicename&rrdfile=${rrdfile}&title=${devicename}%20(${variable})&legend=${variable}&timescale=d&mode=gif" >
    </A>
    <hr>
Eof
  }	# for $rrdfile

  &print_footer();

}	# doGraph()

## return the user to the 'return' page and EXIT.
#  this loses the state information though (so user has to authenticate
#  again).
sub restoreView {
  print "Content-type: text/html\n\n";
  print <<ReSTORE;
  <html> <head>
    <meta http-equiv="refresh" content="0;URL=$FORM{'restoreurl'}">
    <title>SNIPS</title>
   <head>
   <body> <h2>Please wait as screen reloads...</h2> </body>
   </html>
ReSTORE

  exit 0;
}
  
#------------------------------------------------------------
# Info blurb about snips.
sub aboutSnips {

  # &denyAccess if ($userlevel > 9);
  if ($command =~ /^UserHelp/i) {	# no special buttons for userlevel
    print "Content-type: text/html\n\n <html> <head>\n";
    print "<title>Snips Help</title> </head> <body bgcolor=\"#ffffff\">\n";
  }
  else { &print_button_header(); }

  print <<EOHELP;

   <center><H2>Systems &amp; Network Integrated Polling Software</H2>
     <HR width="60%" align="center">
   </center>

<A href="http://www.netplex-tech.com/software/snips/">SNIPS
(System and Network Integrated Polling Software) </A> is a network monitoring
package that runs on Unix platforms and capable of monitoring network and
system variables such as ICMP or RPC reachability, RMON variables,
nameservers, ethernet load, port reachability, host performance, SNMP traps,
radius, NTP, modem line usage, appletalk & novell routes/services, BGP peers,
etc.
There is just one set of monitoring agents and <em>any</em> number of
display agents, and all of the displays see the same consistent set of data.
Additionally, each event is assigned a severity (determined by comparing
against user defined threshold values) which is gradually escalated, thus
preventing false alarms and a customized priority notification based on
the severity. There are four severity levels ranging from Critical thru Info,
and each event typically steps through each one of these severities until
it reaches its maximum allowed level.
<P>
This display uses a dynamically generated web page and so can display on a
variety of terminals. The user running the display can select the minimum
display severity--only events above this minimum severity level are displayed.
If you\'re running a Netscape-compatible web browser, the display will
automatically update itself every minute.
<P>
More information about snips is available
<a href="http://www.netplex-tech.com/software/snips/"> here. </a>
<P>
SNIPS was written by:
<BLOCKQUOTE>Vikas Aggarwal
<BR><a href="mailto:vikas\@navya.com">vikas\@navya.com</a>
<BR>March, 2001
</BLOCKQUOTE>
This web interface was originally written for NOCOL by:
<BLOCKQUOTE>Rick Beebe
<BR><a href="mailto:richard.beebe\@yale.edu">richard.beebe\@yale.edu</a>
<BR>March, 1998
</BLOCKQUOTE>
EOHELP

&print_footer();

}

#####
##### main
#####

my ($buffer, @pairs);
# Check that the POST method is used
if ($ENV{'REQUEST_METHOD'} eq 'POST') {
  # POST method dicatates that we get the form input
  # from standard input
  read(STDIN, $buffer, $ENV{'CONTENT_LENGTH'});
}
else {
  $buffer = $ENV{'QUERY_STRING'};
}	

# Split the the name-value pairs on &
@pairs = split(/&/, $buffer);

foreach my $pair (@pairs) {
  my ($name, $value) = split(/=/, $pair);
  $value =~ tr/+/ /;
  # Now convert any HTML'ized characters into their real world
  # equivalent. e.g. a %20 becomes a space. 
  $value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;
  $FORM{$name} = $value;
}
## Now all the form variables are in the $FORM associative array

$command  = $FORM{command};	# what we are supposed to do
$devicename = $FORM{devicename};
$deviceaddr = $FORM{deviceaddr};
$subdevice = $FORM{subdevice};
$variable = $FORM{variable};

$done_footer = 0;	# boolean flag

# Maintain a $userfile to set these (see sub authcheck() ). Lower number is
# higher priority. Basic level is '9'.
$userlevel = 9;			# default authority is basic-level

## we dont need any userlevel for these following commands
if    ($command =~ /^Authenticate/i) { &doAuthenticate; exit 0; }
elsif ($command =~ /^About/i) { &aboutSnips; exit 0; }	# generic blurb
elsif ($command =~ /^Help/i)  { &aboutSnips; exit 0; }	# generic blurb
elsif ($command =~ /^UserHelp/i)  { &aboutSnips; exit 0; } # user level help
elsif ($command =~ /^SnipsView/i)  { &restoreView; exit 0; }# snips display

&set_userlevel;		# get and set the user privelege level

if    ($command =~ /^DeviceHelp/i) { &doDeviceHelp; }	# show device Help
elsif ($command =~ /^Update/i)  { &doUpdates; }	# maintain 'updates' file
elsif ($command =~ /^History/i) { &doHistory; }	# snipslogd logs
elsif ($command =~ /^Device\s+Logs/i)    { &doHistory; }      # snipslogd logs
elsif ($command =~ /^Troubleshoot/i) { &doTroubleShoot; }
elsif ($command =~ /^Graphs/i) { &doGraph; }	# using RRD
else { &restoreView; }	# show snips screen

&print_footer;
exit 0;

