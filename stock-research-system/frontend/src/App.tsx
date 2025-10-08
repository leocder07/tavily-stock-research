import React from 'react';
import { Provider } from 'react-redux';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import './styles/clerk-overrides.css';
import ErrorBoundary from './components/ErrorBoundary';
import { store } from './store';
import AppContent from './AppContent';
import AnalysisPage from './components/AnalysisPage';

const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <Provider store={store}>
        <Router>
          <Routes>
            <Route path="/" element={<AppContent />} />
            <Route path="/analyze/:analysisId" element={<AnalysisPage />} />
          </Routes>
        </Router>
      </Provider>
    </ErrorBoundary>
  );
};

export default App;