#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# Copyright (c) 2014-2015 Muges
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import pygame
pygame.mixer.init(frequency=48000)

import os.path
import json
from mutagen.oggvorbis import OggVorbis

class Volume:
    """
    Abstract class, used to represent a named object whose volume can
    be changed
    """
    def __init__(self, name, volume=0):
        """
        Set the volume (an integer between 0 and 100) and the name that will be
        used in the user interface
        """
        self.volume = volume
        self.name = name

    def get_volume(self):
        """
        Return the volume (an integer between 0 and 100)
        """
        return self.volume

    def _set_volume(self):
        """
        Method that should be implemented by the subclasses, which
        actually sets the volume (for example set the volume of a pygame
        sound)
        """
        raise NotImplementedError()

    def set_volume(self, volume):
        """
        Set the volume
        """
        self.volume = min(max(0, int(volume)), 100)
        self._set_volume()

    def inc_volume(self, step):
        """
        Increment the volume (or decrement it, the step may be
        negative)
        """
        self.set_volume(self.volume+step)

class Sound(Volume):
    """
    Sound object, the sound is extracted from an ogg file, and is
    played with pygame.
    """
    def __init__(self, filename, mastervolume):
        """
        Create a volume object from an ogg file. mastervolume is a
        reference to a MasterVolume object that will control this
        sound.
        """
        self.filename = filename

        # Read the title in the ogg vorbis tags
        tags = OggVorbis(filename)
        try:
            name = tags["title"][0]
        except KeyError:
            basename = os.path.basename(filename)
            name, ext = os.path.splitext(basename)
        Volume.__init__(self, name)

        # Link with the MasterVolume object
        self.mastervolume = mastervolume

        # The pygame.mixer.Sound object (only loaded when necessary)
        self.sound = None
        
    def _set_volume(self):
        """
        Set the volume of the pygame.mixer.Sound object (this method
        should not be called directly, it will be called by the
        set_volume method.
        """
        if self.sound == None:
            # Load the sound and play it
            self.sound = pygame.mixer.Sound(self.filename)
            self.sound.play(-1)

        # Set the volume
        self.sound.set_volume((self.mastervolume.get_volume()*self.get_volume())/10000.)

class Preset:
    """
    Stores volumes for each track
    """
    def __init__(self, filename, master):
        """
        Initialise (without reading or creating it) a preset that
        will be stored in the file `filename`. master is a reference to
        a mastervolume object.
        """
        self.filename = filename
        self.master = master
        self.volumes = {}

    def apply(self):
        """
        Apply the preset
        """
        for sound in self.master.get_sounds():
            if self.volumes.has_key(sound.name):
                sound.set_volume(self.volumes[sound.name])
            else:
                sound.set_volume(0)

    def save(self):
        """
        Save the current settings (from the MasterVolume) to the
        preset (without writing it)
        """
        for sound in self.master.get_sounds():
            volume = sound.get_volume()
            if volume == 0:
                self.volumes.pop(sound.name)
            else:
                self.volumes[sound.name] = volume

    def read(self):
        """
        Read the preset from the file
        """
        # TODO : handle errors
        with open(self.filename, "r") as f:
            self.volumes = json.load(f)

    def write(self):
        """
        Write the preset to the file
        """
        # TODO : handle errors
        with open(self.filename, "w") as f:
            json.dump(self.volumes, f)

class MasterVolume(Volume):
    """
    Volume object used to control each track's volume
    """

    # Configuration directories
    confdirs = [os.path.dirname(os.path.realpath(__file__)),
                "/usr/share/ambientsounds/",
                os.path.expanduser("~/.config/ambientsounds/")]

    def __init__(self):
        Volume.__init__(self, "Volume", 100)

        # Get the sounds
        self.sounds = []
        for dirname in self.confdirs:
            sounddir = os.path.join(dirname, "sounds")
            if os.path.isdir(sounddir):
                for filename in os.listdir(sounddir):
                    self.sounds.append(Sound(os.path.join(sounddir, filename), self))

        pygame.mixer.set_num_channels(len(self.sounds))

        # Get the presets
        self.presets = []
        for dirname in self.confdirs:
            presetdir = os.path.join(dirname, "presets")
            if os.path.isdir(presetdir):
                for filename in os.listdir(presetdir):
                    self.presets.append(Preset(os.path.join(presetdir, filename), self))

    def get_sounds(self):
        """
        Returns the list of available tracks
        """
        return self.sounds

    def get_presets(self):
        """
        Returns the list of available presets
        """
        return self.presets

    def _set_volume(self):
        """
        Update the volume of all the sounds
        """
        for sound in self.sounds:
            sound._set_volume()
