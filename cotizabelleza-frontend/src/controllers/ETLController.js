/**
 * ETL Controller - Frontend MVC
 * Controla las operaciones del pipeline ETL desde el frontend
 */
import mvcApi from '../services/mvcApi.js';

class ETLController {
  constructor() {
    this.data = {
      status: {
        scraper_files: {},
        processed_files: {},
        database_stats: {},
        last_updated: null
      },
      logs: [],
      operations: {
        scraping: false,
        processing: false,
        loading: false,
        syncing: false
      },
      results: {
        lastScraping: null,
        lastProcessing: null,
        lastSync: null
      },
      loading: false,
      error: null
    };
    this.subscribers = new Set();
  }

  /**
   * Suscribirse a cambios de estado
   */
  subscribe(callback) {
    this.subscribers.add(callback);
    return () => this.subscribers.delete(callback);
  }

  /**
   * Notificar cambios a suscriptores
   */
  notify() {
    this.subscribers.forEach(callback => callback(this.data));
  }

  /**
   * Actualizar estado
   */
  setState(newState) {
    this.data = { ...this.data, ...newState };
    this.notify();
  }

  /**
   * Obtener estado del ETL
   */
  async loadStatus() {
    this.setState({ loading: true, error: null });

    try {
      const status = await mvcApi.etl.getStatus();
      
      this.setState({
        status: {
          ...status,
          last_updated: new Date().toISOString()
        },
        loading: false
      });

      return status;

    } catch (error) {
      console.error('Error loading ETL status:', error);
      this.setState({
        error: 'Error cargando estado del ETL',
        loading: false
      });
      throw error;
    }
  }

  /**
   * Ejecutar pipeline ETL completo
   */
  async runFullPipeline(config = {}) {
    this.setState({
      operations: { ...this.data.operations, scraping: true, processing: true, loading: true },
      error: null
    });

    try {
      const result = await mvcApi.etl.runFullPipeline(config);

      this.addLog('info', 'Pipeline ETL completo iniciado', result);

      this.setState({
        operations: {
          scraping: false,
          processing: false,
          loading: false,
          syncing: false
        },
        results: {
          ...this.data.results,
          lastScraping: result.extract,
          lastProcessing: result.transform,
          lastSync: result.load
        }
      });

      // Refrescar estado después del pipeline
      setTimeout(() => this.loadStatus(), 1000);

      return result;

    } catch (error) {
      console.error('Error running full ETL pipeline:', error);
      this.setState({
        error: 'Error ejecutando pipeline ETL completo',
        operations: {
          scraping: false,
          processing: false,
          loading: false,
          syncing: false
        }
      });
      this.addLog('error', 'Error en pipeline ETL', { error: error.message });
      throw error;
    }
  }

  /**
   * Ejecutar solo scraper
   */
  async runScraper(tienda, categoria = null) {
    this.setState({
      operations: { ...this.data.operations, scraping: true },
      error: null
    });

    try {
      const result = await mvcApi.etl.runScraper(tienda, categoria);

      this.addLog('info', `Scraper ${tienda} ejecutado`, result);

      this.setState({
        operations: { ...this.data.operations, scraping: false },
        results: {
          ...this.data.results,
          lastScraping: result
        }
      });

      // Refrescar estado
      setTimeout(() => this.loadStatus(), 1000);

      return result;

    } catch (error) {
      console.error(`Error running scraper for ${tienda}:`, error);
      this.setState({
        error: `Error ejecutando scraper ${tienda}`,
        operations: { ...this.data.operations, scraping: false }
      });
      this.addLog('error', `Error scraper ${tienda}`, { error: error.message });
      throw error;
    }
  }

  /**
   * Ejecutar solo procesador
   */
  async runProcessor(config = {}) {
    this.setState({
      operations: { ...this.data.operations, processing: true },
      error: null
    });

    try {
      const result = await mvcApi.etl.runProcessor(config);

      this.addLog('info', 'Procesador ejecutado', result);

      this.setState({
        operations: { ...this.data.operations, processing: false },
        results: {
          ...this.data.results,
          lastProcessing: result
        }
      });

      // Refrescar estado
      setTimeout(() => this.loadStatus(), 1000);

      return result;

    } catch (error) {
      console.error('Error running processor:', error);
      this.setState({
        error: 'Error ejecutando procesador',
        operations: { ...this.data.operations, processing: false }
      });
      this.addLog('error', 'Error procesador', { error: error.message });
      throw error;
    }
  }

