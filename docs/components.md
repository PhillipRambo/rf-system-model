# Components

This chapter describes all implemented signal processing blocks. Every block follows the same interface (see {doc}`core_framework`) and operates on complex baseband signals where $|x|^2$ is instantaneous power in watts.

For theoretical derivations behind the models, refer to the project report in the repository root.

---

## RF Devices

### LNA — Low Noise Amplifier

`rfmodel.rf.LNA` — `LNABlock`, `LNAParams`

The LNA model captures the two dominant impairments of a physical low-noise amplifier: **gain with thermal noise** and **memoryless third-order nonlinearity**.

**Parameters**

| Parameter | Description |
|---|---|
| `gain_db` | Small-signal power gain in dB |
| `nf_db` | Noise figure in dB |
| `IP3_dbm` | Input-referred third-order intercept point (IIP3) in dBm |
| `temp_k` | Physical temperature in Kelvin (default: 290 K) |

**What the model does**

1. **Linear gain** — scales the signal amplitude by $\alpha = \sqrt{G}$
2. **Cubic nonlinearity** — applies $y = \alpha x - \beta |x|^2 x$ where $\beta$ is derived from IIP3. This models gain compression and generates intermodulation distortion (IM3) products from multi-tone inputs.
3. **Output noise** — adds complex Gaussian noise with power $(F-1) \cdot kTG \cdot B$ where $F$ is the noise factor, $B = f_s/2$ is the noise bandwidth, and $G$ is the linear power gain.

**What can be demonstrated**

- Gain verification (small-signal)
- IIP3 extraction via two-tone sweep (1:1 fundamental slope, 3:1 IM3 slope)
- Noise figure measurement from output noise floor
- Cascaded noise figure in multi-block pipelines

**Example**

```python
from rfmodel.rf.LNA import LNABlock, LNAParams

lna = LNABlock("lna1", LNAParams(gain_db=20, nf_db=3.0, IP3_dbm=10.0), seed=1)
sig_out = lna.process(sig_in)
```

---

### PA — Power Amplifier

`rfmodel.rf.PA` — `PABlock`, `PAParams`

The PA model offers two selectable AM-AM compression laws suited to different use cases.

**Parameters**

| Parameter | Description |
|---|---|
| `gain_db` | Small-signal power gain in dB |
| `p1db_out_dbm` | Output 1 dB compression point in dBm |
| `smoothness_p` | Rapp model knee sharpness (default: 2.0, larger = sharper) |
| `enable_cubic` | If `True`, use cubic model instead of Rapp (default: `False`) |

**Rapp model (default)**

The Rapp soft compression model provides a smooth, physically realistic AM-AM characteristic that saturates gracefully above P1dB:

$$r_\text{out} = \frac{g \cdot r}{\left(1 + (g \cdot r / A_\text{sat})^{2p}\right)^{1/(2p)}}$$

The saturation parameter $A_\text{sat}$ is solved automatically to place the 1 dB compression point exactly at the specified `p1db_out_dbm`. The `smoothness_p` parameter controls the transition sharpness — higher values produce a sharper knee, closer to an ideal hard limiter.

**Cubic model**

The cubic model $y = \alpha x - \beta |x|^2 x$ provides an analytic approximation valid near and slightly below P1dB. The coefficient $\beta$ is derived from the P1dB specification. This model goes unphysical (output reversal) well above P1dB and is primarily useful for analytical work and low-order distortion studies.

**What can be demonstrated**

- Gain compression sweep and P1dB extraction
- Comparison between Rapp and cubic AM-AM characteristics
- Impact of PA nonlinearity on EVM and spectral regrowth

**Example**

```python
from rfmodel.rf.PA import PABlock, PAParams

# Rapp model
pa = PABlock("pa1", PAParams(gain_db=30, p1db_out_dbm=27, smoothness_p=5))

# Cubic model
pa_cubic = PABlock("pa1", PAParams(gain_db=30, p1db_out_dbm=27, enable_cubic=True))
```

---

### Mixer and PLL

`rfmodel.rf.Mixer_PLL_block` — `MixerBlock`, `MixerParams`, `PLL`, `PLLParams`

The Mixer block combines a frequency conversion model with an integrated PLL phase noise impairment. This makes it the most complex block in the RF chain, as it simultaneously models conversion gain, nonlinearity, noise figure, and LO phase noise.

