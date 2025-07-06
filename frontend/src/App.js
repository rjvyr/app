import React, { useState, useEffect, useContext, createContext } from 'react';
import PlansPage from './PlansPage';

// Auth Context
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);
  
  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    if (token) {
      validateToken();
    } else {
      setLoading(false);
    }
  }, [token]);

  const validateToken = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        localStorage.removeItem('token');
        setToken(null);
      }
    } catch (error) {
      console.error('Token validation error:', error);
      localStorage.removeItem('token');
      setToken(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await fetch(`${backendUrl}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      if (response.ok) {
        const data = await response.json();
        setToken(data.access_token);
        setUser(data.user);
        localStorage.setItem('token', data.access_token);
        return { success: true };
      } else {
        const error = await response.json();
        return { success: false, error: error.detail };
      }
    } catch (error) {
      return { success: false, error: 'Network error' };
    }
  };

  const register = async (userData) => {
    try {
      const response = await fetch(`${backendUrl}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData)
      });

      if (response.ok) {
        return { success: true };
      } else {
        const error = await response.json();
        return { success: false, error: error.detail };
      }
    } catch (error) {
      return { success: false, error: 'Network error' };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading, backendUrl, token }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Login Form Component
const LoginForm = () => {
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = await login(formData.email, formData.password);
    if (!result.success) {
      setError(result.error);
    }
    setLoading(false);
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">futureseo</h1>
          <p className="text-gray-600 mt-2">Sign in to your AI Brand Visibility Scanner</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
};

