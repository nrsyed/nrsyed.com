#!/bin/bash

config1="config_uBlogger.toml"
config2="config_hyde.toml"
link=$(readlink config.toml)

if [ $link = $config1 ]; then
  new_link=$config2
else
  new_link=$config1
fi

rm config.toml
ln -s $new_link config.toml
