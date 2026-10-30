# Lab Notebook

## 2026-10-30
- First gym attempt at the isometric fatigue hold, on laptop instead of desktop PC
- Determined test parameters on right arm first (no sensor): preacher bench, 35 lb dumbbell, held to failure at ~60s at the elbow angle of peak bicep tension — photographed for later angle measurement. 35 lb confirmed as the right load for a ~30-60s target failure window
- Real recording attempt on battery power came back at only 623 Hz effective rate instead of the expected ~1000 Hz (56,564 samples over 90.8s). Saved file renamed to isometric_hold_01_FAILED_623hz.csv rather than deleted, kept as a reference
- Root cause: running on battery, not plugged in. Confirmed by a 15s rate-check recording after plugging in a spare charger — 14,991 samples in 15.00s = 999.4 Hz, matching desktop performance exactly
- Lesson: laptop must be on AC power for any real recording. Battery-saving CPU throttling is enough to silently cut the sustainable serial throughput by ~40%, which would have corrupted the Nyquist margin (effective ceiling ~311 Hz against ~450 Hz of real sEMG content) without any visible error
- Second real attempt (post-charger) failed for a different reason: had someone else press Enter to start the recording so both hands were free for the weight. Terminal likely wasn't focused when they pressed it — nothing saved, no new CSV, and no way to confirm afterward whether it ran at all
- Lesson: don't hand off the start step. The protocol depends on being able to see the terminal confirm it's running; a second person without context can't verify that. Next attempt: start the recording myself, accept ~2s of setup noise in the baseline rather than risk an unverified run
- Out of fresh electrodes after two attempts — ordering more before the next session
- Next session: same protocol, laptop on AC power from the start, same 35 lb / same angle, start the recording solo

## 2026-09-08
- Verified the micros() scheduling from last session: intervals were exactly 1000 µs with zero standard deviation. Timing logic confirmed correct
- But only 820 samples arrived in a 15 s window instead of ~15,000. Deltas were uniformly 1000 µs with no gaps, meaning the samples were contiguous — the capture stopped early rather than dropping samples throughout
- Instrumented log_serial.py with elapsed-time and line-count printouts. Result: elapsed 15.2 s, 820 lines. The loop ran its full duration but data stopped arriving after ~0.8 s. Without this, "820 rows" was ambiguous between two unrelated failure modes
- Controlled test: dropped INTERVAL_US to 2000 (500 Hz) and got 7,757 lines over 15 s — a clean sustained 500 Hz. This isolated the fault as rate-dependent throughput, not a broken connection, bad sketch, or hardware fault
- Two bottlenecks identified, both in the 1 ms per-sample budget:
  - Arduino side: converting a 7–8 digit micros() timestamp to ASCII on every sample. Removed timestamps entirely — justified because the interval was already proven constant, so sample time is reconstructable from row index at a known fixed rate
  - Python side: pyserial's readline() scans byte-by-byte for a newline, and doing that plus a csv.writer call 1000×/second exceeded what the receive loop could sustain. Rewrote to read ser.in_waiting bytes in bulk into a bytearray during capture, then split and filter after the clock stops
- Added ser.reset_input_buffer() after the 2 s startup sleep so data accumulated during board reset isn't counted
- Final result: 14,994 samples in 15.001 s = 999.5 Hz sustained. Nyquist ceiling now 500 Hz, above the ~450 Hz upper bound of sEMG content
- Why this was worth a full session: with timestamps removed, the analysis assumes the sample rate. An actual rate of 750 Hz against an assumed 1000 Hz would inflate every computed frequency by ~33%, including median frequency. The error would be invisible in the output — plots would look fine and the numbers would be wrong
- Also lost time to an unsaved log_serial.py: the edited version sat in the VS Code buffer while Python kept running the old file from disk. Zero rows written, no error raised. Check the tab's unsaved-changes dot before blaming the logic
- Prepared for the first real trial: OUTPUT_FILE renamed per-recording to avoid overwriting, DURATION_SECONDS set to 90
- Next session: isometric preacher-bench hold to failure. Chose isometric over repeated curls — no movement means no motion artifact, and continuous activation means every analysis window has usable spectral content

