# Examples

This chapter collects all verification and test notebooks. Each notebook is self-contained and targets a specific block or system-level behaviour. They are organised into two groups: **device verification** (individual RF components tested in isolation) and **system verification** (end-to-end signal chain tests).

All notebooks load their pipeline from a YAML configuration file in the same directory, keeping test parameters easy to inspect and modify without touching the notebook cells.

The four system-performance notebooks under `verification/` (BER, EVM, Link Budget, and Signal Generation Demo) share a common setup helper, `verification/tx_setup.py`. Its `build_test_setup(...)` function generates the PRBS / QAM / OFDM payload, scales it to a target average input power, and instantiates the TX → channel → RX pipeline from `Tx_channel_Rx.yaml`. Start with the **Signal Generation Demo** notebook to see this end-to-end before reading the BER and EVM notebooks.

---

## Device Verification

### LNA — Nonlinearity

**Notebook:** `test_benches/Devices/LNA/LNA_Verification_Non_linear.ipynb`

Demonstrates the IIP3 measurement procedure for the LNA using the standard two-tone method. A real two-tone RF signal is constructed and down-converted to the complex baseband. The input power is swept over a wide range using a scale-factor approach, and the spectrum analyser is used to track the fundamental tone power and the third-order intermodulation (IM3) product power at each sweep point.

The resulting curves (fundamental: slope ~1 dB/dB, IM3: slope ~3 dB/dB) are fitted in the linear regime and extrapolated to their intersection, giving the input-referred IIP3. The measured intercept point is compared against the configured `IP3_dbm` parameter and the error is printed.

**Key checks:**
- Fundamental slope ≈ 1 dB/dB
- IM3 slope ≈ 3 dB/dB
- Measured IIP3 matches configured value

---

### LNA — Noise Figure

**Notebook:** `test_benches/Devices/LNA/LNA_Verification_noise.ipynb`

Verifies the LNA noise model. A thermal noise source at temperature $T = 290$ K with power $kTB$ is generated as the input signal. The signal is passed through the LNA and the output noise power is measured. The noise figure is computed as:

$$F = \frac{P_{n,\text{out}}}{G \cdot kTB}$$

The measured noise figure is compared against the configured `nf_db` parameter. The input and output noise power spectral densities are plotted to verify the flat noise floor and the added noise from the amplifier.

**Key checks:**
- Measured NF matches configured `nf_db`
- Output noise PSD is uniformly elevated above input noise floor by the noise factor

---

### PA — Compression and Model Comparison

**Notebook:** `test_benches/Devices/PA/PA_test.ipynb`

Tests the PA block across a range of input powers to characterise the AM-AM compression curve. The notebook includes:

1. **Small-signal gain check** — verifies the gain at low input power matches `gain_db`
2. **Compression sweep** — sweeps input power from −30 to +20 dBm, measures output power and gain at each point, and identifies the 1 dB compression point
3. **Comparison of Rapp vs cubic model** — runs the same sweep with both models enabled and overlays the results, illustrating the difference in compression shape and the cubic model's unphysical gain reversal above P1dB

The Rapp model is the recommended default for PA simulation; the cubic model is provided for analytical compatibility.

**Key checks:**
- Small-signal gain matches `gain_db`
- Measured output P1dB matches configured `p1db_out_dbm`
- Rapp model saturates gracefully; cubic model diverges well above P1dB

---

### Mixer — Linearity and Noise

**Notebook:** `test_benches/Devices/Mixer_PLL/Mixer_Verification.ipynb`

A multi-part verification of the mixer block covering three test cases:

1. **Ideal mixer verification** — disables all impairments (`mixer_ideal=True`) and verifies that signal power is preserved exactly through the mixer. The input and output spectra are overlaid to confirm no distortion.

2. **IIP3 two-tone test** — following the same procedure as the LNA nonlinearity test, a two-tone complex envelope input is swept in power and the fundamental/IM3 powers are tracked. Linear fits are extrapolated to find the IIP3 and verify it against the configured `iip3_dbm`.

3. **Noise figure test** — uses a thermal noise input to measure the mixer's added noise and compute the noise figure, following the same method as the LNA noise notebook.

**Key checks:**
- Ideal mixer: power ratio = 1.0
- Measured IIP3 matches `iip3_dbm`
- Measured NF matches `nf_db`

---

### PLL — Phase Noise Verification

**Notebook:** `test_benches/Devices/Mixer_PLL/PLL_Verification.ipynb`

