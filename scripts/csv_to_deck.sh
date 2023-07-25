#!/usr/bin/env bash

filepath=$1

sed -i -E "s/([^a-zA-Z]),/\1 /g" $filepath
sed -i -E "s/\"//g" $filepath
sed -i -E "s/\s+/ /g" $filepath
