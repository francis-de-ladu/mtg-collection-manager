#!/usr/bin/env bash

filepath=$1

sed -i -E "s/^([0-9]+)\s/\1,/g" $filepath
sed -i -E "s/\s</,</g" $filepath
sed -i -E "s/\s\[/,[/g" $filepath
sed -i -E "s/([^>]),\[/\1,,[/g" $filepath
sed -i -E "s/,\b(.+)\b,/,\"\1\",/g" $filepath
sed -i -E "s/\s?(\(F\))?$/,\1/g" $filepath
sed -i -E "s/([^a-zA-Z]),/\1\t/g" $filepath
sed -i -E "s/([^a-zA-Z]),/\1\t/g" $filepath

# sed -i -E "s/,+/,/g" $filepath
