const express = require('express');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 8080;
const LOG_FILE = '/var/log/app/app.log';

// Ensure log directory exists
const logDir = path.dirname(LOG_FILE);
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir, { recursive: true });
}

// Simple logger
function log(level, message) {
  const timestamp = new Date().toISOString();
  const entry = `[${timestamp}] [${level}] ${message}\n`;
  console.log(entry.trim());
  fs.appendFileSync(LOG_FILE, entry);
}

// Middleware
app.use(express.json());

// Request logger middleware
app.use((req, res, next) => {
  log('INFO', `${req.method} ${req.url} - ${req.ip}`);
  next();
});

// ─── Routes ───────────────────────────────────────────────

// Health check endpoint
app.get('/health', (req, res) => {
  const health = {
    status: 'UP',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    version: '1.0.0',
    environment: process.env.NODE_ENV || 'development'
  };
  log('INFO', 'Health check passed');
  res.status(200).json(health);
});

// Home endpoint
app.get('/', (req, res) => {
  res.status(200).json({
    message: '🚀 Smart Self-Healing DevOps Platform is Running!',
    version: '1.0.0',
    timestamp: new Date().toISOString()
  });
});

// Simulate error endpoint (for testing AI log analyzer)
app.get('/simulate-error', (req, res) => {
  log('ERROR', 'Simulated application error: OutOfMemoryError - Java heap space');
  log('ERROR', 'at com.app.service.DataProcessor.process(DataProcessor.java:45)');
  log('ERROR', 'Database connection pool exhausted after 30s timeout');
  res.status(500).json({ error: 'Simulated failure for testing' });
});

// Logs endpoint (returns recent logs)
app.get('/logs', (req, res) => {
  try {
    if (fs.existsSync(LOG_FILE)) {
      const logs = fs.readFileSync(LOG_FILE, 'utf8').split('\n').slice(-50);
      res.status(200).json({ logs });
    } else {
      res.status(200).json({ logs: [] });
    }
  } catch (err) {
    res.status(500).json({ error: 'Could not read logs' });
  }
});

// Metrics endpoint
app.get('/metrics', (req, res) => {
  const metrics = {
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    cpu: process.cpuUsage(),
    timestamp: new Date().toISOString()
  };
  res.status(200).json(metrics);
});

// 404 handler
app.use((req, res) => {
  log('WARN', `404 Not Found: ${req.url}`);
  res.status(404).json({ error: 'Route not found' });
});

// Error handler
app.use((err, req, res, next) => {
  log('ERROR', `Unhandled error: ${err.message}`);
  res.status(500).json({ error: 'Internal Server Error' });
});

// ─── Start Server ──────────────────────────────────────────
app.listen(PORT, () => {
  log('INFO', `✅ Server started on port ${PORT}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  log('INFO', 'SIGTERM received. Shutting down gracefully...');
  process.exit(0);
});

module.exports = app;
