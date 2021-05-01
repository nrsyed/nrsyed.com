---
title: Migrating from WordPress to Hugo (and SiteGround to Digital Ocean)
author: Najam Syed
type: post
date: 2021-05-01T00:01:22-04:00
url: /2021/05/01/migrating-from-wordpress-to-hugo-and-siteground-to-digital-ocean
categories:
  - Web Development
  - System Administration
tags:
  - Apache
  - AWS
  - CSS
  - Digital Ocean
  - gunicorn
  - HTML
  - Hugo
  - Isso
  - JavaScript
  - Linux
  - markdown
  - PHP
  - postfix
  - Python
  - SQL
  - systemd
  - VPS
  - WordPress
---

* [Introduction](#introduction)
* [Steps](#steps)
  - [Choose a Hugo theme](#choose-a-theme)
  - [Convert posts to markdown](#convert-to-markdown)
  - [Configure send-only email server](#configure-email)
  - [Add Isso post commenting system](#add-isso-comments)
  - [Transfer WordPress comments to Isso database](#transfer-comments)
  - [Create a contact form](#create-contact-form)
  - [Generate and deploy static site files](#deploy)
* [Conclusion](#conclusion)


# Introduction

When I started this blog in 2017, I was working as a mechanical
engineer bored to tears by [CAD][26]/[FEA][27]. Though I actually enjoy
SolidWorks, I'm not a fan of it being a core component of
my job description. Programming was, for me, infinitely more satisfying.
Hence, my goals in creating a blog were 1) to learn or review topics in
math/engineering and software development, and 2) to create a modest but
polished portfolio to aid my transition to a career in computer science.

I didn't want to spend much time setting up or maintaining a website but I
did want to retain *some* control, so I opted for a [WordPress][28] blog
self-hosted on [SiteGround][29] (as opposed to a WordPress hosted on
[WordPress.com](https://wordpress.com)). WordPress has a nice graphical
interface for administrative tasks and writing posts. It also has an active
community and loads of plugins. Need a contact form? There's a plugin for that.
Want code syntax highlighting? There's a plugin for that. Want to collect
detailed statistics on visitors to your site? There's a... well, you get the
idea.

{{< figure
  src="/img/old_site.png" alt="My old, ugly WordPress site"
  caption="My old, ugly WordPress site"
>}}

It worked well enough for me for several years, but as I grew comfortable
with software development and Linux, I found myself wanting to tinker.
Unfortunately, WordPress is a hulking behemoth of PHP with so many moving
parts and layers of abstraction as to be opaque to anyone who hasn't spent a
significant amount of time learning WordPress. Its codebase is convoluted,
its style inconsistent, and it requires regular updates to patch its numerous
vulnerabilities. Similarly, the WordPress plugin ecosystem is tenuous, with
code quality and security varying wildly from plugin to plugin and author to
author.

Furthermore, all site content is stored in a poorly structured MySQL database,
so a simple task like editing a post without the GUI involves the added hassle
of reading from and writing to a database. There are command line tools
(e.g., `wp-cli`) that facilitate such tasks, but to me, that's a barrier
between me and my content.

Enter [Hugo][2]. Hugo is a fast, lightweight static site generator written in
Go that enables more direct control over the site's design and content. Posts
are stored in plaintext files, and Hugo supports [Markdown][30]. And because
it generates a static site, it has none of the vulnerabilities of WordPress.

As part of this redesign and migration from WordPress to Hugo, I ditched
SiteGround as my host, where I was paying $15/month (their cheapest
plan) and went with a [Digital Ocean][31] Droplet that costs me $5/month.
With SiteGround, you have limited control over the server and essentially
pay a premium for them to handle all the administrative stuff and provide
web-based tools to manage your site. On the other hand, with a Digital Ocean
Droplet, you have complete control over the server and you're responsible for
all system administration; it is yours to do with as you please. Sign me up!

# Steps

<span id="choose-a-theme" />
## Choose a Hugo theme

I went with htr3n's [hyde-hyde][8] theme for its clean look, relative
simplicity, logical structure, and ease of customization.


<span id="convert-to-markdown" />
## Convert posts to markdown

Because WordPress stores posts in a MySQL database, the first step is
extracting posts from the database and converting post metadata and
content to markdown. HTML in the post content must also be converted to
Hugo-friendly markdown and shortcode. I used Cyrill Schumacher's
[wordpress-to-hugo-exporter][3] as a first pass.

This did a decent, albeit incomplete, job of generating Hugo-compatible
markdown files from the WordPress database. In my case, it didn't always
correctly format or indent code blocks, nor did it generate Hugo image
shortcodes from &lt;img&gt; HTML tags (among other tags). It also didn't
split long lines, whereas I prefer a maximum line length of 80 characters in
my text files for convenience. To fix/format the markdown files to my liking,
I wrote a hacky but functional [Python script][4] that used [pyparsing][5]
to define a [context-free grammar][6], lex/parse the markdown files into
tokens, fix incorrectly formatted tokens, and enforce an 80-character max
line length (making exceptions for certain tokens, e.g., URLs or lines of
code, even if they caused a line to exceed 80 characters).


<span id="configure-email" />
## Configure send-only email server

I wanted to receive post comment notifications and messages from the contact
form in my GMail inbox, which I thought would be relatively straightforward,
especially since I only want to send email from the server to one specific
email address (mine) and don't need the server to receive or relay any email.
(Although I developed and troubleshooted my email server solution alongside
the contact form and post comment system, I'm going to discuss it before those
components because they build upon it). Turns out email is a nightmare.

Initially, I tried to use `sendmail` but it worked inconsistently, so I ended
up using `postfix`, which can be installed and set up as follows:

{{< highlight plain >}}
sudo apt install postfix
sudo postfix start
{{< / highlight >}}

To reconfigure `postfix` and change any settings, run
`sudo dpkg-reconfigure postfix`. Alternatively, you can directly edit
the settings in `/etc/postfix/main.cf` (don't forget to `sudo postfix reload`
if you do). The mail server's activity is logged to
`/var/log/mail.log`, which we can monitor via `tail` for debugging:

{{< highlight plain >}}
tail -f /var/log/mail.log
{{< / highlight >}}

At this point, we can try to send a test email from the terminal to check if
everything is working:

{{< highlight plain >}}
echo "test message body" | mail -s "test subject" foo.bar@gmail.com
{{< / highlight >}}

Unfortunately, some services are more strict than others. Case in point: I was
I was able to use the above command to send email to a Yahoo address but
attempting to send it to my GMail produced the following response in
`/var/log/mail.log`:

{{< highlight plain >}}
Apr 28 17:14:53 localhost postfix/smtp[1686]: 71179717: to=<foo.bar@gmail.com>,
relay=gmail-smtp-in.l.google.com[173.194.206.26]:25, delay=0.52,
delays=0.03/0.02/0.16/0.31, dsn=5.7.26, status=bounced (host
gmail-smtp-in.l.google.com[173.194.206.26] said:
550-5.7.26 This message does not have authentication information or fails to
550-5.7.26 pass authentication checks. To best protect our users from spam, the
550-5.7.26 message has been blocked. Please visit 550-5.7.26
https://support.google.com/mail/answer/81126#authentication for more 550 5.7.26
information. 11si549071qvx.168 - gsmtp (in reply to end of DATA command))
{{< / highlight >}}

I tried several solutions for this issue, like [adding a domain SPF record][36]
[in the Digital Ocean settings][37]. Nothing worked. Ultimately, I opted for
[Amazon AWS SES][38] (**S**imple **E**mail **S**ervice) to send emails on
behalf of my GMail account without actually using my Google credentials. AWS
SES is free below a certain usage threshold, which currently more than covers
my needs.

Make an AWS account first if you don't have one, then navigate to AWS SES SMTP
settings and make note of the **server name** and **port** choices.

{{< figure src="/img/aws_ses_smtp.png" alt="AWS SES SMTP settings" >}}

Click *Create My SMTP Credentials* and follow the instructions. At the
end of the process, you'll be presented with an SMTP username and password.

{{< figure src="/img/aws_ses_credentials.png" alt="AWS SES SMTP credentials" >}}

Finally, before you can use AWS SES credentials to send email, you'll need to
add and verify an email address in *Email Addresses* under the Identity
Management category in the sidebar.


## Add Isso post commenting system
<span id="add-isso-comments" />

In the interest of hosting everything myself, I went with [Isso][7] because
it's open source, lightweight, and exists only on my server (unlike, e.g.,
Disqus). Isso is a comment server written in Python and JavaScript, and it
uses a SQLite database on the backend to store comments. I installed Isso in a
virtualenv per the [official instructions][14]:

{{< highlight plain >}}
virtualenv -p python3 /opt/isso
source /opt/isso/bin/activate
pip install isso
{{< / highlight >}}

As a reference, I also found [this post][15] by Stiobhart Matulevicz helpful in
integrating it into Hugo.

To add Isso comments to the hyde-hyde Hugo theme, I created a
[Hugo partial for the comment section][10], which has some client-side
options for commenting, and included it at the end of the
[single post content partial][11] (refer to the Hugo documentation on
[partial templates][9]); I disabled reply email notifications because I
couldn't get this feature to work, but may enable it in the future if I can
dig into Isso and identify the cause. I also added some modifications to the
[comment section CSS][12]. Finally, to customize the placeholder text in the
comment box to read `Leave a comment` instead of the default
`Type Comment Here (at least 3 chars)`, I modified [embed.min.js][13],
the minified JavaScript file that's included with the Isso Python install. In
my case, that file is located at
`/opt/isso/lib/python3.6/site-packages/isso/js/embed.min.js`.

You configure the Isso server with a configuration file, which can be named
anything and can be placed anywhere. I named mine `isso.cfg` and will refer to
its filepath as `/path/to/isso.cfg`. My `isso.cfg` looks something like this:

{{< highlight cfg "linenos=true" >}}
[general]
dbpath = /path/to/comments.db
host =
  http://nrsyed.com/
  https://nrsyed.com/
log-file = /path/to/isso.log
max-age = 1h
reply-notifications = true
notify = smtp

[server]
listen = http://localhost:1234
reload = off
profile = off
public-endpoint = https://nrsyed.com/isso/

[moderation]
enabled = true

[smtp]
username = ABCDEFGHIJKLMNOPQRST
password = ABCDEFGHIKLJMNOPQRSTUVWXYZ1234567890+/=zyxwv
host = email-smtp.us-east-1.amazonaws.com
port = 25
to = your_email@gmail.com
from = "Isso" <your_email@gmail.com>
timeout = 10
security = starttls

[admin]
enabled = true
password = hunter2

[markup]
options = strikethrough, superscript, fenced-code

[guard]
enabled = true
reply-to-self = true
require-author = true
ratelimit = 2
{{< / highlight >}}

Full documentation of these server-side config parameters can be found
[here][32], but make note of the server listen port on **line 12** (`1234`
in this example); you can choose any unused port for this value. In the
`[smtp]` settings on **line 20**, the `username` and `password` should match
the AWS SES username/password credentials from earlier, `host` should match
the AWS SES server name, and `port` should be one of the port choices from
AWS SES. The `to` and `from` fields should contain an email address that you
added and verified on AWS SES.

For testing, Isso has a builtin server that can be started as follows:

{{< highlight plain >}}
source /opt/isso/bin/activate
isso -c /path/to/isso.cfg &
{{< / highlight >}}

And stopped like so:

{{< highlight plain >}}
kill -SIGINT $(pgrep isso)
{{< / highlight >}}

If the server isn't running, the comment section won't appear in posts.

For actual deployment, we want something more robust, so I used [gunicorn][21]
and ran the server as a systemd service. To do this, I created a file at
`/etc/systemd/system/isso.service` and, using the Isso documentation's
[instructions for gunicorn deployment][22] as a guideline, populated the file
as follows (note that `gunicorn` must first be installed in the Isso virtual
environment in `/opt/isso`):

{{< highlight plain >}}
[Unit]
Description=Isso comment server
After=network.target

[Service]
User=najam
Group=www-data
WorkingDirectory=/home/najam/isso
Environment="ISSO_SETTINGS=/path/to/isso.cfg"
ExecStart=/opt/isso/bin/gunicorn -b localhost:1234 -w 4 --preload isso.run
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
{{< / highlight >}}

being sure to replace `1234` with the server listen port defined in `isso.cfg`.
The service can be enabled and started as follows:

{{< highlight plain >}}
systemctl enable isso
systemctl start isso
{{< / highlight >}}

Next, we need to let the Isso server communicate with Apache by using Apache
as a reverse proxy. Enable the proxy modules:

{{< highlight plain >}}
a2enmod proxy
a2enmod proxy_http
{{< / highlight >}}

Then, per the instructions in [this post][34] by Dan Gheorghe Haiduc (and
referring to [this Digital Ocean tutorial][35] for additional information),
we add the following lines to the site's Apache configuration file VirtualHost
settings, which should be found in `/etc/apache2/sites-available/`:

{{< highlight plain >}}
  ProxyPass /isso/ http://localhost:1234/
  ProxyPassReverse /isso/ http://localhost:1234/
{{< / highlight >}}

This binds the `/isso/` web endpoint to the port we defined in `isso.cfg`.
These lines should be added to the site's SSL VirtualHost entry as well,
for HTTPS.


## Transfer WordPress comments to Isso database
<span id="transfer-comments" />

The [wordpress-to-hugo-exporter][3] tool generates an XML file from the
WordPress blog that includes post comments. I wrote my own tools to extract
comments from this XML output and import them into the Isso SQLite database.
[xmlread.py][16] uses the builtin Python `xml` module to parse the XML
structure and write out a JSON file linking posts to their corresponding
comments. Next, I used [import_comments.py][17] to read that JSON file and
insert the comments into the Isso SQLite database file.

After that last step, I found that code blocks in some comments didn't display
correctly because WordPress renders them differently than Isso. To fix these
formatting issues, I manually edited those comments. Since comments in the
aforementioned JSON file were written out as single-line strings (with newlines
represented by the `\n` newline character), it would have been a pain to edit
them as-is, so I created another script, [editable_comments.py][18], that
contains a function to write each comment out to a human-friendly, easily
editable text file. After editing them, a different function in the script
takes a pointer to the directory of text files and puts them back into the
original JSON format, on which we can again run import_comments.py to insert
them into the database.


## Create a contact form
<span id="create-contact-form" />

Major credit goes to Fredrik Jonsson and [his post][23] on creating an
HTML/PHP/JavaScript contact form with spam protection from scratch, as well as
his [Hugo Zen][24] theme that served as a guideline on integrating it into
Hugo. On the frontend, his implementation utilizes jQuery. I wrote
[my own implementation][33] in pure JavaScript to avoid bringing in another
library. To prevent the contact page from automatically reloading upon form
submission, I disabled the default submit behavior and wrote the AJAX POST
request logic myself with the aid of [this obscure repo][25], which shows an
example of such a contact form. Here's the relevant function from my script:

{{< highlight js "linenos=true" >}}
function post_data(form_submission) {
  let name = encodeURIComponent(document.getElementById("edit-name").value);
  let email = encodeURIComponent(document.getElementById("edit-mail").value);
  let url = encodeURIComponent(document.getElementById("edit-url").value);
  let subject = encodeURIComponent(document.getElementById("edit-subject").value);
  let message = encodeURIComponent(document.getElementById("edit-message").value);

  // Parameters to send to PHP script.
  let params = "name=" + name + "&email=" + email + "&url=" + url
    + "&subject=" + subject + "&message=" + message;

  let http = new XMLHttpRequest();
  http.open("POST", "/php/contact.php", true);
  http.setRequestHeader("Content-type", "application/x-www-form-urlencoded");

  http.onreadystatechange = function(){
    let form = document.getElementById("contact-form");
    form.classList.add("hidden");

    let contact_status = document.getElementById("contact-status");
    if (http.readyState == 4 && http.status == 200){
      contact_status.textContent = "Message submitted";
    } else {
      contact_status.textContent = "Error submitting message";
    }
	}

  http.send(params);
  form_submission.preventDefault();
}
{{< / highlight >}}

On the backend, Fredrik's implementation uses a PHP script to validate the
contact form input and send it via the [default PHP mail() function][39].
However, this function is limited and doesn't support authentication, which
we need for AWS SES. Therefore, I [rewrote the script][40] to utilize the PHP
[PEAR][41] framework and its `Mail.php` header, as demonstrated in this
[LFC hosting knowledgebase article][42]. PEAR can be installed as follows:

{{< highlight plain >}}
sudo apt install php-pear
sudo apt install php-mail
{{< / highlight >}}

Initially, when I tested the contact form with my PHP script, I encountered
the following PHP warning in the Apache error log (whose location is defined
in your site's `.conf` file in `/etc/apache2/sites-available`; in my case, it's
`/var/log/apache2/error.log`):

{{< highlight plain >}}
PHP Warning:  require_once(): open_basedir restriction in effect.
File(/usr/share/php/Mail.php) is not within the allowed path(s):
{{< / highlight >}}

To fix this, I had to comment out the `open_basedir` entry in my Apache
`php.ini` file. There are several `php.ini` files, but you can figure out which
one Apache is using via [phpinfo][43] (on my system, it's
`/etc/php/7.2/apache2/php.ini`).


## Generate and deploy static site files
<span id="deploy" />

To generate the site files, we simply have to run the `hugo` command in the
source directory, which places the files in a new directory named `public`,
then copy those files to the appropriate Apache server directory:

{{< highlight plain >}}
export HTML_DIR=/var/www/nrsyed.com/public_html

hugo && touch public
sudo rm -r $HTML_DIR/*
sudo cp -r public/* $HTML_DIR
{{< / highlight >}}

I run `touch` on the newly created directory because Hugo doesn't correctly
set the directory's Last Modified date to a valid value. In my case, it set
it to August 30, 1754, i.e., running `ls -l | grep public` yielded the
following:

{{< highlight plain >}}
drwxr-xr-x 17 najam najam 4096 Aug 30  1754 public
{{< / highlight >}}

This isn't a problem in and of itself; however, I use a version of
[ranger file manager][19] that crashes when it encounters an invalid date.
Apparently, this issue has been addressed in newer versions that have not
yet found their way into the Ubuntu repositories.

To avoid putting my AWS SES credentials (and other personal information, like
my email address) directly in the Isso config file (`isso.cfg`) and in the
[contact form PHP file][44], I opted to put this information in a secrets
file outside the Apache public_html directory (even though the PHP file source
should never be accessible from the web). The PHP script reads the values from
the file in the following bit of logic:

{{< highlight php "linenos=true" >}}
$secrets_file = '/path/to/secrets.txt';
if (file_exists($secrets_file)) {
  $file = fopen($secrets_file, "r");
  $address = base64_decode(fgets($file));
  $host = base64_decode(fgets($file));
  $username = base64_decode(fgets($file));
  $password = base64_decode(fgets($file));
  fclose($file);
} else {
  $error = true;
}
{{< / highlight >}}

The base-64 encoding of secret values doesn't really make the secrets
more secure, but it does obscure their meaning in the event the server is
compromised (which should never happen). To avoid accidentally pushing
credentials and personal information to GitHub, I created a file named
[isso.cfg.nosecrets][45], which is an `isso.cfg` with dummy "secret" values.
I wrote a simple Python script called [sitetools.py][46] that takes a path
to the secrets file (whose structure is defined in that Python file) and the
"dummy" Isso config file, replaces the dummy values with the actual values,
and writes the result to `isso.cfg` (which is in the repo's `.gitignore`).
The script also updates the value of the `$secrets_file` variable in the
build files' PHP script.

Admittedly, most of this is unnecessary, but a little healthy paranoia never
hurts, right?

# Conclusion



[1]: https://wordpress.org/
[2]: https://gohugo.io/
[3]: https://github.com/SchumacherFM/wordpress-to-hugo-exporter
[4]: https://github.com/nrsyed/nrsyed.com/blob/hugo/tools/format_posts.py
[5]: https://github.com/pyparsing/pyparsing/
[6]: https://en.wikipedia.org/wiki/Context-free_grammar
[7]: https://posativ.org/isso/
[8]: https://github.com/htr3n/hyde-hyde
[9]: https://gohugo.io/templates/partials/
[10]: https://github.com/nrsyed/nrsyed.com/blob/hugo/layouts/partials/isso.html
[11]: https://github.com/nrsyed/nrsyed.com/blob/hugo/layouts/partials/page-single/content.html
[12]: https://github.com/nrsyed/nrsyed.com/blob/hugo/assets/scss/_isso.scss
[13]: https://github.com/nrsyed/nrsyed.com/tree/hugo/_isso
[14]: https://posativ.org/isso/docs/install/
[15]: https://stiobhart.net/2017-02-24-isso-comments/
[16]: https://github.com/nrsyed/nrsyed.com/blob/hugo/tools/xmlread.py
[17]: https://github.com/nrsyed/nrsyed.com/blob/hugo/tools/import_comments.py
[18]: https://github.com/nrsyed/nrsyed.com/blob/hugo/tools/editable_comments.py
[19]: https://github.com/ranger/ranger
[20]: https://therandombits.com/2018/12/how-to-add-isso-comments-to-your-site/
[21]: https://gunicorn.org/
[22]: https://posativ.org/isso/docs/extras/deployment/#gunicorn
[23]: https://xdeb.org/post/2017/06/24/a-html5-php-javascript-contact-form-with-spam-protection/
[24]: https://github.com/frjo/hugo-theme-zen
[25]: https://github.com/talbene/Pure-JavaScript-AJAX-POST-Contact-Form
[26]: https://en.wikipedia.org/wiki/Computer-aided_design
[27]: https://en.wikipedia.org/wiki/Finite_element_method
[28]: https://wordpress.org
[29]: https://www.siteground.com
[30]: https://en.wikipedia.org/wiki/Markdown
[31]: https://www.digitalocean.com/
[32]: https://posativ.org/isso/docs/configuration/server/
[33]: https://github.com/nrsyed/nrsyed.com/blob/hugo/assets/js/contact.js
[34]: https://danuker.go.ro/installing-isso-on-debian-apache.html
[35]: https://www.digitalocean.com/community/tutorials/how-to-use-apache-http-server-as-reverse-proxy-using-mod_proxy-extension
[36]: https://devanswers.co/postfix-gmail-bounce-this-message-does-not-have-authentication-information-or-fails-to-550-5-7-26-pass-authentication-checks/
[37]: https://www.digitalocean.com/community/tutorials/how-to-create-a-spf-record-for-your-domain-with-google-apps
[38]: https://aws.amazon.com/ses/
[39]: https://www.php.net/manual/en/function.mail.php
[40]: https://github.com/nrsyed/nrsyed.com/blob/hugo/static/php/contact.php
[41]: https://pear.php.net/
[42]: https://account.lfchosting.com/knowledgebase.php?action=displayarticle&id=187
[43]: https://www.php.net/manual/en/function.phpinfo.php
[44]: https://github.com/nrsyed/nrsyed.com/blob/hugo/static/php/contact.php
[45]: https://github.com/nrsyed/nrsyed.com/blob/hugo/isso.cfg.nosecrets
[46]: https://github.com/nrsyed/nrsyed.com/blob/hugo/sitetools.py