## 2026-09-07
- Opened first Jupyter notebook (analysis/emg_pipeline.ipynb); loaded test_log.csv with pandas
- Hit KeyError on 'timestamp_ms' — log_serial.py's `"timestamp" not in line` filter was stripping the header row before writing, so pandas treated the first data row as column names. Worked around with `header=None, names=[...]`; fixed the script to write its own header row directly
- Plotted the full 15 s recording: six clean flex bursts, stable baseline between them, consistent amplitudes, no drift
- Realized the signal is RAW, not ENV — it swings symmetrically to ~11,000 and ~5,000 around a ~8,150 baseline. An envelope can only rise from rest. 8,192 is exactly half of 16,383, i.e. mid-supply bias, the signature of an AC-coupled bipolar signal. Confirmed the Link Shield switch was on RAW
- This retroactively corrects Saturday's read of the 5,884 sample as a dropout artifact — on a bipolar signal, sub-baseline values are just the negative half of the waveform. Not an artifact
- RAW is the required mode for this project: median frequency depends on the frequency content of the signal, and ENV destroys that by rectifying and smoothing before it ever reaches the ADC
- Identified a sampling rate problem: 500 Hz sampling gives a Nyquist ceiling of 250 Hz, but sEMG carries meaningful power to ~450 Hz. Content above 250 Hz aliases down and injects phantom low-frequency energy into the band median frequency is computed from. Not recoverable in post-processing — has to be prevented at acquisition
- Rewrote the sketch to sample at 1000 Hz using micros()-based scheduling instead of delay(). Used `lastSample += INTERVAL_US` rather than `= now` so loop overhead doesn't accumulate into timing drift
- Raised baud from 115200 to 500000. At ~1000 lines/s × ~13 chars/line, 115200 baud (~11,520 char/s) would have saturated, blocked on Serial.print, and silently throttled the sample rate below 1000 Hz
- Renamed timestamp_ms → timestamp_us across the sketch, log_serial.py, and notebook. A units mix-up here would throw median frequency off by 1000×
- Next session: verify consecutive timestamps differ by ~1000 µs, then record a full curls-to-fatigue set

## 2026-09-05
- Placed electrodes and captured first live EMG signal
- Corrected a placement misunderstanding: in the standard no-cable setup, all three pads snap onto the sensor board and the whole board sits on the muscle belly. The "REF on a bony prominence" guidance only applies when using the separate MyoWare Reference Cable, which I don't have
- Baseline at rest ~8,150; flex peaks 9,000–10,000; fast, clean return to baseline. Peak amplitude scaled with flex intensity, consistent with motor unit recruitment and firing rate increasing with force
- Investigated the noisy resting baseline systematically:
  - Ruled out physiological tremor — pattern unchanged with the arm fully supported and relaxed
  - Ruled out simple 60 Hz aliasing — pattern barely changed between delay(10) and delay(2), which a 5× sampling rate change should have shifted
  - Found noise *increased* with distance from the PC, suggesting the long USB cable is acting as an antenna for ambient EMI rather than the PC being the source. Mitigated by keeping the cable coiled and near grounded equipment; full removal deferred to the bandpass/notch stage in software
- Built the CSV logging path: Arduino prints `timestamp,value`; log_serial.py (pyserial) reads the port and writes to data/raw/test_log.csv
- Debugging along the way:
  - PermissionError 13 on COM3 — the port was held open. Closing the Serial Monitor/Plotter panels wasn't enough; the entire Arduino IDE had to be closed
  - SAM-BA upload failure at 76% of flash write — resolved on retry, likely a transient USB hiccup
  - First CSV came out as timestamps with trailing commas and no values — caused by a Serial.println where Serial.print belonged, splitting each row across two lines

## 2026-09-04
- Set up Arduino IDE + board support for Uno R4 WiFi; confirmed working with Blink sketch
- Installed Python (numpy, scipy, matplotlib, pandas, jupyter) after Citrix/MATLAB access proved impractical
- Built LED + resistor circuit on breadboard; initial wiring put resistor and ground in the same row, bypassing the LED entirely (parallel short instead of series path) — fixed by rebuilding as a proper series chain
- Wired photoresistor module to A0; hit "serial port busy" and "invalid serial port" upload errors caused by Serial Plotter holding the COM port open during upload — resolved by closing Plotter before uploading
- Got clean analog readings: ~3700 baseline, ~11000 when covered, at 14-bit resolution
- Observed persistent baseline noise (~hundreds of counts) even under constant light — likely 60 Hz mains flicker, directly motivating the notch filter in the processing pipeline
- Created the GitHub repo (emg-fatigue-monitor), cloned via GitHub Desktop, set up folder structure (firmware/, analysis/, data/raw, data/processed, docs/images) with .gitkeep placeholders since git doesn't track empty directories
- Assembled the MyoWare stack: Link Shield onto Muscle Sensor, Arduino Shield onto Uno R4, TRS cable into shield port A0
- Couldn't seat the Link Shield at first — the Muscle Sensor ships with a placeholder shield attached over the snap connectors that has to be removed first
- VIN and ENV LEDs were initially unlit; reseating the shield and TRS connections fixed it
- With no electrodes attached, readings pinned near 16,000 and swung wildly — expected behavior for a high-gain differential amplifier with floating inputs acting as antennas

## 2026-09-03
- Finalized hardware selection: MyoWare 2.0 Muscle Sensor, Link Shield, Arduino Shield, Uno R4 WiFi
- Chose R4 WiFi over R3 for 14-bit ADC resolution and future WiFi/dashboard option
- Sourced Kendall H124SG 24mm disposable EMG electrodes after initially finding incompatible TENS pads (wrong connector, wrong size) — learned MyoWare's snap connector matches standard ECG/EMG electrode format, not TENS