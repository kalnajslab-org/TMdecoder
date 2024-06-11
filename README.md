# TMdecoder

A program to decode and display LASP-Strateole2 Telelemetry Messages (TMs).
The output is in CSV format. A CSV header is included.

*It currently only decodes RS41 TM files. LPC compatibilty is under construction*

There are two sample TMs inlcuded here which can be used to try out the application:

- `TM.RS41.ready_tm`: An RS41 telemetry message
- `TM.LPC.ready_tm`: An LPC telemetry message.

The `.ready_tm` file extension is the convention that CNES uses for
the files created by their ground system.

The `.dump` files are the text output from a binary dump made
with the `od` program. They are useful for diagnosing the internal
format of the TM messages.

# Installation

```sh
pip3 install xmltodict
git clone https://github.com/MisterMartin/TMdecoder.git
```

## Test
```sh
cd TMdecoder
python3 TMdecoder.py -o csv.txt TM.RS41.ready_tm
```

## Usage

```python3 TMdecoder.h -h``` displays help:

```text
usage: TMdecoder [-h] [-o OUTFILE] [-q] filename

Decode a LASP StratoCore TM message and produce CSV

positional arguments:
  filename              TM message file

optional arguments:
  -h, --help            show this help message and exit
  -o OUTFILE, --outfile OUTFILE
                        Save CSV to a file
  -q, --quiet           Turn off printing
```