Verifies the PLL phase noise model by generating an LO signal from the PLL and measuring its phase noise spectrum. The phase noise curve is extracted using the phase noise analyser and compared against the configured model parameters.

The notebook illustrates the two-region PLL noise shape: the low-frequency region dominated by reference noise (flat response inside the loop bandwidth) and the high-frequency VCO $1/f^2$ region outside the loop bandwidth. The crossover point at the loop bandwidth $f_L$ is clearly visible in the measured PSD.

**Key checks:**
- Phase noise at the configured offset matches `VCO_Phase_Noise_dBc`
- Loop bandwidth knee visible at `f_L`
- Noise floor at low offsets matches `SLF_dBc`

---

## System Verification

### Channel Modelling

**Notebook:** `test_benches/System/Channel/Channel_modelling.ipynb`

Demonstrates the channel model blocks. Covers free-space path loss computation using the Friis equation and AWGN channel effects on a known signal. Shows how path loss and noise combine in a realistic propagation scenario.

---

### OFDM and QAM

**Notebook:** `test_benches/System/OFDM_QAM/OFDM_QAM_test.ipynb`

End-to-end test of the OFDM/QAM signal processing chain:

- PRBS bit generation
- QAM modulation and constellation visualisation
- OFDM modulation: FFT spectrum, cyclic prefix, guard bands
- OFDM demodulation and QAM demapping
- BER computation for a given SNR

This notebook establishes the baseline communication chain without RF impairments, verifying that the modulator/demodulator pair is error-free in an ideal (noiseless) scenario.

---

### Payload Generation

**Notebook:** `test_benches/System/Payload_Generation/payload.ipynb`

Covers the generation of a complete baseband payload: PRBS bits → QAM symbols → OFDM waveform. Shows the signal at each processing stage and characterises the statistical properties (PAPR, power distribution) of the resulting complex baseband waveform before it enters the RF chain.

---

### Signal Generation Demo

**Notebook:** `verification/Signal_Generation_Demo.ipynb`

Walks through how a complete OFDM baseband payload is built up step by step: PRBS-15 bit generation, Gray-coded 64-QAM mapping, OFDM modulation (active subcarriers, IFFT, cyclic prefix), and power scaling to a target input level. The notebook ends by loading the full TX → channel → RX pipeline from `Tx_channel_Rx.yaml`. This is the recommended entry point before reading the BER, EVM, or Link Budget notebooks — those four share the same setup, wrapped into `verification/tx_setup.py:build_test_setup()`.

---

### Link Budget Verification

**Notebook:** `verification/Link_Budget.ipynb`

Compares the analytical per-block power budget (gain, loss, and noise figure computed cascade-style from the YAML) against the simulated power at every tap of the RF pipeline. Includes a sweep over input power to expose where compression sets in.

**Key checks:**
- Tap-by-tap power matches the analytical budget within a few tenths of a dB in the linear regime
- Cumulative noise figure grows according to Friis' formula
- PA compression appears at the expected input power on the sweep

---

### EVM Verification

**Notebook:** `verification/EVM.ipynb`

Measures the RMS EVM at two reference planes (after the PA, and after the full chain) and produces two 2-D sweeps:

1. **EVM vs PLL parameters** — VCO phase noise at 1 MHz offset × PLL loop bandwidth, with multiple phase-noise realisations averaged per grid point
2. **EVM vs I/Q imbalance** — amplitude imbalance (dB) × phase imbalance (degrees) using the standard $y = K_1 x + K_2 x^*$ complex-baseband model

A single-point I/Q imbalance cell at the end reports the EVM penalty for a user-chosen $(\varepsilon, \theta)$ pair against the balanced reference.

---

### BER Verification

**Notebook:** `verification/BER.ipynb`

End-to-end Bit Error Rate of the full chain, in four parts:

1. Point BER at the nominal SNR, together with the receive-side SNR and Eb/N0
2. BER vs Eb/N0 sweep, compared against the theoretical QAM-in-AWGN curve
3. **Chip-input sensitivity sweep** — channel AWGN bypassed, so only the LNA + RX-mixer NF add noise. Measures true chip sensitivity, referenced to the LNA input plane.
4. **Bench-test sensitivity** — TX chain bypassed, AWGN floor held fixed at $kTB$. Emulates a signal generator wired directly to the LNA, with the AWGN SNR recomputed at every sweep point to keep the noise power constant.

This and the EVM notebook are the primary tools for assessing the overall impact of RF impairments on system performance and comparing against the specification targets in the project report.
