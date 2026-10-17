Chart.js is vendored from the official distribution so the trends page does not
depend on a third-party CDN at runtime.

- Library: Chart.js 4.5.1 UMD build
- Source: https://cdn.jsdelivr.net/npm/chart.js@4.5.1/dist/chart.umd.min.js
- License: `CHARTJS-LICENSE.md` (MIT)

The chart uses a linear x-axis with epoch-millisecond values and formats ticks
with the browser's `Intl.DateTimeFormat`, so no separate date adapter is needed.