// Register Form Component
const RegisterForm = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
    company: '',
    website: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const { register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = await register(formData);
    if (result.success) {
      setSuccess(true);
    } else {
      setError(result.error);
    }
    setLoading(false);
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-100 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8 text-center">
          <div className="text-green-600 text-6xl mb-4">✓</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Account Created!</h2>
          <p className="text-gray-600 mb-6">Please check your email to verify your account.</p>
          <p className="text-sm text-gray-500">Your 7-day free trial has started with 50 free scans!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">futureseo</h1>
          <p className="text-gray-600 mt-2">Start your 7-day free trial</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
              <input
                type="text"
                name="full_name"
                value={formData.full_name}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Company</label>
              <input
                type="text"
                name="company"
                value={formData.company}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Website (Optional)</label>
            <input
              type="url"
              name="website"
              value={formData.website}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="https://yourwebsite.com"
            />
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Creating Account...' : 'Start Free Trial'}
          </button>
        </form>
        
        <div className="mt-6 text-center">
          <p className="text-gray-600">
            Already have an account?{' '}
            <button className="text-blue-600 hover:underline font-medium">
              Sign in
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

// Main Dashboard Component
const Dashboard = () => {
  const { user, logout, backendUrl, token, setUser } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [dashboardData, setDashboardData] = useState(null);
  const [competitorData, setCompetitorData] = useState(null);
  const [queriesData, setQueriesData] = useState(null);
  const [recommendationsData, setRecommendationsData] = useState(null);
  const [brands, setBrands] = useState([]);
  const [selectedBrandId, setSelectedBrandId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scanLoading, setScanLoading] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    fetchAllRealData();
  }, []);

  useEffect(() => {
    // Don't auto-select first brand, let user choose
    // This allows "All Brands" to be the default view
  }, [brands]);

  // Refetch data when brand selection changes
  useEffect(() => {
    if (selectedBrandId) {
      fetchBrandSpecificData(selectedBrandId);
    } else if (selectedBrandId === '') {
      // When "All Brands" is selected, fetch all data
      fetchAllRealData();
    }
  }, [selectedBrandId]);

  const fetchAllRealData = async () => {
    try {
      const headers = { 'Authorization': `Bearer ${token}` };
      
      const [dashResponse, compResponse, queryResponse, recResponse, brandsResponse] = await Promise.all([
        fetch(`${backendUrl}/api/dashboard/real`, { headers }),
        fetch(`${backendUrl}/api/competitors/real`, { headers }),
        fetch(`${backendUrl}/api/queries/real`, { headers }),
        fetch(`${backendUrl}/api/recommendations/real`, { headers }),
        fetch(`${backendUrl}/api/brands`, { headers })
      ]);

      const [dashData, compData, queryData, recData, brandsData] = await Promise.all([
        dashResponse.json(),
        compResponse.json(),
        queryResponse.json(),
        recResponse.json(),
        brandsResponse.json()
      ]);

      setDashboardData(dashData);
      setCompetitorData(compData);
      setQueriesData(queryData);
      setRecommendationsData(recData);
      setBrands(brandsData.brands);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchBrandSpecificData = async (brandId) => {
    try {
      setLoading(true);
      const headers = { 'Authorization': `Bearer ${token}` };
      
      // Add brand_id parameter to API calls for brand-specific data
      const [dashResponse, compResponse, queryResponse, recResponse] = await Promise.all([
        fetch(`${backendUrl}/api/dashboard/real?brand_id=${brandId}`, { headers }),
        fetch(`${backendUrl}/api/competitors/real?brand_id=${brandId}`, { headers }),
        fetch(`${backendUrl}/api/queries/real?brand_id=${brandId}`, { headers }),
        fetch(`${backendUrl}/api/recommendations/real?brand_id=${brandId}`, { headers })
      ]);

      const [dashData, compData, queryData, recData] = await Promise.all([
        dashResponse.json(),
        compResponse.json(),
        queryResponse.json(),
        recResponse.json()
      ]);

      setDashboardData(dashData);
      setCompetitorData(compData);
      setQueriesData(queryData);
      setRecommendationsData(recData);
    } catch (error) {
      console.error('Error fetching brand-specific data:', error);
    } finally {
      setLoading(false);
    }
  };

  const runScan = async (brandId, scanType) => {
    setScanLoading(true);
    try {
      const response = await fetch(`${backendUrl}/api/scans`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ brand_id: brandId, scan_type: scanType })
      });

      if (response.ok) {
        const scanResult = await response.json();
        
        // Refresh all data including user info to update scan usage
        await Promise.all([
          fetchAllRealData(),
          refreshUserData() // This will update the scan usage bar
        ]);
        
        alert(`${scanType} scan completed successfully! Used ${scanResult.scans_used} scans.`);
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      alert('Network error occurred');
    } finally {
      setScanLoading(false);
    }
  };

  const refreshUserData = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const updatedUser = await response.json();
        // Update user data in AuthContext
        setUser(updatedUser);
      }
    } catch (error) {
      console.error('Error refreshing user data:', error);
    }
  };

  const renderEnterpriseWelcome = () => (
    <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-xl p-6 mb-6">
      <div className="flex items-center space-x-4">
        <div className="text-4xl">🚀</div>
        <div>
          <h3 className="text-lg font-bold text-gray-900">Welcome to Enterprise!</h3>
          <p className="text-gray-600">
            You now have full access: <strong>1,500 scans/month</strong> • <strong>10 brands</strong> • <strong>All features</strong> • Ready for <strong>futureseo.io</strong>
          </p>
        </div>
      </div>
    </div>
  );

  const renderBrandSelector = () => {
    if (brands.length <= 1) return null;

    return (
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Brand to View Data ({brands.length} brands available)
        </label>
        <select
          value={selectedBrandId || ''}
          onChange={(e) => {
            const newBrandId = e.target.value;
            setSelectedBrandId(newBrandId);
            // Show loading state
            setLoading(true);
          }}
          className="w-full max-w-xs px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
        >
          <option value="">All Brands (Combined Data)</option>
          {brands.map((brand) => (
            <option key={brand._id} value={brand._id}>
              {brand.name} ({brand.industry})
            </option>
          ))}
        </select>
        {selectedBrandId && (
          <div className="mt-2 text-sm text-blue-600">
            🎯 Showing data for: <strong>{brands.find(b => b._id === selectedBrandId)?.name}</strong>
          </div>
        )}
        {!selectedBrandId && (
          <div className="mt-2 text-sm text-gray-600">
            📊 Showing combined data for all brands
          </div>
        )}
      </div>
    );
  };

  const renderOverview = () => (
    <div className="space-y-6">
      {renderEnterpriseWelcome()}
      {renderBrandSelector()}
      
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">AI Visibility Score</h1>
          <p className="text-gray-600 mt-1">Real-time brand visibility tracking</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <div className="text-sm text-gray-500">Enterprise Plan</div>
            <div className="text-xs text-gray-400">Live AI Analysis</div>
          </div>
          <div className="w-3 h-3 bg-green-500 rounded-full"></div>
        </div>
      </div>

      {/* Main Score Card using REAL data */}
      <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100">
        <div className="text-center">
          <div className="text-6xl font-bold text-blue-600 mb-2">
            {dashboardData?.overall_visibility ? Math.round(dashboardData.overall_visibility) : 0}%
          </div>
          <div className="text-lg text-gray-600 mb-4">
            {dashboardData?.overall_visibility > 70 ? 'Excellent' : 
             dashboardData?.overall_visibility > 50 ? 'Good' : 
             dashboardData?.overall_visibility > 30 ? 'Fair' : 'Run scans to see your score'}
          </div>
          <div className="flex items-center justify-center space-x-4 text-sm text-gray-500">
            <span>{dashboardData?.total_mentions || 0}/{dashboardData?.total_queries || 0} queries mention your brand</span>
            <span>•</span>
            <span>{dashboardData?.brands_count || 0} brands tracked</span>
          </div>
        </div>
      </div>

      {/* Platform Breakdown using REAL data */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">AI Platform Breakdown</h3>
        <div className="space-y-4">
          {/* ChatGPT */}
          <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <span className="text-blue-600 font-bold">🤖</span>
              </div>
              <div>
                <div className="font-semibold text-gray-900">ChatGPT (GPT-4o-mini)</div>
                <div className="text-sm text-gray-500">
                  {dashboardData?.platform_breakdown?.ChatGPT?.mentions || 0} mentions out of {dashboardData?.platform_breakdown?.ChatGPT?.total_questions || 0} queries
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-blue-600">
                {dashboardData?.platform_breakdown?.ChatGPT ? Math.round(dashboardData.platform_breakdown.ChatGPT.visibility_rate) : 0}%
              </div>
              <div className="text-sm text-gray-500">Real API data</div>
            </div>
          </div>

          {/* Gemini */}
          <div className="flex items-center justify-between p-4 bg-purple-50 rounded-lg">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <span className="text-purple-600 font-bold">💎</span>
              </div>
              <div>
                <div className="font-semibold text-gray-900">Google Gemini</div>
                <div className="text-sm text-gray-500">Coming soon - Integration in progress</div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-purple-600">-</div>
              <div className="text-sm text-gray-500">Pro/Enterprise</div>
            </div>
          </div>

          {/* AI Overview */}
          <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                <span className="text-green-600 font-bold">🔍</span>
              </div>
              <div>
                <div className="font-semibold text-gray-900">Google AI Overview</div>
                <div className="text-sm text-gray-500">Coming soon - Integration in progress</div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-green-600">-</div>
              <div className="text-sm text-gray-500">Pro/Enterprise</div>
            </div>
          </div>
          
          {(!dashboardData?.platform_breakdown || Object.keys(dashboardData.platform_breakdown).length === 0) && (
            <div className="text-center py-8 text-gray-500">
              <div className="text-4xl mb-4">📊</div>
              <p className="text-lg font-medium mb-2">No scan data yet</p>
              <p className="text-sm">Run your first scan to see real AI visibility data!</p>
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <button
            onClick={() => brands.length > 0 && runScan(selectedBrandId || brands[0]._id, 'quick')}
            disabled={scanLoading || brands.length === 0}
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors disabled:opacity-50"
          >
            <div className="text-center">
              <div className="text-2xl mb-2">⚡</div>
              <div className="font-medium text-gray-900">Quick Scan</div>
              <div className="text-sm text-gray-500">5 real AI queries</div>
            </div>
          </button>

          <button
            onClick={() => brands.length > 0 && runScan(selectedBrandId || brands[0]._id, 'standard')}
            disabled={scanLoading || brands.length === 0}
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-green-500 hover:bg-green-50 transition-colors disabled:opacity-50"
          >
            <div className="text-center">
              <div className="text-2xl mb-2">🎯</div>
              <div className="font-medium text-gray-900">Standard Scan</div>
              <div className="text-sm text-gray-500">25 real AI queries</div>
            </div>
          </button>

          <button
            onClick={() => brands.length > 0 && runScan(selectedBrandId || brands[0]._id, 'deep')}
            disabled={scanLoading || brands.length === 0}
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-colors disabled:opacity-50"
          >
            <div className="text-center">
              <div className="text-2xl mb-2">🚀</div>
              <div className="font-medium text-gray-900">Deep Scan</div>
              <div className="text-sm text-gray-500">50 real AI queries</div>
            </div>
          </button>

          <button
            onClick={() => brands.length > 0 && runScan(selectedBrandId || brands[0]._id, 'competitor')}
            disabled={scanLoading || brands.length === 0}
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-orange-500 hover:bg-orange-50 transition-colors disabled:opacity-50"
          >
            <div className="text-center">
              <div className="text-2xl mb-2">🏆</div>
              <div className="font-medium text-gray-900">Competitor Scan</div>
              <div className="text-sm text-gray-500">10 competitor queries</div>
            </div>
          </button>
        </div>
        
        {brands.length === 0 && (
          <div className="mt-4 text-center text-gray-500">
            <p>Add a brand first to start scanning!</p>
            <button
              onClick={() => setActiveTab('add-brand')}
              className="mt-2 text-blue-600 hover:underline"
            >
              Add Your First Brand →
            </button>
          </div>
        )}
      </div>

      {/* Usage Stats */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Scan Usage</h3>
          <span className="text-sm text-gray-500">Enterprise Plan</span>
        </div>
        <div className="space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Scans Used</span>
            <span className="font-medium">{user?.scans_used || 0}/{user?.scans_limit || 1500}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full" 
              style={{width: `${((user?.scans_used || 0) / (user?.scans_limit || 1500)) * 100}%`}}
            ></div>
          </div>
          <div className="text-xs text-gray-500">
            {(user?.scans_limit || 1500) - (user?.scans_used || 0)} scans remaining
          </div>
        </div>
      </div>
    </div>
  );

  const renderCompetitors = () => (
    <div className="space-y-6">
      {renderEnterpriseWelcome()}
      {renderBrandSelector()}
      
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Competitor Analysis</h2>
        <div className="text-sm text-gray-500">Real AI data • Live results</div>
      </div>

      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Brand Rankings</h3>
        <div className="space-y-4">
          {competitorData?.competitors?.map((competitor, index) => (
            <div key={competitor.name} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-4">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold ${
                  competitor.is_user_brand ? 'bg-blue-600' : 'bg-gray-600'
                }`}>
                  {competitor.rank}
                </div>
                <div>
                  <div className="font-semibold text-gray-900">
                    {competitor.name} {competitor.is_user_brand && '(Your Brand)'}
                  </div>
                  <div className="text-sm text-gray-500">
                    {competitor.mentions} mentions in {competitor.total_queries} queries
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-xl font-bold text-gray-900">{competitor.visibility_score.toFixed(1)}%</div>
                <div className="text-sm text-gray-500">Visibility</div>
              </div>
            </div>
          ))}
          
          {(!competitorData?.competitors || competitorData.competitors.length === 0) && (
            <div className="text-center py-8 text-gray-500">
              <div className="text-4xl mb-4">🏆</div>
              <p className="text-lg font-medium mb-2">No competitor data yet</p>
              <p className="text-sm">Run scans to see how you rank against competitors!</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const renderQueries = () => (
    <div className="space-y-6">
      {renderEnterpriseWelcome()}
      {renderBrandSelector()}
      
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Query Analysis</h2>
        <div className="text-sm text-gray-500">
          {queriesData?.summary?.total_analyzed || 0} queries analyzed
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 text-center">
          <div className="text-3xl font-bold text-green-600">{queriesData?.summary?.with_mentions || 0}</div>
          <div className="text-gray-600">With Mentions</div>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 text-center">
          <div className="text-3xl font-bold text-red-600">{queriesData?.summary?.without_mentions || 0}</div>
          <div className="text-gray-600">Without Mentions</div>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 text-center">
          <div className="text-3xl font-bold text-blue-600">
            {queriesData?.summary?.average_position ? queriesData.summary.average_position.toFixed(1) : '-'}
          </div>
          <div className="text-gray-600">Avg Position</div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Recent Queries</h3>
        </div>
        <div className="divide-y divide-gray-200">
          {queriesData?.queries?.slice(0, 10).map((query, index) => (
            <div key={query.id} className="p-6">
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900">{query.query}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {query.platform} • {new Date(query.date).toLocaleDateString()}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {query.brand_mentioned ? (
                    <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                      ✓ Mentioned
                    </span>
                  ) : (
                    <span className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full">
                      ✗ Not Mentioned
                    </span>
                  )}
                </div>
              </div>
              <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
                {query.response.substring(0, 200)}...
              </div>
              {query.competitors?.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {query.competitors.map((comp, idx) => (
                    <span key={idx} className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded">
                      {comp}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
          
          {(!queriesData?.queries || queriesData.queries.length === 0) && (
            <div className="p-12 text-center text-gray-500">
              <div className="text-4xl mb-4">🔍</div>
              <p className="text-lg font-medium mb-2">No queries yet</p>
              <p className="text-sm">Run your first scan to see detailed query analysis!</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const renderRecommendations = () => (
    <div className="space-y-6">
      {renderEnterpriseWelcome()}
      {renderBrandSelector()}
      
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">AI Recommendations</h2>
        <div className="text-sm text-gray-500">
          {recommendationsData?.total_recommendations || 0} recommendations
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {recommendationsData?.recommendations?.map((rec) => (
          <div key={rec.id} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <div className="flex items-start justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">{rec.title}</h3>
              <span className={`px-2 py-1 text-xs rounded-full ${
                rec.priority === 'High' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
              }`}>
                {rec.priority}
              </span>
            </div>
            
            <div className="space-y-3">
              <div className="text-sm text-gray-600">{rec.description}</div>
              
              <div className="flex items-center space-x-4 text-sm">
                <span className="text-green-600 font-medium">{rec.impact}</span>
                <span className="text-gray-500">•</span>
                <span className="text-gray-500">{rec.time_estimate}</span>
              </div>
              
              <div>
                <div className="text-sm font-medium text-gray-900 mb-2">Action Items:</div>
                <ul className="text-sm text-gray-600 space-y-1">
                  {rec.action_items.map((item, idx) => (
                    <li key={idx} className="flex items-start">
                      <span className="text-blue-600 mr-2">•</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        ))}
        
        {(!recommendationsData?.recommendations || recommendationsData.recommendations.length === 0) && (
          <div className="col-span-2 text-center py-12 text-gray-500">
            <div className="text-4xl mb-4">💡</div>
            <p className="text-lg font-medium mb-2">No recommendations yet</p>
            <p className="text-sm">Run more scans to get AI-powered recommendations!</p>
          </div>
        )}
      </div>
    </div>
  );

  const renderBrands = () => (
    <div className="space-y-6">
      {renderEnterpriseWelcome()}
      
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Your Brands</h2>
        <button
          onClick={() => setActiveTab('add-brand')}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors"
        >
          Add Brand
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {brands.map((brand) => (
          <div key={brand._id} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">{brand.name}</h3>
            <p className="text-gray-600 mb-4">{brand.industry}</p>
            
            <div className="space-y-2 mb-4">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Visibility Score:</span>
                <span className="font-medium">{brand.visibility_score?.toFixed(1) || 0}%</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Total Scans:</span>
                <span className="font-medium">{brand.total_scans || 0}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Last Scanned:</span>
                <span className="font-medium">
                  {brand.last_scanned ? new Date(brand.last_scanned).toLocaleDateString() : 'Never'}
                </span>
              </div>
            </div>
            
            <div className="space-y-2">
              <button
                onClick={() => runScan(brand._id, 'quick')}
                disabled={scanLoading}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                Quick Scan (5 scans)
              </button>
              <button
                onClick={() => runScan(brand._id, 'standard')}
                disabled={scanLoading}
                className="w-full px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50 transition-colors"
              >
                Standard Scan (25 scans)
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderAddBrand = () => (
    <AddBrandForm onSuccess={() => {
      fetchAllRealData();
      setActiveTab('brands');
    }} />
  );

  const renderSettings = () => (
    <div className="space-y-6">
      {renderEnterpriseWelcome()}
      
      <h2 className="text-2xl font-bold text-gray-900">Settings</h2>
      
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Account Information</h3>
        <div className="space-y-3">
          <div className="flex justify-between">
            <span className="text-gray-600">Name:</span>
            <span className="font-medium">{user?.full_name}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Email:</span>
            <span className="font-medium">{user?.email}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Plan:</span>
            <span className="font-medium capitalize text-green-600">
              {user?.plan} {user?.plan === 'enterprise' && '🚀'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Scans Used:</span>
            <span className="font-medium">{user?.scans_used}/{user?.scans_limit}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Domain:</span>
            <span className="font-medium text-blue-600">futureseo.io</span>
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Danger Zone</h3>
        <button
          onClick={logout}
          className="bg-red-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-red-700 transition-colors"
        >
          Sign Out
        </button>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading Enterprise dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4 md:space-x-8">
              <h1 className="text-xl font-bold text-gray-900">futureseo</h1>
              
              {/* Desktop Navigation */}
              <nav className="hidden md:flex space-x-4 lg:space-x-6">
                {[
                  { id: 'overview', name: 'Overview', icon: '📊' },
                  { id: 'competitors', name: 'Competitors', icon: '🏆' },
                  { id: 'queries', name: 'Queries', icon: '🔍' },
                  { id: 'recommendations', name: 'Recommendations', icon: '💡' },
                  { id: 'brands', name: 'Brands', icon: '🎯' },
                  { id: 'plans', name: 'Plans', icon: '💳' },
                  { id: 'settings', name: 'Settings', icon: '⚙️' }
                ].map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      activeTab === tab.id
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    <span>{tab.icon}</span>
                    <span className="hidden lg:inline">{tab.name}</span>
                  </button>
                ))}
              </nav>
              
              {/* Mobile Menu Button */}
              <div className="md:hidden">
                <button
                  onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                  className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
                >
                  <span className="sr-only">Open main menu</span>
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  </svg>
                </button>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-right hidden sm:block">
                <div className="text-sm font-medium text-gray-900">{user?.full_name}</div>
                <div className="text-xs text-green-600 font-medium">
                  Enterprise Plan 🚀
                </div>
              </div>
              <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center text-white font-bold">
                {user?.full_name?.charAt(0).toUpperCase()}
              </div>
            </div>
          </div>
        </div>
        
        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden">
            <div className="px-2 pt-2 pb-3 space-y-1 border-t border-gray-200">
              {[
                { id: 'overview', name: 'Overview', icon: '📊' },
                { id: 'competitors', name: 'Competitors', icon: '🏆' },
                { id: 'queries', name: 'Queries', icon: '🔍' },
                { id: 'recommendations', name: 'Recommendations', icon: '💡' },
                { id: 'brands', name: 'Brands', icon: '🎯' },
                { id: 'plans', name: 'Plans', icon: '💳' },
                { id: 'settings', name: 'Settings', icon: '⚙️' }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => {
                    setActiveTab(tab.id);
                    setMobileMenuOpen(false);
                  }}
                  className={`w-full flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === tab.id
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <span>{tab.icon}</span>
                  <span>{tab.name}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 md:py-8">
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'competitors' && renderCompetitors()}
        {activeTab === 'queries' && renderQueries()}
        {activeTab === 'recommendations' && renderRecommendations()}
        {activeTab === 'brands' && renderBrands()}
        {activeTab === 'add-brand' && renderAddBrand()}
        {activeTab === 'plans' && <PlansPage backendUrl={backendUrl} user={user} token={token} />}
        {activeTab === 'settings' && renderSettings()}
      </div>
    </div>
  );
};

// Add Brand Form Component
const AddBrandForm = ({ onSuccess }) => {
  const [formData, setFormData] = useState({
    name: '',
    industry: '',
    keywords: '',
    competitors: '',
    website: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { backendUrl, token } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${backendUrl}/api/brands`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: formData.name,
          industry: formData.industry,
          keywords: formData.keywords.split(',').map(k => k.trim()),
          competitors: formData.competitors.split(',').map(c => c.trim()),
          website: formData.website
        })
      });

      if (response.ok) {
        onSuccess();
      } else {
        const errorData = await response.json();
        setError(errorData.detail);
      }
    } catch (error) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Add New Brand</h2>
      
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Brand Name
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Industry
            </label>
            <input
              type="text"
              name="industry"
              value={formData.industry}
              onChange={handleChange}
              placeholder="e.g., SaaS, E-commerce, Healthcare"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Keywords (comma-separated)
            </label>
            <input
              type="text"
              name="keywords"
              value={formData.keywords}
              onChange={handleChange}
              placeholder="e.g., productivity, team collaboration, project tracking"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Competitors (comma-separated)
            </label>
            <input
              type="text"
              name="competitors"
              value={formData.competitors}
              onChange={handleChange}
              placeholder="e.g., Asana, Monday.com, Trello"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Website (Optional)
            </label>
            <input
              type="url"
              name="website"
              value={formData.website}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Adding Brand...' : 'Add Brand'}
            </button>
            <button
              type="button"
              onClick={onSuccess}
              className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Main App Component
const App = () => {
  const [showRegister, setShowRegister] = useState(false);

  return (
    <AuthProvider>
      <AppContent showRegister={showRegister} setShowRegister={setShowRegister} />
    </AuthProvider>
  );
};

const AppContent = ({ showRegister, setShowRegister }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return showRegister ? (
      <div>
        <RegisterForm />
        <button
          onClick={() => setShowRegister(false)}
          className="fixed top-4 right-4 text-blue-600 hover:underline"
        >
          Back to Login
        </button>
      </div>
    ) : (
      <div>
        <LoginForm />
        <button
          onClick={() => setShowRegister(true)}
          className="fixed top-4 right-4 text-blue-600 hover:underline"
        >
          Sign Up
        </button>
      </div>
    );
  }

  return <Dashboard />;
};

export default App;