#!/usr/bin/env bash
convert -white-threshold 25% -brightness-contrast 30x100 -alpha off -threshold 50% $1 $2
#convert -brightness-contrast 30x100 -alpha off -threshold 70% $1 $2
