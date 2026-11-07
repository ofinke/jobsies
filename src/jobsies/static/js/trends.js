(() => {
  "use strict";

  const dateFormatOptions = {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  };

  function formatTimestamp(timestamp, timezone) {
    return new Intl.DateTimeFormat(undefined, {
      ...dateFormatOptions,
      timeZone: timezone,
    }).format(new Date(timestamp));
  }

  function getChartCanvases(root) {
    const canvases = root.querySelectorAll("canvas[data-trend-chart]");
    return [...canvases];
  }

  function destroyCharts(root) {
    getChartCanvases(root).forEach((canvas) => {
      Chart.getChart(canvas)?.destroy();
    });
  }

  function renderChart(canvas) {
    if (Chart.getChart(canvas)) {
      return;
    }

    const title = canvas.dataset.title;
    const unit = canvas.dataset.unit;
    const timezone = canvas.dataset.timezone;
    const { timestamp, value } = JSON.parse(canvas.dataset.points);
    const points = timestamp
      .map((sampleTime, index) => ({
        x: Date.parse(sampleTime),
        y: typeof value[index] === "number" && Number.isFinite(value[index]) ? value[index] : null,
      }))
      .filter((point) => Number.isFinite(point.x));
    const styles = getComputedStyle(document.documentElement);
    const lineColor = styles.getPropertyValue("--secondary").trim();
    const textColor = styles.getPropertyValue("--text-subtle").trim();
    const gridColor = styles.getPropertyValue("--content-border-subtle").trim();

    new Chart(canvas, {
      type: "line",
      data: {
        datasets: [{
          label: title,
          data: points,
          borderColor: lineColor,
          backgroundColor: lineColor,
          borderWidth: 2,
          pointRadius: 3,
          pointHoverRadius: 5,
          tension: 0.2,
          spanGaps: false,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        parsing: false,
        interaction: {
          intersect: false,
          mode: "nearest",
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              title(items) {
                return items.length ? formatTimestamp(items[0].parsed.x, timezone) : "";
              },
              label(context) {
                const suffix = unit ? ` ${unit}` : "";
                return `${title}: ${context.parsed.y ?? "—"}${suffix}`;
              },
            },
          },
        },
        scales: {
          x: {
            type: "linear",
            title: {
              display: true,
              text: "Time",
              color: textColor,
            },
            ticks: {
              color: textColor,
              font: { size: 14 },
              maxTicksLimit: 6,
              callback(tick) {
                return formatTimestamp(tick, timezone);
              },
            },
            grid: { color: gridColor },
          },
          y: {
            title: {
              display: Boolean(unit),
              text: unit,
              color: textColor,
            },
            ticks: {
              color: textColor,
              font: { size: 14 },
            },
            grid: { color: gridColor },
          },
        },
      },
    });
  }

  function initializeCharts() {
    document.querySelectorAll("canvas[data-trend-chart]").forEach(renderChart);
  }

  document.addEventListener("htmx:beforeSwap", (event) => {
    if (event.detail.target?.id === "trends-list") {
      destroyCharts(event.detail.target);
    }
  });
  document.addEventListener("htmx:afterSwap", initializeCharts);
  document.addEventListener("DOMContentLoaded", initializeCharts);
  document.addEventListener("click", (event) => {
    if (event.target.closest("#theme-toggle")) {
      requestAnimationFrame(() => {
        destroyCharts(document);
        initializeCharts();
      });
    }
  });
})();
