# TMdecoder

A program to decode and display LASP-Strateole2 Telemetry Messages (TMs).
These messages are transmitted in real-time via the Zephyr system,
and stored locally on the LPC mainboard SD card.
The output is printed in CSV format. A CSV header is included. An option
for saving to a CSV file is provided.

The program attempts to determine which instrument the file contins 
data for LPC or RS41. If it cannot determine this automatically,
use the `-l` or `-r` switches.

There are two sample TMs included here which can be used to try out the application:

- `TM.RS41.ready_tm`: An RS41 telemetry message
- `TM.LPC.ready_tm`: An LPC telemetry message.

The `.ready_tm` file extension is the convention that CNES uses for
the files created by their ground system.

The `.dump` files are the text output from a binary dump made
with the `od` program. They are useful for diagnosing the internal
format of the TM messages. They were created with the Linux `od` command:
```sh
od -a -t x1 -A d  TM.LPC.ready_tm > TM.LPC.dump
```

# Installation

```sh
pip3 install xmltodict
git clone https://github.com/MisterMartin/TMdecoder.git
```

## Test

```sh
cd TMdecoder
python3 TMdecoder.py -o rs41.csv TM.RS41.ready_tm
python3 TMdecoder.py -o lpc.csv TM.LPC.ready_tm
```

## Usage

```python3 TMdecoder.h -h``` displays help:

```text
usage: TMdecoder [-h] [-l] [-r] [-c CSV] [-b] [-t] [-q] filename

Decode a LASP StratoCore TM message and produce CSV

positional arguments:
  filename           TM message file, or file extension (for batch processing)

optional arguments:
  -h, --help         show this help message and exit
  -l, --lpc          LPC file
  -r, --rs41         RS41 file
  -c CSV, --csv CSV  Save CSV to a file
  -b, --batch        Batch process, creating .csv files
  -t, --tm           Print the TM header
  -q, --quiet        Turn off printing

If -l or -r are not specified, try to automatically determine the msg type. Only one of -c or -b is allowed. In batch mode, the current directory is searched for the
files.'
```

# N.B.

The LPC message binary section decoding was adapted from 
`readPCXML_2021.py`.