#### Mixer

**Parameters (`MixerParams`)**

| Parameter | Description |
|---|---|
| `gain_db` | Conversion gain in dB |
| `iip3_dbm` | Input-referred IIP3 in dBm |
| `iip2_dbm` | Input-referred IIP2 in dBm (optional; `None` disables 2nd-order distortion) |
| `nf_db` | Noise figure in dB |
| `temp_k` | Physical temperature (default: 290 K) |
| `pll` | `PLLParams` instance, or `None` to disable phase noise |
| `mixer_ideal` | If `True`, bypasses all impairments (gain, NL, noise) — useful for isolating PLL effects |

The nonlinearity and noise models are identical in structure to the LNA, with an optional second-order term controlled by `iip2_dbm`. When `pll` is configured, the block first multiplies the input signal by the PLL-generated LO phasor $e^{j\phi(t)}$, then applies gain, nonlinearity, and noise.

#### PLL Phase Noise Model

**Parameters (`PLLParams`)** — the column **YAML key** shows the name used in YAML configs (these differ from the Python attribute names in `PLLParams`).

| Python attribute | YAML key | Description |
|---|---|---|
| `VCO_Phase_Noise_dBc` | `VCO_PhaseNoise` | Tuple `[dBc, f_offset]` specifying the VCO phase noise level at a reference offset |
| `SLF_dBc` | `LF_noise_floor` | Low-frequency noise floor in dBc/Hz |
| `f_L` | `loop_bandwidth` | PLL loop bandwidth in Hz |
| `Tu` | `Tu` | OFDM useful symbol duration (required when subcarrier weighting is enabled) |
| `enable_ofdm_weighting` | `enable_ofdm_weighting` | Apply OFDM subcarrier weighting function (default: `False`) |
| `f_range_limits` | `Foffset_Range` | Frequency range for PSD evaluation (default: 10 Hz to 10 GHz) |
| `vco_noise_floor_dbc` | `vco_noise_floor` | Far-from-carrier VCO thermal floor in dBc/Hz (optional; `None` disables it) |

The phase noise PSD combines two regions shaped by the loop filter:

- **Inside the loop bandwidth** ($f < f_L$): reference oscillator noise, modelled as a flat noise floor (low-pass characteristic)
- **Outside the loop bandwidth** ($f > f_L$): free-running VCO noise following a $1/f^2$ Lorentzian spectrum (high-pass characteristic)

The time-domain LO impairment $e^{j\phi(t)}$ is generated via an FFT-based shaping method: a white noise spectrum is coloured by the target PSD, then transformed to the time domain to produce the phase trajectory $\phi(t)$.

When `enable_ofdm_weighting` is active, the phase noise PSD is filtered by the OFDM subcarrier response function, directly giving the effective phase noise contribution to each subcarrier rather than the raw single-sideband spectrum.

**What can be demonstrated**

- IIP3 and noise figure of the mixer (with PLL disabled)
- PLL phase noise PSD shape and loop bandwidth effect
- Phase noise contribution to EVM and constellation rotation/spreading
- OFDM subcarrier weighting effect on effective phase noise

**Example**

```python
from rfmodel.rf.Mixer_PLL_block import MixerBlock, MixerParams, PLLParams

pll_params = PLLParams(
    VCO_Phase_Noise_dBc=(-90, 1e6),
    SLF_dBc=-140,
    f_L=10e3,
    Tu=3.2e-6,
    enable_ofdm_weighting=False,
)

mixer = MixerBlock("mixer1", MixerParams(
    gain_db=0,
    iip3_dbm=20,
    nf_db=8,
    pll=pll_params,
))
```

---

## Channel Models

### AWGN Channel

`rfmodel.channel.AWGN` — `AWGNBlock`, `AWGNParams`

Adds complex Gaussian white noise to the signal in one of two selectable modes.

**Parameters**

| Parameter | Description |
|---|---|
| `snr_db` | Signal-to-noise ratio in dB (used in SNR mode) |
| `thermal_noise` | If `True`, switches to thermal mode and fixes the noise power at $kTB$, ignoring `snr_db` (default: `False`) |
| `temp_k` | Physical noise temperature in K, used only in thermal mode (default: 290 K) |

**SNR mode** (`thermal_noise=False`, default) — the noise power is computed from the **instantaneous signal power** at the block input: $P_n = P_s / \text{SNR}_\text{linear}$. The SNR is invariant under signal scaling, which makes this mode the natural choice for BER-vs-SNR sweeps.

