# T3Num
written by René Mathes

**T3Num** can be used to enumerate most of the public extensions used by a Typo3 CMS website. If an extension is not in the TER, this script will not enumerate it.

Do not use it for bad things. Use your brain.

## Usage
```sh
$ ./t3num.py [-h] [--target TARGET] [--force] [--output OUTPUT] [--sysext] [--update]
             [--use-get] [--no-check-certificate]

    --target                    base URL of the Typo3 website
    --force                     continue enumeration even though typo3/index.php can not be found
    --output                    file to output results
    --sysext                    enumerate Typo3 sysext instead of normal extensions
    --update                    update Typo3 extensions.xml from a TER mirror
    --use-get                   use HTTP GET instead of HTTP HEAD requests
    --no-check-certificate      do not validate SSL/TLS certificates
```

## Requirements
* python 2.7

## Things to do
* more enumeration
* more documentation (but then... it's not rocket science)
* ...

## License
GPL v3.0
