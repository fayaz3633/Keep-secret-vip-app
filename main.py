name: Build Android APK

on:
push:
branches:
- main
workflow_dispatch:

jobs:
build:
runs-on: ubuntu-latest

steps:
  - uses: actions/checkout@v4

  - uses: actions/cache@v4
    with:
      path: |
        ~/.buildozer
        ~/.gradle
      key: buildozer-${{ runner.os }}

  - name: Install Dependencies
    run: |
      sudo apt-get update
      sudo apt-get install -y \
      build-essential ccache git \
      libffi-dev libssl-dev \
      libsdl2-dev libsdl2-image-dev \
      libsdl2-ttf-dev libjpeg-dev \
      autoconf automake libtool \
      pkg-config zlib1g-dev \
      python3-pip python3-setuptools

      python3 -m pip install --upgrade pip
      pip3 install --user buildozer cython virtualenv

  - name: Build APK
    run: |
      export PATH=$PATH:$HOME/.local/bin
      buildozer android debug

  - name: Upload APK
    uses: actions/upload-artifact@v4
    with:
      name: Keep-Secret-VIP-APK
      path: bin/*.apk
