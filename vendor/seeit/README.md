# Seeit Vendor DLL Folder

Place the vendor-supplied native USB relay DLL in this folder:

```text
vendor/seeit/usb_relay_device.dll
```

This allows the Seeit USBB native USB driver to load the DLL directly from the
portable Test in a Box folder. No administrator rights or system-wide DLL
installation are required.

## Architecture

The DLL architecture must match the portable Python installation:

- 64-bit Python requires the 64-bit DLL.
- 32-bit Python requires the 32-bit DLL.

A mismatch normally produces a Windows DLL load error.

## Licensing

The DLL is vendor software and is not distributed with Test in a Box.

Obtain it from the hardware supplier and confirm that its licence permits your
intended use. Do not commit the DLL to the public repository unless you have
confirmed redistribution permission.

https://www.seeit.fr/telechargement.php?page=dl&switch=y

## Alternative locations

The driver also supports:

- an absolute DLL path configured in the Instrument Library;
- the `TIAB_USB_RELAY_DLL` environment variable;
- the current working directory;
- the native USB driver directory.

The `vendor/seeit/` folder is the recommended portable, no-admin location.
