# JDemetra+ Visualization Service

Microservice for generating charts and visualizations from time series data and analysis results.

## Features

- Time series plots with multiple series support
- Seasonal adjustment decomposition plots
- Spectral analysis plots
- Diagnostic plots (ACF, PACF, residuals)
- Forecast visualization with confidence intervals
- Multiple output formats (PNG, SVG, PDF, interactive HTML)
- Plot customization and theming
- Batch plot generation

## Installation

```bash
pip install -e .
```

## Running the Service

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8008 --reload
```

## Docker

```bash
docker build -t jdemetra-viz-service .
docker run -p 8008:8008 jdemetra-viz-service
```

## API Endpoints

- `POST /api/v1/viz/timeseries` - Plot time series data
- `POST /api/v1/viz/decomposition` - Plot seasonal adjustment decomposition
- `POST /api/v1/viz/spectrum` - Plot spectral analysis
- `POST /api/v1/viz/diagnostics` - Generate diagnostic plots
- `POST /api/v1/viz/forecast` - Plot forecasts with confidence intervals
- `POST /api/v1/viz/comparison` - Compare multiple series or models
- `POST /api/v1/viz/batch` - Generate multiple plots in batch
- `GET /api/v1/viz/themes` - List available plot themes
- `GET /api/v1/viz/download/{plot_id}` - Download generated plot

## Plot Types

### Time Series Plot
Basic line plot with options for:
- Multiple series
- Markers and annotations
- Custom date formatting
- Grid and styling options

### Decomposition Plot
Multi-panel plot showing:
- Original series
- Trend component
- Seasonal component
- Irregular component

### Spectral Analysis
- Periodogram
- Spectral density
- Frequency identification

### Diagnostic Plots
- ACF/PACF plots
- Residual plots
- Q-Q plots
- Histogram with normality test

### Forecast Plot
- Historical data
- Forecast values
- Confidence intervals
- Out-of-sample comparison

## Output Formats

- **PNG**: Raster format for web/documents
- **SVG**: Vector format for scalable graphics
- **PDF**: High-quality document format
- **HTML**: Interactive plots with Plotly

## Configuration

Environment variables:
- `VIZ_SERVICE_PORT`: Service port (default: 8008)
- `MAX_SERIES_LENGTH`: Maximum time series length (default: 10000)
- `PLOT_CACHE_TTL`: Plot cache TTL in seconds (default: 3600)
- `DEFAULT_DPI`: Default plot DPI (default: 100)
- `MAX_PLOT_SIZE`: Maximum plot dimensions (default: 2000)