# Link Budget Verification

Compares the **analytical** per-block power budget — gain, loss, and noise contribution computed cascade-style from the YAML parameters — against the **simulated** power measured at every tap of the RF pipeline.

The notebook proceeds in four steps:

1. **Pipeline setup** — loads the TX/channel/RX chain via `build_test_setup()` and renders the block diagram
2. **Analytical link budget** — applies gain, path loss, and noise figure block-by-block to produce expected power and noise at each plane
3. **Simulated power per tap** — runs the pipeline once and reads the actual power at each tap with the spectrum analyser
4. **Sweep over input power** — confirms the analytical/simulated agreement holds across the full operating range, exposing where compression sets in

**Key checks:**
- Tap-by-tap power matches the analytical budget within a few tenths of a dB in the linear regime
- Cumulative noise figure grows according to Friis' formula
- Compression of the PA appears at the expected input power level on the sweep

## Pipeline configuration

```{literalinclude} ../../verification/Tx_channel_Rx.yaml
:language: yaml
```
