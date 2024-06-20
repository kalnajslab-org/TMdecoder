# TMdecoder

A program to decode and display LASP-Strateole2 Telemetry Messages (TMs).
The output is printed in CSV format. A CSV header is included. An option
for saving to a CSV file is provided.

You must specify on the command line which type of file is
being processed, either LPC or RS41.

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
python3 TMdecoder.py -r -o rs41.csv TM.RS41.ready_tm
python3 TMdecoder.py -l -o lpc.csv TM.LPC.ready_tm
```

## Usage

```python3 TMdecoder.h -h``` displays help:

```text
usage: TMdecoder [-h] [-l] [-r] [-o OUTFILE] [-q] filename

Decode a LASP StratoCore TM message and produce CSV

positional arguments:
  filename              TM message file

optional arguments:
  -h, --help            show this help message and exit
  -l, --lpc             LPC file
  -r, --rs41            RS41 file
  -o OUTFILE, --outfile OUTFILE
                        Save CSV to a file
  -q, --quiet           Turn off printing

Either -l or -r must be specified
```
hi