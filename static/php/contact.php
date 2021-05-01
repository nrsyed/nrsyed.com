<?php
require_once('/usr/share/php/Mail.php');

$error = false;
$status = 'error';

// e-mail subject prefix.
$prefix = 'nrsyed.com';

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

// Check that the submission address is valid.
if ((bool) filter_var(trim($address), FILTER_VALIDATE_EMAIL)) {
  // Also set sender/return path header to this address to avoid SPF errors.
  $to = $sender = trim($address);
} else {
  $error = true;
}

// Check that referer is local server.
if (
    !isset($_SERVER['HTTP_REFERER'])
    || (parse_url($_SERVER['HTTP_REFERER'], PHP_URL_HOST) != $_SERVER['SERVER_NAME'])
) {
  exit('Direct access not permitted');
}

// Check that this is a post request.
if ($_SERVER['REQUEST_METHOD'] != 'POST' || empty($_POST)) {
  $error = true;
}

// Check if fake url field is filled in, i.e. spam bot.
if (!empty($_POST['url'])) {
  $error = true;
}

// Check that e-mail address is valid.
if ((bool) filter_var(trim($_POST['email']), FILTER_VALIDATE_EMAIL)) {
  $email = trim($_POST['email']);
}
else {
  $error = true;
}

if (!$error) {
  $name = _contact_clean_str($_POST['name'], ENT_QUOTES, true, true);
  $prefix = _contact_clean_str($prefix, ENT_NOQUOTES, true, true);
  $subject = _contact_clean_str($_POST['subject'], ENT_NOQUOTES, true, true);
  $subject = "[$prefix] $subject";
  $message = _contact_clean_str($_POST['message'], ENT_NOQUOTES);
  $lines = explode("\n", $message);
  array_walk($lines, '_contact_ff_wrap');
  $message = implode("\n", $lines);

  $headers = [
    'From'          => "Contact form <$sender>",
    'Sender'        => $sender,
    'To'            => $sender,
    'Return-Path'   => $sender,
    'Reply-To'      => "$name <$email>",
    'Subject'       => $subject,
    'MIME-Version'  => '1.0',
    'Content-Type'              => 'text/plain; charset=UTF-8; format=flowed; delsp=yes',
    'Content-Transfer-Encoding' => '8Bit',
    'X-Mailer'                  => 'nrsyed.com blog',
  ];

  $mime_headers = [];
  foreach ($headers as $key => $value) {
    $mime_headers[] = "$key: $value";
  }
  $mail_headers = join("\n", $mime_headers);

  // Send mail.
  $smtp = Mail::factory(
    'smtp',
    array (
      'host' => $host,
      'auth' => true,
      'username' => $username,
      'password' => $password
    )
  );

  $mail = $smtp->send($sender, $headers, $message);

  if (!PEAR::isError($mail)) {
    $status = 'submitted';
  }
}

$contact_form_url = strtok($_SERVER['HTTP_REFERER'], '?');

// Redirect back to contact form with status.
header('Location: ' . $contact_form_url . '?' . $status, TRUE, 302);
exit;

function _contact_ff_wrap(&$line) {
  $line = wordwrap($line, 72, " \n");
}

function _contact_clean_str($str, $quotes, $strip = false, $encode = false) {
  if ($strip) {
    $str = strip_tags($str);
  }

  $str = htmlspecialchars(trim($str), $quotes, 'UTF-8');

  if ($encode && preg_match('/[^\x20-\x7E]/', $str)) {
    $str = '=?UTF-8?B?' . base64_encode($str) . '?=';
  }

  return $str;
}
