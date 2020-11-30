# wotstats

Self-hosted World of Tanks player statistics

[DEMO](https://wotstats.krystianch.com/)

## Description

The `wotstats` Python script does the following after invocation:

* fetches current statistics from the official World of Tanks API,
* saves them to the data file,
* generates a *svg* plot that shows stats changing in time.

This script should be run periodically to update the plot using the newest data.
If you want fairly frequent updates, run it hourly.
You can use the provided systemd unit and timer.

Keep in mind that the WoT API does not update its data instantly.
After you play a battle, you might have to wait a few hours for the changes to reach the WoT API.

If you want the plots available as a webpage, you can use the provided html and css.
If you choose to, configure the script to generate plots in the `img` directory by setting the `plotdir` parameter.

## Requirements

Python >= 3.8 and packages from [requirements.txt](requirements.txt).

## Usage

```text
$ ./wotstats --help
usage: wotstats [-h] --application-id APPLICATION_ID --account ACCOUNT [ACCOUNT ...] [--api-root API_ROOT] [--clean] [--nofetch] [-v] datafile plotdir

positional arguments:
  datafile              file containing stats history
  plotdir               directory where the plots will be created

optional arguments:
  -h, --help            show this help message and exit
  --application-id APPLICATION_ID
                        get one from developers.wargaming.net
  --account ACCOUNT [ACCOUNT ...]
                        ids of accounts to track
  --api-root API_ROOT   API root for your realm (defaults to EU API)
  --clean               clean the datafile
  --nofetch             don't fetch current stats
  -v, --verbose         be more verbose
```

Example:

```bash
./wotstats \
    --application-id d1e3a3d7b1e3e3f7d1e3a3d7b1e3e3f7 \
    wotstats.csv \
    static/img \
    --account 133773311 733113377
```
