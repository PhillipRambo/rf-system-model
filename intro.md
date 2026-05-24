# RF PLL System Model

**rf-system-model** is a Python package for behavioural simulation of RF signal chains with integrated PLL phase noise modelling. It is designed to support end-to-end analysis of wireless communication systems at the complex baseband level, connecting device-level impairments — nonlinearity, noise figure, and phase noise — to system-level performance metrics such as EVM and BER.

The package was developed as part of an R&D project (Kandidat, 2nd semester) investigating the impact of RF front-end and local oscillator impairments on OFDM-based communication systems.

---

## What the package can do

- **RF front-end modelling** — LNA, PA, and Mixer blocks with configurable gain, nonlinearity (IIP3 / P1dB), and noise figure
- **PLL phase noise simulation** — two-region noise model (reference noise + VCO noise) shaped by the loop filter, with optional OFDM subcarrier weighting
- **Channel effects** — additive white Gaussian noise (AWGN) and free-space path loss via the Friis equation
- **Communication waveforms** — PRBS bit generation, Gray-coded QAM modulation (4–256-QAM), and OFDM modulation/demodulation with configurable FFT size and cyclic prefix
- **Measurement and analysis** — spectrum analysis, phase noise curves, EVM and BER computation
- **Flexible pipeline system** — build complete signal chains from YAML or Python, tap intermediate signals for debugging, enable/disable or swap blocks at runtime

All models operate on **complex baseband (analytic) signals** where $|x(t)|^2$ is instantaneous power in watts. This convention is used consistently across the entire package.

---

## Documentation overview

```{tableofcontents}
```

| Chapter | Contents |
|---|---|
| {doc}`docs/core_framework` | Signal, Block, Pipeline, YAML configuration, registry pattern |
| {doc}`docs/components` | All implemented blocks: RF devices, channel models, comms, measurement |
| {doc}`docs/examples_intro` | Annotated notebooks covering device and system-level verification |

For theoretical background, derivations, and system specifications, please refer to the project report located in the repository root.

---

## Contact

**Phillip Rambo** — phillipfbp@gmail.com