  /**
   * Sincronizar datos a la BD
   */
  async syncData() {
    this.setState({
      operations: { ...this.data.operations, syncing: true },
      error: null
    });

    try {
      const result = await mvcApi.etl.syncData();

      this.addLog('info', 'Sincronización completada', result);

      this.setState({
        operations: { ...this.data.operations, syncing: false },
        results: {
          ...this.data.results,
          lastSync: result
        }
      });

      // Refrescar estado
      setTimeout(() => this.loadStatus(), 1000);

      return result;

    } catch (error) {
      console.error('Error syncing data:', error);
      this.setState({
        error: 'Error sincronizando datos',
        operations: { ...this.data.operations, syncing: false }
      });
      this.addLog('error', 'Error sincronización', { error: error.message });
      throw error;
    }
  }

  /**
   * Agregar log
   */
  addLog(level, message, data = {}) {
    const logEntry = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      level,
      message,
      data
    };

    const logs = [logEntry, ...this.data.logs.slice(0, 99)]; // Mantener últimos 100 logs

    this.setState({ logs });
  }

  /**
   * Obtener estadísticas del estado actual
   */
  getStatusStats() {
    const { status } = this.data;
    
    const scraperFiles = Object.values(status.scraper_files || {});
    const processedFiles = Object.values(status.processed_files || {});
    
    return {
      scraperFiles: {
        total: scraperFiles.length,
        existing: scraperFiles.filter(f => f.exists).length,
        totalSize: scraperFiles.reduce((sum, f) => sum + (f.size || 0), 0)
      },
      processedFiles: {
        total: processedFiles.length,
        existing: processedFiles.filter(f => f.exists).length,
        totalSize: processedFiles.reduce((sum, f) => sum + (f.size || 0), 0)
      },
      database: status.database_stats || {},
      lastUpdate: status.last_updated
    };
  }

  /**
   * Verificar si hay operaciones en curso
   */
  isOperating() {
    const { operations } = this.data;
    return Object.values(operations).some(op => op === true);
  }

  /**
   * Obtener logs filtrados
   */
  getLogsByLevel(level) {
    return this.data.logs.filter(log => log.level === level);
  }

  /**
   * Obtener logs recientes
   */
  getRecentLogs(limit = 10) {
    return this.data.logs.slice(0, limit);
  }

  /**
   * Limpiar logs
   */
  clearLogs() {
    this.setState({ logs: [] });
  }

  /**
   * Obtener estado de archivos específicos
   */
  getFileStatus(fileName) {
    const { status } = this.data;
    
    // Buscar en scraper files
    for (const [path, fileInfo] of Object.entries(status.scraper_files || {})) {
      if (path.includes(fileName)) {
        return { ...fileInfo, path, type: 'scraper' };
      }
    }
    
    // Buscar en processed files
    for (const [path, fileInfo] of Object.entries(status.processed_files || {})) {
      if (path.includes(fileName)) {
        return { ...fileInfo, path, type: 'processed' };
      }
    }
    
    return null;
  }

  /**
   * Obtener resumen de salud del ETL
   */
  getHealthSummary() {
    const stats = this.getStatusStats();
    const isOperating = this.isOperating();
    const hasError = !!this.data.error;
    
    return {
      status: hasError ? 'error' : isOperating ? 'running' : 'idle',
      dataFreshness: stats.lastUpdate ? 
        Date.now() - new Date(stats.lastUpdate).getTime() : null,
      filesStatus: {
        scraper: `${stats.scraperFiles.existing}/${stats.scraperFiles.total}`,
        processed: `${stats.processedFiles.existing}/${stats.processedFiles.total}`
      },
      databaseStatus: stats.database,
      operations: this.data.operations,
      lastError: this.data.error
    };
  }

  /**
   * Refrescar estado
   */
  async refresh() {
    return this.loadStatus();
  }

  /**
   * Limpiar estado
   */
  clear() {
    this.setState({
      status: {
        scraper_files: {},
        processed_files: {},
        database_stats: {},
        last_updated: null
      },
      logs: [],
      operations: {
        scraping: false,
        processing: false,
        loading: false,
        syncing: false
      },
      results: {
        lastScraping: null,
        lastProcessing: null,
        lastSync: null
      },
      loading: false,
      error: null
    });
  }
}

// Instancia singleton para el controlador
const etlController = new ETLController();

export default etlController;
