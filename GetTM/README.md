# GetTM

# bitstruct

`bitstruct` would not install on my older iMac, failing with:
```sh
     ld: library 'System' not found
      clang: error: linker command failed with exit code 1 (use -v to see invocation)
      error: command '/usr/local/bin/clang' failed with exit code 1

```

To get it to install, I did the following:
- downgraded my Xcode to one that matched
  MacOS 13.7.4. I got it from https://xcodereleases.com.
```sh
export LDFLAGS=-L/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/lib
pip install bitstruct
```

It's not clear that I needed to downgrade `Xcode`
