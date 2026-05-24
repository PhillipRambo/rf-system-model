# Signal Generation Demo

A walk-through of how a complete OFDM baseband payload is built up from PRBS bits, what the intermediate signals look like, and how the same setup is wrapped into the `build_test_setup()` helper used by the BER, EVM, and Link Budget notebooks.

The notebook covers:

- **PRBS bit generation** — configuring a PRBS-15 source with a fixed seed
- **QAM mapping** — bit groups to Gray-coded 64-QAM symbols, with a constellation plot
- **OFDM modulation** — packing QAM symbols onto active subcarriers, IFFT, cyclic prefix, and the resulting time-domain waveform / spectrum
- **Power scaling** — rescaling the OFDM waveform to a target average input power in dBm
- **Pipeline loading** — instantiating the full TX → channel → RX pipeline from `Tx_channel_Rx.yaml`

This is the recommended starting point for understanding the verification setup before running BER or EVM sweeps.

## Pipeline configuration

The pipeline used here and in the other verification notebooks is defined in:

```{literalinclude} ../../verification/Tx_channel_Rx.yaml
:language: yaml
```