**Thermal mode** (`thermal_noise=True`) — the noise power is fixed at the Johnson–Nyquist floor $P_n = kT \cdot f_s$ over the complex-baseband bandwidth. The noise is **independent of signal level**, so the SNR changes across an input-power sweep. This mode models a matched source/cable at temperature `temp_k` and is used by the bench-test sensitivity cell of the BER verification notebook.

In both modes, complex Gaussian noise is drawn with $\sigma = \sqrt{P_n/2}$ per component.

**What can be demonstrated**

- BER vs SNR curves for QAM/OFDM
- Sensitivity analysis (minimum detectable SNR)
- Comparison of theoretical and simulated BER

**Example**

```python
from rfmodel.channel.AWGN import AWGNBlock, AWGNParams

awgn = AWGNBlock("awgn", AWGNParams(snr_db=20))
```

---

### Path Loss

`rfmodel.channel.path_loss` — `PathLossBlock`, `PathLossParams`

Applies free-space path loss using the Friis transmission equation.

**Parameters**

| Parameter | Description |
|---|---|
| `freq_hz` | Carrier frequency in Hz |
| `distance_m` | Link distance in metres |
| `tx_ant_gain_db` | Transmit antenna gain in dBi (default: 0) |
| `rx_ant_gain_db` | Receive antenna gain in dBi (default: 0) |

The Friis gain is:

$$G_\text{Friis} = G_t G_r \left(\frac{\lambda}{4\pi d}\right)^2$$

The received power gain is clamped to $G_t G_r$ (unity path loss) to avoid physically unrealisable gain at very short distances. A `UserWarning` is raised if $d < 2\lambda$ (near-field regime).

**What can be demonstrated**

- Received power vs distance
- Link budget calculations
- Combined path loss + AWGN for a complete propagation channel

**Example**

```python
from rfmodel.channel.path_loss import PathLossBlock, PathLossParams

pl = PathLossBlock("path_loss", PathLossParams(
    freq_hz=2.4e9,
    distance_m=100,
    tx_ant_gain_db=3,
    rx_ant_gain_db=3,
))
```

---

## Communications Blocks

### PRBS Bit Source

`rfmodel.comms.pseudorandom_NGR` — `PRBSBitSource`, `PRBSParams`

Generates pseudo-random bit sequences using a linear feedback shift register (LFSR).

**Parameters**

| Parameter | Description |
|---|---|
| `order` | LFSR order: 7 or 15 |
| `n_bits` | Number of bits to generate |
| `seed` | Initial LFSR state (1 to $2^\text{order} - 1$) |

Supported polynomials: PRBS-7 ($x^7 + x^6 + 1$) and PRBS-15 ($x^{15} + x^{14} + 1$). The output is a 1D `uint8` array of 0s and 1s, which serves as the input to the QAM modulator.

---

### QAM Modulator

`rfmodel.comms.QAM_modulator` — `QAMModulator`, `QAMParams`

Implements square M-QAM modulation with Gray coding.

**Parameters**

| Parameter | Description |
|---|---|
| `M` | Constellation size: 4, 16, 64, or 256 |
| `gray_map` | Enable Gray coding (default: `True`) |
| `unit_average_power` | Normalise constellation to unit average power (default: `True`) |

The modulator maps groups of $\log_2 M$ bits to complex symbols drawn from a square QAM constellation. Gray coding ensures that adjacent symbols differ by only one bit, minimising BER at moderate SNR.

**Methods**

- `process(signal)` — maps bit array to complex symbols; the signal's `x` field must contain a uint8 bit array
- `demap(rx_symbols)` — hard-decision demapping (nearest-symbol slicing)

**What can be demonstrated**

- Constellation diagrams (ideal and distorted)
- BER vs SNR for different modulation orders
- Effect of phase noise and nonlinearity on constellation spreading

---

### OFDM Modulator

`rfmodel.comms.OFDM_block` — `OFDMModulator`, `OFDMParams`

Implements OFDM modulation and demodulation with configurable FFT size, cyclic prefix, and subcarrier mapping.

**Parameters**

