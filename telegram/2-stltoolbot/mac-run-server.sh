#!/bin/bash

while true; do
    /Applications/Blender.app/Contents/MacOS/Blender --background --python ./src/tools.py
    sleep 1
done
