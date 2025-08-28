import axios from 'axios';

// Configurar axios para usar JSON por defecto
axios.defaults.headers.common['Content-Type'] = 'application/json';

export default axios;
