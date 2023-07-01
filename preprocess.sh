#!/usr/bin/env bash
convert -brightness-contrast 30x100 -alpha off -threshold 50% $1 $2
