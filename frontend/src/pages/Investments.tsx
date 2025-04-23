import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { investmentService } from '../api/investmentService';
import { PortfolioItem, InvestmentRecommendation, PortfolioQuality } from '../types/investment';

const Investments: React.FC = () => {
  const [portfolio, setPortfolio] = useState<PortfolioItem[]>([]);
  const [recommendations, setRecommendations] = useState<InvestmentRecommendation[]>([]);
  const [portfolioQuality, setPortfolioQuality] = useState<PortfolioQuality | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [activeTab, setActiveTab] = useState('portfolio'); // 'portfolio', 'recommendations', 'quality'

  // Form state
  const [formData, setFormData] = useState<PortfolioItem>({
    symbol: '',
    shares: 0,
    purchase_price: 0
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError('');
      
      // Fetch portfolio data
      const portfolioData = await investmentService.getPortfolio();
      setPortfolio(portfolioData.items || []);
      
      // Fetch investment recommendations
      const recommendationsData = await investmentService.getRecommendations();
      setRecommendations(recommendationsData.recommendations || []);
      
      // Fetch portfolio quality assessment
      const qualityData = await investmentService.getPortfolioQuality();
      setPortfolioQuality(qualityData);
      
      setLoading(false);
    } catch (err) {
      console.error('Error fetching investment data:', err);
      setError('Failed to load investment data. Please try again.');
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'symbol' ? value.toUpperCase() : parseFloat(value)
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await investmentService.addToPortfolio(formData);
      fetchData(); // Refresh data
      setShowAddForm(false);
      setFormData({ symbol: '', shares: 0, purchase_price: 0 });
    } catch (err) {
      console.error('Error adding investment:', err);
      setError('Failed to add investment. Please try again.');
    }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to remove this investment from your portfolio?')) {
      try {
        await investmentService.removeFromPortfolio(id);
        setPortfolio(prev => prev.filter(item => item.id !== id));
      } catch (err) {
        console.error('Error removing investment:', err);
        setError('Failed to remove investment. Please try again.');
      }
    }
  };

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: { y: 0, opacity: 1 }
  };

  // Calculate portfolio value
  const calculatePortfolioValue = () => {
    return portfolio.reduce((total, item) => {
      return total + (item.shares * item.purchase_price);
    }, 0);
  };

  if (loading && portfolio.length === 0) {
    return (
      <div className="loading-container">
        <motion.div 
          className="loader"
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        />
        <p>Loading investment data...</p>
      </div>
    );
  }

  return (
    <div className="investments-page">
      <motion.div 
        className="investments-header"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1>Investment Portfolio</h1>
        <motion.button
          className="add-button"
          onClick={() => setShowAddForm(!showAddForm)}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          {showAddForm ? 'Cancel' : 'Add New Investment'}
        </motion.button>
      </motion.div>

      {error && (
        <motion.div 
          className="error-message"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          {error}
          <button onClick={() => setError('')}>Dismiss</button>
        </motion.div>
      )}

      <div className="tabs">
        <motion.button 
          className={`tab ${activeTab === 'portfolio' ? 'active' : ''}`}
          onClick={() => setActiveTab('portfolio')}
          whileHover={{ y: -2 }}
          whileTap={{ y: 0 }}
        >
          Portfolio
        </motion.button>
        <motion.button 
          className={`tab ${activeTab === 'recommendations' ? 'active' : ''}`}
          onClick={() => setActiveTab('recommendations')}
          whileHover={{ y: -2 }}
          whileTap={{ y: 0 }}
        >
          Recommendations
        </motion.button>
        <motion.button 
          className={`tab ${activeTab === 'quality' ? 'active' : ''}`}
          onClick={() => setActiveTab('quality')}
          whileHover={{ y: -2 }}
          whileTap={{ y: 0 }}
        >
          Portfolio Analysis
        </motion.button>
      </div>

      <AnimatePresence>
        {showAddForm && (
          <motion.div 
            className="investment-form-container"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            <form onSubmit={handleSubmit} className="investment-form">
              <div className="form-group">
                <label htmlFor="symbol">Stock Symbol</label>
                <input
                  type="text"
                  id="symbol"
                  name="symbol"
                  value={formData.symbol}
                  onChange={handleInputChange}
                  placeholder="e.g., AAPL"
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="shares">Number of Shares</label>
                <input
                  type="number"
                  step="0.01"
                  id="shares"
                  name="shares"
                  value={formData.shares}
                  onChange={handleInputChange}
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="purchase_price">Purchase Price per Share ($)</label>
                <input
                  type="number"
                  step="0.01"
                  id="purchase_price"
                  name="purchase_price"
                  value={formData.purchase_price}
                  onChange={handleInputChange}
                  required
                />
              </div>
              
              <motion.button 
                type="submit" 
                className="submit-button"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                Add to Portfolio
              </motion.button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      {activeTab === 'portfolio' && (
        <motion.div 
          key="portfolio-tab"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="tab-content"
        >
          {portfolio.length > 0 ? (
            <motion.div 
              className="portfolio-container"
              variants={containerVariants}
              initial="hidden"
              animate="visible"
            >
              <div className="portfolio-summary">
                <div className="summary-item">
                  <h3>Total Value</h3>
                  <p className="value">${calculatePortfolioValue().toFixed(2)}</p>
                </div>
                <div className="summary-item">
                  <h3>Holdings</h3>
                  <p className="value">{portfolio.length}</p>
                </div>
              </div>

              <div className="portfolio-list">
                <div className="portfolio-header">
                  <div className="portfolio-symbol">Symbol</div>
                  <div className="portfolio-shares">Shares</div>
                  <div className="portfolio-price">Purchase Price</div>
                  <div className="portfolio-value">Total Value</div>
                  <div className="portfolio-actions">Actions</div>
                </div>
                
                {portfolio.map(item => (
                  <motion.div 
                    key={item.id}
                    className="portfolio-item"
                    variants={itemVariants}
                    whileHover={{ scale: 1.01, boxShadow: '0 4px 8px rgba(0,0,0,0.1)' }}
                  >
                    <div className="portfolio-symbol">{item.symbol}</div>
                    <div className="portfolio-shares">{item.shares.toFixed(2)}</div>
                    <div className="portfolio-price">${item.purchase_price.toFixed(2)}</div>
                    <div className="portfolio-value">${(item.shares * item.purchase_price).toFixed(2)}</div>
                    <div className="portfolio-actions">
                      <motion.button
                        className="action-button delete"
                        onClick={() => handleDelete(item.id || '')}
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        disabled={!item.id}
                      >
                        Remove
                      </motion.button>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          ) : (
            <motion.div 
              className="no-investments"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
            >
              <p>Your portfolio is empty. Add your first investment to get started!</p>
            </motion.div>
          )}
        </motion.div>
      )}

      {activeTab === 'recommendations' && (
        <motion.div 
          key="recommendations-tab"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="tab-content"
        >
          {recommendations.length > 0 ? (
            <motion.div 
              className="recommendations-container"
              variants={containerVariants}
              initial="hidden"
              animate="visible"
            >
              <div className="recommendations-intro">
                <h3>Personalized Investment Recommendations</h3>
                <p>Based on your financial profile and current market conditions.</p>
              </div>

              <div className="recommendations-list">
                {recommendations.map((rec, index) => (
                  <motion.div 
                    key={index}
                    className="recommendation-item"
                    variants={itemVariants}
                    whileHover={{ scale: 1.02, boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }}
                  >
                    <div className="rec-header">
                      <h3>{rec.name} ({rec.symbol})</h3>
                      <span className={`rec-type ${rec.type.toLowerCase().replace(' ', '-')}`}>{rec.type}</span>
                    </div>
                    <div className="rec-details">
                      <div className="rec-price">
                        <span className="label">Current Price:</span> ${rec.price.toFixed(2)}
                      </div>
                      <div className="rec-potential">
                        <span className="label">Growth Potential:</span> {rec.growth_potential}
                      </div>
                      <div className="rec-risk">
                        <span className="label">Risk Level:</span>
                        <span className={`risk-level ${rec.risk_level.toLowerCase()}`}>{rec.risk_level}</span>
                      </div>
                    </div>
                    <div className="rec-reason">
                      <h4>Why We Recommend It:</h4>
                      <p>{rec.recommendation_reason}</p>
                    </div>
                    <motion.button
                      className="add-to-portfolio-button"
                      onClick={() => {
                        setFormData({
                          symbol: rec.symbol,
                          shares: 0,
                          purchase_price: rec.price
                        });
                        setShowAddForm(true);
                        setActiveTab('portfolio');
                      }}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      Add to Portfolio
                    </motion.button>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          ) : (
            <motion.div 
              className="no-recommendations"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
            >
              <p>No recommendations available. Check back later for personalized investment suggestions.</p>
            </motion.div>
          )}
        </motion.div>
      )}

      {activeTab === 'quality' && (
        <motion.div 
          key="quality-tab"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="tab-content"
        >
          {portfolioQuality ? (
            <motion.div 
              className="quality-assessment"
              variants={containerVariants}
              initial="hidden"
              animate="visible"
            >
              <motion.div className="quality-header" variants={itemVariants}>
                <h2>Portfolio Quality Assessment</h2>
                <div className="overall-rating">
                  <span>Overall Rating:</span>
                  <div className="rating-stars">
                    {[...Array(5)].map((_, i) => (
                      <span key={i} className={i < Math.round(portfolioQuality.overall_rating) ? 'star filled' : 'star'}>
                        ★
                      </span>
                    ))}
                  </div>
                  <span className="rating-text">{portfolioQuality.overall_rating.toFixed(1)}/5.0</span>
                </div>
              </motion.div>

              <motion.div className="quality-section" variants={itemVariants}>
                <h3>Portfolio Assessment</h3>
                <div className="assessment-details">
                  <div className="assessment-item">
                    <span className="label">Diversification:</span>
                    <span className="value">{portfolioQuality.portfolio_assessment.diversification}</span>
                  </div>
                  <div className="assessment-item">
                    <span className="label">Risk Level:</span>
                    <span className="value">{portfolioQuality.portfolio_assessment.risk_level}</span>
                  </div>
                  <div className="assessment-item">
                    <span className="label">Growth Potential:</span>
                    <span className="value">{portfolioQuality.portfolio_assessment.growth_potential}</span>
                  </div>
                  <div className="assessment-item">
                    <span className="label">Diversification Score:</span>
                    <div className="progress-bar">
                      <div 
                        className="progress" 
                        style={{ width: `${portfolioQuality.diversification_score * 100}%` }}
                      ></div>
                    </div>
                    <span className="value">{(portfolioQuality.diversification_score * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </motion.div>

              <motion.div className="quality-section" variants={itemVariants}>
                <h3>Improvement Opportunities</h3>
                <ul className="improvement-list">
                  {portfolioQuality.portfolio_assessment.improvement_opportunities.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              </motion.div>

              {Object.keys(portfolioQuality.holdings_analysis).length > 0 && (
                <motion.div className="quality-section" variants={itemVariants}>
                  <h3>Individual Holdings Analysis</h3>
                  <div className="holdings-analysis">
                    {Object.entries(portfolioQuality.holdings_analysis).map(([symbol, analysis], index) => (
                      <div key={index} className="holding-analysis-item">
                        <div className="holding-header">
                          <h4>{symbol}</h4>
                          <div className="rating-stars small">
                            {[...Array(5)].map((_, i) => (
                              <span key={i} className={i < Math.round(analysis.rating) ? 'star filled' : 'star'}>
                                ★
                              </span>
                            ))}
                          </div>
                        </div>
                        
                        <div className="holding-details">
                          <div className="strengths">
                            <h5>Strengths:</h5>
                            <ul>
                              {analysis.strengths.map((item, i) => (
                                <li key={i}>{item}</li>
                              ))}
                            </ul>
                          </div>
                          
                          <div className="risks">
                            <h5>Risks:</h5>
                            <ul>
                              {analysis.risks.map((item, i) => (
                                <li key={i}>{item}</li>
                              ))}
                            </ul>
                          </div>
                        </div>
                        
                        <div className="recommendation">
                          <strong>Recommendation:</strong> {analysis.recommendation}
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </motion.div>
          ) : (
            <motion.div 
              className="no-quality-data"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
            >
              <p>Portfolio quality assessment is not available. Add investments to your portfolio to receive a quality assessment.</p>
            </motion.div>
          )}
        </motion.div>
      )}
    </div>
  );
};

export default Investments;
