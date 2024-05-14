# Eye Tracker App

This app is designed for demo purpose on Windows platform. It should run on MacOS and Linux as well but untested.

## Simulated Run Instructions for Windows

To simulate coordinates data from COM port on a Windows desktop, follow these steps:

1. Download from https://freevirtualserialports.com/ and install **virtual serial port device**.
2. Run the above application, create a `Local Bridge` with default options (first port name is `COM1` and second port name is `COM2`)
3. Download **[Coordinates_Serial_Generator](https://github.com/richardzone/coordinates_serial_generator/releases/)** and run it. You should see log output like below:
    ```log
    Sent to COM2: b'[77, 388]'

    Sent to COM2: b'[1432, 130]'

    Sent to COM2: b'[925, 230]'

    Sent to COM2: b'[350, 358]'

    Sent to COM2: b'[633, 336]'

    Sent to COM2: b'[739, 597]'
    ```

4. Finally download **[this app (Eye Tracker App)](https://github.com/richardzone/eye-tracker-app/releases/)** and run it. Select Serial Port `COM1` and click `Connect to Serial (Hit Esc to Disconnect)`. You should see the mouse cursor moving around, triggered by data sent via serial port from the **Coordinates_Serial_Generator**.


## Local dev environment setup

1. Install Python >= 3.12
2.
```shell
./venv/bin/activate
pip install -e .
pytest # to run tests
python run.py # to run app
pyinstaller -y --windowed --add-data translations:translations run.py # to create app release in dist folder
```
