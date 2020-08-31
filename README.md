# slack-zotero

Simple interface between a Zotero 'group' and a Slack-compatible webhook. 
Zotero is an open-source reference manager, and the 'groups' allow you to
collective add to a shared library of academic work. 
This code then checks this library, and automatically injects messages this new
literature into your group-chat (such as Slack or Zulip). 

Effectively this enables low-friction 'journal-club' discussions to naturally
arise, and for other group members to easily keep up to date with the latest
exciting literature. 

I think this works particularly well with Zulip due to it's entirely
thread-based way of organising group chat, and easy ability to move these
automatically generated threads from the 'bot' channel to where ether they make
the most sense (project based, methods etc.)

## Pictorial example

A picture is probably the most useful explanation - this was generated
automatically after adding a classic paper. 
https://mobile.twitter.com/JarvistFrost/status/1300432993354502144

## Getting started

Hopefully fairly explanatory. Email / Tweet me if you get stuck.

`zulip-zotero.sh` is just an expanded call signature of what was previously in
the doc string of the python code. 
The python code has been very slightly fixed up, and a Zulip-convenient new
default of setting the thread-topic ('channel') to the title of the academic
paper.

You'd then need to setup some method of calling this regularly. (Such as with
`cron` on an always-on server.) Currently I'm just running this in a loop with
an hours sleep, in a tmux window on my office workstation. :)

## Constructing the webhook URL for Zulip:

(Lifted from the Zulip documentation.)

Construct the URL for the Slack-compatible webhook bot using the bot's API key
and the desired stream name:

https://yourZulipDomain.zulipchat.com/api/v1/external/slack_incoming?api_key=abcdefgh&stream=stream%20name

Modify the parameters of the URL above, where api_key is the API key of your
Zulip bot, and stream is the URL-encoded stream name you want the notifications
sent to. If you do not specify a stream, the bot will send notifications via
PMs to the creator of the bot. If you'd like this integration to always send to
the topic your topic, just add &topic=your%20topic to the end of the URL.

