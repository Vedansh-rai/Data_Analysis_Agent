import { useState, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import Plot from 'react-plotly.js';
import { Upload, FileText, BarChart2, Loader, AlertCircle, CheckCircle, ExternalLink, TrendingUp, Settings } from 'lucide-react';
import './App.css';

const API_URL = "http://localhost:8000";

const CHART_TYPES = [
  { value: 'bar', label: '📊 Bar Chart' },
  { value: 'line', label: '📈 Line Chart' },
  { value: 'scatter', label: '⚫ Scatter Plot' },
  { value: 'pie', label: '🥧 Pie Chart' },
  { value: 'histogram', label: '📉 Histogram' },
  { value: 'box', label: '📦 Box Plot' },
  { value: 'area', label: '🏔️ Area Chart' },
];

const AGGREGATIONS = [
  { value: 'sum', label: 'Sum' },
  { value: 'mean', label: 'Average' },
  { value: 'count', label: 'Count' },
  { value: 'min', label: 'Min' },
  { value: 'max', label: 'Max' },
];

function App() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [error, setError] = useState(null);
  const [tableauStatus, setTableauStatus] = useState(null);
  const [tableauMessage, setTableauMessage] = useState(null);
  const [activeTab, setActiveTab] = useState('report');
  
  // Chart Builder State
  const [columns, setColumns] = useState([]);
  const [xAxis, setXAxis] = useState('');
  const [yAxis, setYAxis] = useState('');
  const [chartType, setChartType] = useState('bar');
  const [colorBy, setColorBy] = useState('');
  const [aggregation, setAggregation] = useState('sum');
  const [customChart, setCustomChart] = useState(null);
  const [buildingChart, setBuildingChart] = useState(false);

  // Check Tableau on mount
  useEffect(() => {
    axios.get(`${API_URL}/tableau/check`)
      .then(res => setTableauStatus(res.data))
      .catch(() => setTableauStatus({ installed: false }));
  }, []);

  const handleFileUpload = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setLoading(true);
    setError(null);
    setReport(null);
    setDashboard(null);
    setCustomChart(null);
    setTableauMessage(null);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      // 1. Upload
      await axios.post(`${API_URL}/upload`, formData);
      
      // 2. Analyze
      const analysisRes = await axios.post(`${API_URL}/analyze?filename=${selectedFile.name}`);
      setReport(analysisRes.data);
      
      // Set columns for chart builder
      const cols = analysisRes.data.summary.column_names || [];
      setColumns(cols);
      if (cols.length >= 2) {
        setXAxis(cols[0]);
        setYAxis(cols[1]);
      }
      
      // 3. Generate Dashboard
      const dashboardRes = await axios.post(`${API_URL}/dashboard?filename=${selectedFile.name}`);
      setDashboard(dashboardRes.data);
      
    } catch (err) {
      setError(err.response?.data?.detail || "Analysis failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleOpenInTableau = async () => {
    if (!file) return;
    
    setTableauMessage({ type: 'loading', text: 'Opening in Tableau...' });
    
    try {
      const res = await axios.post(`${API_URL}/tableau/open?filename=${file.name}`);
      setTableauMessage({ type: 'success', text: res.data.message });
    } catch (err) {
      setTableauMessage({ 
        type: 'error', 
        text: err.response?.data?.detail || 'Failed to open Tableau' 
      });
    }
  };

  const handleBuildChart = async () => {
    if (!file || !xAxis || !yAxis) return;
    
    setBuildingChart(true);
    
    try {
      const params = new URLSearchParams({
        filename: file.name,
        x_axis: xAxis,
        y_axis: yAxis,
        chart_type: chartType,
        aggregation: aggregation
      });
      if (colorBy) params.append('color_by', colorBy);
      
      const res = await axios.post(`${API_URL}/chart/custom?${params.toString()}`);
      setCustomChart(res.data);
    } catch (err) {
      console.error('Chart build failed:', err);
    } finally {
      setBuildingChart(false);
    }
  };

  const renderChart = (chart, index) => {
    try {
      const plotData = JSON.parse(chart.data);
      return (
        <div key={index} className="chart-card">
          <h4>{chart.title}</h4>
          <Plot
            data={plotData.data}
            layout={{
              ...plotData.layout,
              autosize: true,
              margin: { t: 40, r: 20, b: 40, l: 50 },
            }}
            config={{ responsive: true, displayModeBar: true }}
            style={{ width: '100%', height: '350px' }}
          />
        </div>
      );
    } catch (e) {
      return <div key={index} className="chart-error">Failed to render chart</div>;
    }
  };

  const renderCustomChart = () => {
    if (!customChart) return null;
    try {
      const plotData = JSON.parse(customChart.data);
      return (
        <Plot
          data={plotData.data}
          layout={{
            ...plotData.layout,
            autosize: true,
            margin: { t: 50, r: 30, b: 50, l: 60 },
          }}
          config={{ responsive: true, displayModeBar: true }}
          style={{ width: '100%', height: '450px' }}
        />
      );
    } catch (e) {
      return <div className="chart-error">Failed to render chart</div>;
    }
  };

  return (
    <div className="app-container">
      <header className="header">
        <div className="brand">
          <BarChart2 size={28} />
          <h1>Data Analysis Agent</h1>
        </div>
        <p className="tagline">Upload any dataset. Get instant insights.</p>
        {tableauStatus?.installed && (
          <div className="tableau-status">
            ✅ Connected to {tableauStatus.name}
          </div>
        )}
      </header>

      <main className="main-content">
        {/* Upload Section */}
        <section className="upload-section">
          <label htmlFor="file-upload" className="upload-zone">
            <Upload size={32} />
            <span>{file ? file.name : "Drop CSV or Excel file here"}</span>
            <small>or click to browse</small>
          </label>
          <input 
            id="file-upload" 
            type="file" 
            onChange={handleFileUpload} 
            accept=".csv,.xlsx,.xls" 
            hidden 
          />
        </section>

        {/* Loading State */}
        {loading && (
          <div className="loading-state">
            <Loader className="spin" size={40} />
            <p>Analyzing your data & generating dashboard...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="error-state">
            <AlertCircle size={24} />
            <p>{error}</p>
          </div>
        )}

        {/* Tabs */}
        {report && (
          <div className="tabs">
            <button 
              className={`tab ${activeTab === 'report' ? 'active' : ''}`}
              onClick={() => setActiveTab('report')}
            >
              <FileText size={18} /> Report
            </button>
            <button 
              className={`tab ${activeTab === 'dashboard' ? 'active' : ''}`}
              onClick={() => setActiveTab('dashboard')}
            >
              <TrendingUp size={18} /> Auto Dashboard
            </button>
            <button 
              className={`tab ${activeTab === 'builder' ? 'active' : ''}`}
              onClick={() => setActiveTab('builder')}
            >
              <Settings size={18} /> Chart Builder
            </button>
          </div>
        )}

        {/* Report Tab */}
        {report && activeTab === 'report' && (
          <section className="report-section">
            <div className="report-header">
              <CheckCircle size={24} />
              <h2>Analysis Complete</h2>
            </div>

            {/* Quick Stats */}
            <div className="stats-grid">
              <div className="stat-card">
                <span className="stat-value">{report.summary.rows.toLocaleString()}</span>
                <span className="stat-label">Rows</span>
              </div>
              <div className="stat-card">
                <span className="stat-value">{report.summary.columns}</span>
                <span className="stat-label">Columns</span>
              </div>
              <div className="stat-card">
                <span className="stat-value">{report.summary.memory_mb} MB</span>
                <span className="stat-label">Memory</span>
              </div>
              <div className="stat-card">
                <span className="stat-value">{report.summary.duplicates}</span>
                <span className="stat-label">Duplicates</span>
              </div>
            </div>

            {/* Tableau Integration */}
            {tableauStatus?.installed && (
              <div className="tableau-section">
                <button className="tableau-btn" onClick={handleOpenInTableau} disabled={loading}>
                  <ExternalLink size={18} />
                  Open Cleaned Data in {tableauStatus.name || 'Tableau'}
                </button>
                {tableauMessage && (
                  <span className={`tableau-msg ${tableauMessage.type}`}>
                    {tableauMessage.text}
                  </span>
                )}
              </div>
            )}

            {/* Warnings */}
            {report.warnings.length > 0 && (
              <div className="warnings-box">
                <h3>⚠️ Warnings</h3>
                <ul>
                  {report.warnings.map((w, i) => <li key={i}>{w}</li>)}
                </ul>
              </div>
            )}

            {/* Insights */}
            <div className="insights-box">
              <h3>💡 Key Insights</h3>
              <ul>
                {report.insights.map((insight, i) => <li key={i}>{insight}</li>)}
              </ul>
            </div>

            {/* Full Report */}
            <div className="full-report">
              <h3>📄 Full Report</h3>
              <div className="markdown-body">
                <ReactMarkdown>{report.report_markdown}</ReactMarkdown>
              </div>
            </div>
          </section>
        )}

        {/* Dashboard Tab */}
        {dashboard && activeTab === 'dashboard' && (
          <section className="dashboard-section">
            <div className="dashboard-header">
              <TrendingUp size={24} />
              <h2>Auto-Generated Dashboard</h2>
              <span className="chart-count">{dashboard.chart_count} charts</span>
            </div>
            
            <div className="charts-grid">
              {dashboard.charts.map((chart, index) => renderChart(chart, index))}
            </div>
          </section>
        )}

        {/* Chart Builder Tab */}
        {report && activeTab === 'builder' && (
          <section className="builder-section">
            <div className="builder-header">
              <Settings size={24} />
              <h2>Custom Chart Builder</h2>
              <span className="builder-hint">Select columns like Tableau</span>
            </div>

            <div className="builder-controls">
              <div className="control-row">
                <div className="control-group">
                  <label>X Axis (Dimension)</label>
                  <select value={xAxis} onChange={(e) => setXAxis(e.target.value)}>
                    {columns.map(col => (
                      <option key={col} value={col}>{col}</option>
                    ))}
                  </select>
                </div>

                <div className="control-group">
                  <label>Y Axis (Measure)</label>
                  <select value={yAxis} onChange={(e) => setYAxis(e.target.value)}>
                    {columns.map(col => (
                      <option key={col} value={col}>{col}</option>
                    ))}
                  </select>
                </div>

                <div className="control-group">
                  <label>Chart Type</label>
                  <select value={chartType} onChange={(e) => setChartType(e.target.value)}>
                    {CHART_TYPES.map(ct => (
                      <option key={ct.value} value={ct.value}>{ct.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="control-row">
                <div className="control-group">
                  <label>Color By (Optional)</label>
                  <select value={colorBy} onChange={(e) => setColorBy(e.target.value)}>
                    <option value="">None</option>
                    {columns.map(col => (
                      <option key={col} value={col}>{col}</option>
                    ))}
                  </select>
                </div>

                <div className="control-group">
                  <label>Aggregation</label>
                  <select value={aggregation} onChange={(e) => setAggregation(e.target.value)}>
                    {AGGREGATIONS.map(agg => (
                      <option key={agg.value} value={agg.value}>{agg.label}</option>
                    ))}
                  </select>
                </div>

                <div className="control-group">
                  <label>&nbsp;</label>
                  <button 
                    className="build-chart-btn" 
                    onClick={handleBuildChart}
                    disabled={buildingChart}
                  >
                    {buildingChart ? <Loader className="spin" size={16} /> : '🔨'} Build Chart
                  </button>
                </div>
              </div>
            </div>

            <div className="custom-chart-area">
              {customChart ? (
                renderCustomChart()
              ) : (
                <div className="chart-placeholder">
                  <BarChart2 size={48} />
                  <p>Select columns and click "Build Chart" to visualize</p>
                </div>
              )}
            </div>
          </section>
        )}
      </main>

      <footer className="footer">
        <p>Data Analysis Agent • Powered by Python & React</p>
      </footer>
    </div>
  );
}

export default App;
