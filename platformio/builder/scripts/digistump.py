# Copyright (C) Ivan Kravets <me@ikravets.com>
# See LICENSE for details.

"""
    Builder for Digistump boards
"""

from os.path import join

from SCons.Script import (COMMAND_LINE_TARGETS, AlwaysBuild, Default,
                          DefaultEnvironment, SConscript)

env = DefaultEnvironment()

if "cortex" in env.get("BOARD_OPTIONS").get("build").get("cpu", ""):
    env = SConscript(
        env.subst(join("$PIOBUILDER_DIR", "scripts", "basearm.py")),
        exports="env")
    env.Replace(
        UPLOADER=join("$PIOPACKAGES_DIR", "$PIOPACKAGE_UPLOADER", "bossac"),
        UPLOADERFLAGS=[
            "--info",
            "--debug",
            "--port", "$UPLOAD_PORT",
            "--erase",
            "--write",
            "--verify",
            "--boot"
        ],
        UPLOADCMD='"$UPLOADER" $UPLOADERFLAGS $SOURCES'
    )

    env.Append(
        CPPDEFINES=[
            "printf=iprintf"
        ],

        LINKFLAGS=[
            "-Wl,--entry=Reset_Handler",
            "-Wl,--start-group"
        ]
    )
else:
    env = SConscript(env.subst(
        join("$PIOBUILDER_DIR", "scripts", "baseavr.py")), exports="env")
    env.Replace(
        UPLOADER=join("$PIOPACKAGES_DIR", "tool-avrdude", "avrdude"),
        UPLOADERFLAGS=[
            "-q",  # suppress progress output
            "-D",  # disable auto erase for flash memory
            "-p", "$BOARD_MCU",
            "-C", '"%s"' % join("$PIOPACKAGES_DIR",
                                "tool-avrdude", "avrdude.conf"),
            "-c", "$UPLOAD_PROTOCOL",
            "-b", "$UPLOAD_SPEED",
            "-P", "$UPLOAD_PORT"
        ],
        UPLOADCMD='"$UPLOADER" $UPLOADERFLAGS -U flash:w:$SOURCES:i'
    )

CORELIBS = env.ProcessGeneral()

#
# Target: Build executable and linkable firmware
#

target_elf = env.BuildFirmware(["m"] + CORELIBS)

#
# Target: Build the firmware file
#

if "cortex" in env.get("BOARD_OPTIONS").get("build").get("cpu", ""):
    if "uploadlazy" in COMMAND_LINE_TARGETS:
        target_firm = join("$BUILD_DIR", "firmware.bin")
    else:
        target_firm = env.ElfToBin(join("$BUILD_DIR", "firmware"), target_elf)
else:
    if "uploadlazy" in COMMAND_LINE_TARGETS:
        target_firm = join("$BUILD_DIR", "firmware.hex")
    else:
        target_firm = env.ElfToHex(join("$BUILD_DIR", "firmware"), target_elf)

#
# Target: Print binary size
#

target_size = env.Alias("size", target_elf, "$SIZEPRINTCMD")
AlwaysBuild(target_size)

#
# Target: Upload by default firmware file
#

upload = env.Alias(["upload", "uploadlazy"], target_firm, ("$UPLOADCMD"))
AlwaysBuild(upload)

#
# Target: Define targets
#

Default([target_firm, target_size])