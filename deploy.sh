#!/bin/bash

WWW_DIR=/var/www/nrsyed.me/public_html

sudo rm -r $WWW_DIR/
sudo cp -r public/ $WWW_DIR