| Parameter | Description |
|---|---|
| `n_fft` | FFT size (total number of subcarriers) |
| `cp_len` | Cyclic prefix length in samples |
| `n_data_subcarriers` | Number of active (data-carrying) subcarriers |
| `normalize_ifft` | Apply $1/\sqrt{N}$ IFFT normalisation (default: `False`) |
| `null_dc` | Null the DC subcarrier (default: `True`) |

**Modulation process**

1. Input QAM symbols are grouped into OFDM blocks of `n_data_subcarriers` symbols each
2. Symbols are placed on active subcarriers symmetrically around DC (if `null_dc=True`) or sequentially
3. An IFFT maps the frequency-domain block to a time-domain OFDM symbol
4. A cyclic prefix of length `cp_len` is prepended to each symbol

**Demodulation** reverses this process: strip CP, FFT, extract active subcarriers.

**What can be demonstrated**

- OFDM spectrum (flat over active subcarriers, guard bands at edges)
- Effect of cyclic prefix on multipath robustness
- EVM degradation from phase noise, nonlinearity, or AWGN
- Per-subcarrier SNR analysis

---

## Measurement and Analysis

### Spectrum Analyser

`rfmodel.meas.spectrum_analyser` — `spectrum_analyser(x, fs, tol=1e-12)`

Computes the power spectrum of a signal.

**Returns** `(P_bin_W, freq)` where:
- `P_bin_W` — power per FFT bin in watts
- `freq` — corresponding frequency array in Hz

**Behaviour**

- Real signals: uses `rfft`, corrects for one-sided representation (doubles non-DC/Nyquist bins)
- Complex signals: uses full FFT, no symmetry correction

The function issues a coherent sampling warning if a spectral peak shows significant energy in adjacent bins, indicating spectral leakage.

**Example**

```python
from rfmodel.meas.spectrum_analyser import spectrum_analyser

P, f = spectrum_analyser(sig.x, sig.fs_hz)
P_dbm = 10 * np.log10(P / 1e-3 + 1e-30)
```

---

### Phase Noise Analyser

`rfmodel.meas.phase_noise_analyser` — `calculate_phase_noise_curve(...)`

Extracts a phase noise curve from a modulated or CW signal by unwrapping the instantaneous phase and computing its power spectral density via Welch's method.

**Key parameters**

| Parameter | Description |
|---|---|
| `y` | Complex input signal |
| `fs` | Sampling rate in Hz |
| `nperseg` | Welch segment length (default: $2^{14}$) |
| `target_offset` | Offset frequency at which to report phase noise (default: 1 MHz) |
| `band` | Number of bins to average around target offset |

**Returns** `(offset_freq, L_f_dBc_Hz, pn_at_target)` — the phase noise curve, and the value at the specified offset frequency.

**What can be demonstrated**

- Measured PLL phase noise vs configured model
- Loop bandwidth identification from the PSD shape
- Integrated phase noise over a specified bandwidth

---

## Plotting Utilities

`rfmodel.plot_utils` provides a set of high-level plotting functions for common RF and communications visualisations.

### Spectrum plot

```python
from rfmodel.plot_utils.spectrum_plot import plot_top_spectrum
plot_top_spectrum(freq, P_bin_W, n_peaks=4)
```

Plots a power spectrum in dBm, annotates the strongest peaks, and optionally zooms to the signal region.

### OFDM and constellation plots

```python
from rfmodel.plot_utils.OFDM_plots import (
    plot_constellation,
    plot_ofdm_frequency_bins,
    plot_time_signal,
    plot_spectrum,
    plot_bits,
    plot_constellation_with_bits,
)
```

| Function | Description |
|---|---|
| `plot_constellation(x)` | Scatter plot of complex symbols |
| `plot_constellation_with_bits(symbols, bits, ...)` | Constellation with bit labels annotated |
| `plot_ofdm_frequency_bins(Xk)` | Stem plot of FFT bin magnitudes |
| `plot_time_signal(x)` | Real and imaginary parts vs sample index |
| `plot_spectrum(x, fs_hz)` | Magnitude spectrum in dB |
| `plot_bits(bits)` | Step plot of a bit sequence |

### Pipeline diagram

```python
from rfmodel.plot_utils.plot_block_diagram import plot_pipeline
plot_pipeline(pipe)
```

Draws a schematic of the pipeline with blocks rendered as rectangles. Mixer blocks are shown as circles with a cross (standard mixer symbol) with the PLL shown as a sub-block below. Useful for quickly visualising a configured system.
