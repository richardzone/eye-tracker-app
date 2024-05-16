# Eye Tracker App

[![Python Version Badge](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Frichardzone%2Feye-tracker-app%2Fmaster%2Fpyproject.toml)](https://github.com/richardzone/eye-tracker-app/blob/master/pyproject.toml)
[![Build Status Badge](https://img.shields.io/github/actions/workflow/status/richardzone/eye-tracker-app/python-app-windows.yml)](https://github.com/richardzone/eye-tracker-app/actions)

This companion app will listen for commands input from eye tracker hardware via serial port and execute its commands accordingly.

Currently there are 3 types of commands:
1. A pair of coordinates between `(0,0)` and `(SCREEN_WIDTH, SCREEN_HEIGHT)` - move the mouse cursor to the specified coordinates
2. `calibration_required` - show a red calibration square on center of screen
3. `calibration_done` - hide the calibration square if present

Note that all commands MUST ends with `\n` to be valid.

This app is designed for demo purpose on Windows platform. It should run on MacOS and Linux as well but untested.

## Simulated Run Instructions for Windows

To simulate coordinates data from COM port on a Windows desktop, follow these steps:

1. Download from https://freevirtualserialports.com/ and install **virtual serial port device**.
2. Run the above application, create a `Local Bridge` with default options (first port name is `COM1` and second port name is `COM2`)
3. Download **[Coordinates_Serial_Generator](https://github.com/richardzone/coordinates_serial_generator/releases/)** and run it. You should see log output like below:
    ```log
    Sent to COM2: calibration_done

    Now sleeping for 1.31 seconds

    Sent to COM2: (1522, 226)

    Now sleeping for 0.53 seconds

    Sent to COM2: calibration_done

    Now sleeping for 1.73 seconds

    Sent to COM2: calibration_required

    Now sleeping for 0.91 seconds
    ```

4. Finally download **[this app (Eye Tracker App)](https://github.com/richardzone/eye-tracker-app/releases/)** and run it. Select Serial Port `COM1` and click `Connect to Serial (Hit Esc to Disconnect)`. You should see the mouse cursor moving around, triggered by data sent via serial port from the **Coordinates_Serial_Generator**.


## Local dev environment setup

1. Install Python >= 3.12
2.
```shell
./venv/bin/activate
pip install -e .
python run.py # to run app
pytest # to run tests
pyinstaller -y --windowed --add-data translations:translations run.py # to create app release in dist folder
```
