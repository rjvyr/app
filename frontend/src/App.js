import React, { useState, useEffect, createContext, useContext } from 'react';
import PlansPage from './PlansPage';
import './App.css';

// Context for user authentication
const AuthContext = createContext();

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    if (token) {
      fetchUserInfo();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUserInfo = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        logout();
      }
    } catch (error) {
      console.error('Error fetching user info:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await fetch(`${backendUrl}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (response.ok) {
        const data = await response.json();
        setToken(data.access_token);
        localStorage.setItem('token', data.access_token);
        setUser(data.user);
        return { success: true };
      } else {
        const errorData = await response.json();
        return { success: false, error: errorData.detail };
      }
    } catch (error) {
      return { success: false, error: 'Network error' };
    }
  };

  const register = async (userData) => {
    try {
      const response = await fetch(`${backendUrl}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      const data = await response.json();
      return { success: response.ok, message: data.message, error: data.detail };
    } catch (error) {
      return { success: false, error: 'Network error' };
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
  };

  const value = {
    user,
    login,
    register,
    logout,
    loading,
    token,
    backendUrl
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Mock data for enhanced dashboard
const mockCompetitors = [
  { name: "Asana", visibilityScore: 89.2, mentions: 45, trend: "+3%", rank: 1 },
  { name: "Monday.com", visibilityScore: 84.1, mentions: 42, trend: "+1%", rank: 2 },
  { name: "TestBrand", visibilityScore: 72.5, mentions: 29, trend: "+5%", rank: 3 },
  { name: "Trello", visibilityScore: 65.8, mentions: 31, trend: "-2%", rank: 4 },
  { name: "Notion", visibilityScore: 58.3, mentions: 22, trend: "+4%", rank: 5 }
];

const mockQueries = [
  {
    id: 1,
    query: "What are the best project management tools for teams?",
    platform: "ChatGPT",
    brandMentioned: true,
    position: 2,
    response: "Popular project management tools include Asana, TestBrand, and Monday.com. TestBrand offers excellent team collaboration features...",
    competitors: ["Asana", "Monday.com"],
    date: "2 hours ago"
  },
  {
    id: 2,
    query: "How to improve team productivity and collaboration?",
    platform: "Gemini",
    brandMentioned: false,
    position: null,
    response: "Consider tools like Asana, Slack, and Trello for better team coordination. These platforms offer various features...",
    competitors: ["Asana", "Slack", "Trello"],
    date: "4 hours ago"
  },
  {
    id: 3,
    query: "Best software for remote team management?",
    platform: "ChatGPT",
    brandMentioned: true,
    position: 1,
    response: "TestBrand leads in remote team management with comprehensive features. Other options include Monday.com and Asana...",
    competitors: ["Monday.com", "Asana"],
    date: "6 hours ago"
  },
  {
    id: 4,
    query: "Project management software comparison 2024",
    platform: "AI Overview",
    brandMentioned: false,
    position: null,
    response: "Top project management software includes Asana, Monday.com, and Trello. These tools offer different pricing tiers...",
    competitors: ["Asana", "Monday.com", "Trello"],
    date: "8 hours ago"
  },
  {
    id: 5,
    query: "How to choose the right productivity software?",
    platform: "ChatGPT",
    brandMentioned: true,
    position: 3,
    response: "When selecting productivity software, consider Asana for simplicity, Monday.com for customization, and TestBrand for advanced analytics...",
    competitors: ["Asana", "Monday.com"],
    date: "1 day ago"
  }
];

const mockRecommendations = [
  {
    id: 1,
    title: "Target 'team collaboration' queries",
    priority: "High",
    category: "Content Strategy",
    impact: "+12% visibility",
    description: "You're missing 73% of team collaboration queries. This is a high-volume search area.",
    actionItems: [
      "Create comprehensive team collaboration guide",
      "Write comparison: TestBrand vs Slack for teams",
      "Add collaboration features to homepage"
    ],
    timeEstimate: "8 hours"
  },
  {
    id: 2,
    title: "Improve integration content",
    priority: "Medium",
    category: "SEO Optimization",
    impact: "+8% visibility",
    description: "Competitors dominate integration-related queries. Focus on popular integrations.",
    actionItems: [
      "Update integrations page with Zapier guide",
      "Create Slack integration tutorial",
      "Add API documentation examples"
    ],
    timeEstimate: "6 hours"
  },
  {
    id: 3,
    title: "Enhance pricing strategy visibility",
    priority: "High",
    category: "Product Positioning",
    impact: "+15% visibility",
    description: "Zero mentions in pricing strategy queries. This affects purchasing decisions.",
    actionItems: [
      "Develop pricing comparison charts",
      "Create ROI calculator tool",
      "Write pricing strategy best practices"
    ],
    timeEstimate: "12 hours"
  }
];

// Login Component
const LoginForm = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = await login(email, password);
    
    if (!result.success) {
      setError(result.error);
    }
    
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="max-w-md w-full bg-white p-8 rounded-xl shadow-lg">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900">Welcome Back</h2>
          <p className="text-gray-600 mt-2">Sign in to your AI Brand Visibility Scanner</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
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
        
        <div className="mt-6 text-center">
          <p className="text-gray-600">
            Don't have an account?{' '}
            <button className="text-blue-600 hover:underline font-medium">
              Sign up
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

// Registration Component
const RegisterForm = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
    company: '',
    website: ''
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
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
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  if (success) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full bg-white p-8 rounded-xl shadow-lg text-center">
          <div className="text-green-600 text-6xl mb-4">✓</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Account Created!</h2>
          <p className="text-gray-600 mb-6">
            Please check your email to verify your account and start your free trial.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            Continue to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12">
      <div className="max-w-md w-full bg-white p-8 rounded-xl shadow-lg">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900">Get Started</h2>
          <p className="text-gray-600 mt-2">Start your 7-day free trial today</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email Address
            </label>
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
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Full Name
            </label>
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
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Company
            </label>
            <input
              type="text"
              name="company"
              value={formData.company}
              onChange={handleChange}
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
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
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
  const { user, logout, backendUrl, token } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [dashboardData, setDashboardData] = useState(null);
  const [competitorData, setCompetitorData] = useState(null);
  const [queriesData, setQueriesData] = useState(null);
  const [recommendationsData, setRecommendationsData] = useState(null);
  const [brands, setBrands] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scanLoading, setScanLoading] = useState(false);

  useEffect(() => {
    fetchAllRealData();
  }, []);

  const fetchAllRealData = async () => {
    try {
      setLoading(true);
      const headers = { 'Authorization': `Bearer ${token}` };
      
      const [dashboard, competitors, queries, recommendations, brandsRes] = await Promise.all([
        fetch(`${backendUrl}/api/dashboard/real`, { headers }).then(res => res.json()),
        fetch(`${backendUrl}/api/competitors/real`, { headers }).then(res => res.json()),
        fetch(`${backendUrl}/api/queries/real`, { headers }).then(res => res.json()),
        fetch(`${backendUrl}/api/recommendations/real`, { headers }).then(res => res.json()),
        fetch(`${backendUrl}/api/brands`, { headers }).then(res => res.json())
      ]);

      setDashboardData(dashboard);
      setCompetitorData(competitors);
      setQueriesData(queries);
      setRecommendationsData(recommendations);
      setBrands(brandsRes.brands || []);
    } catch (error) {
      console.error('Error fetching real data:', error);
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
        body: JSON.stringify({
          brand_id: brandId,
          scan_type: scanType
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        alert(`Scan completed! Visibility score: ${data.visibility_score.toFixed(1)}%`);
        // Refresh all data after scan
        fetchAllRealData();
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error running scan:', error);
      alert('Error running scan. Please try again.');
    } finally {
      setScanLoading(false);
    }
  };

  // Enhanced Overview Dashboard using REAL data
  const renderOverview = () => (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">AI Visibility Score</h1>
          <p className="text-gray-600 mt-1">Real-time brand visibility tracking</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <div className="text-sm text-gray-500">Real Data</div>
            <div className="text-xs text-gray-400">Live ChatGPT Analysis</div>
          </div>
          <div className="w-3 h-3 bg-green-500 rounded-full"></div>
        </div>
      </div>

      {/* Main Score Card using REAL data */}
      <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100">
        <div className="text-center">
          <div className="text-6xl font-bold text-blue-600 mb-2">
            {dashboardData?.overall_visibility ? Math.round(dashboardData.overall_visibility) : 0}
          </div>
          <div className="text-lg text-gray-600 mb-4">
            {dashboardData?.overall_visibility > 70 ? 'Excellent' : 
             dashboardData?.overall_visibility > 50 ? 'Good' : 
             dashboardData?.overall_visibility > 30 ? 'Fair' : 'Needs Improvement'}
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
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Platform Breakdown (Real Data)</h3>
        <div className="space-y-4">
          {dashboardData?.platform_breakdown && Object.entries(dashboardData.platform_breakdown).map(([platform, data]) => (
            <div key={platform} className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <span className="text-blue-600 font-bold">
                    {platform === 'ChatGPT' ? '🤖' : platform === 'Gemini' ? '💎' : '🔍'}
                  </span>
                </div>
                <div>
                  <div className="font-semibold text-gray-900">{platform}</div>
                  <div className="text-sm text-gray-500">{data.mentions} mentions out of {data.total_questions} queries</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-blue-600">{Math.round(data.visibility_rate)}%</div>
                <div className="text-sm text-gray-500">Real API data</div>
              </div>
            </div>
          ))}
          
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <button
            onClick={() => brands.length > 0 && runScan(brands[0]._id, 'quick')}
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
            onClick={() => brands.length > 0 && runScan(brands[0]._id, 'standard')}
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
            onClick={() => brands.length > 0 && runScan(brands[0]._id, 'deep')}
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
            onClick={() => brands.length > 0 && runScan(brands[0]._id, 'competitor')}
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
          <span className="text-sm text-gray-500">
            {user?.plan === 'trial' ? 'Free Trial' : `${user?.plan} Plan`}
          </span>
        </div>
        <div className="space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Scans Used</span>
            <span className="font-medium">{user?.scans_used || 0}/{user?.scans_limit || 50}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full" 
              style={{width: `${((user?.scans_used || 0) / (user?.scans_limit || 50)) * 100}%`}}
            ></div>
          </div>
          <div className="text-xs text-gray-500">
            {(user?.scans_limit || 50) - (user?.scans_used || 0)} scans remaining
          </div>
        </div>
      </div>
    </div>
  );

  // Real Competitors Tab
  const renderCompetitors = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Competitors (Real Data)</h2>
          <p className="text-gray-600 mt-1">
            {competitorData?.user_position ? `Your rank: #${competitorData.user_position} out of ${competitorData.total_competitors}` : 'Based on real ChatGPT scan results'}
          </p>
        </div>
        <div className="text-sm text-gray-500">
          {competitorData?.total_queries_analyzed || 0} total queries analyzed
        </div>
      </div>

      {/* Competitor Rankings using REAL data */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-6 border-b border-gray-100">
          <h3 className="text-lg font-semibold text-gray-900">Real Visibility Rankings</h3>
        </div>
        <div className="divide-y divide-gray-100">
          {competitorData?.competitors?.length > 0 ? competitorData.competitors.map((competitor, index) => (
            <div key={competitor.name} className="p-6 flex items-center justify-between hover:bg-gray-50 transition-colors">
              <div className="flex items-center space-x-4">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold ${
                  competitor.is_user_brand ? 'bg-blue-600' : 
                  index === 0 ? 'bg-yellow-500' :
                  index === 1 ? 'bg-gray-400' :
                  index === 2 ? 'bg-orange-500' : 'bg-gray-300'
                }`}>
                  {competitor.rank}
                </div>
                <div>
                  <div className={`font-semibold ${competitor.is_user_brand ? 'text-blue-600' : 'text-gray-900'}`}>
                    {competitor.name}
                    {competitor.is_user_brand && <span className="ml-2 text-xs bg-blue-100 text-blue-600 px-2 py-1 rounded">You</span>}
                  </div>
                  <div className="text-sm text-gray-500">{competitor.mentions} mentions in {competitor.total_queries} queries</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-xl font-bold text-gray-900">{competitor.visibility_score.toFixed(1)}%</div>
                <div className="text-sm text-gray-500">Real data</div>
              </div>
            </div>
          )) : (
            <div className="p-8 text-center text-gray-500">
              <div className="text-4xl mb-4">🏆</div>
              <p className="text-lg font-medium mb-2">No competitor data yet</p>
              <p className="text-sm">Run scans to see how you compare against competitors!</p>
              <button
                onClick={() => brands.length > 0 && runScan(brands[0]._id, 'standard')}
                disabled={scanLoading || brands.length === 0}
                className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                Run Competitor Analysis
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  // Real Queries Tab
  const renderQueries = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Queries (Real ChatGPT Data)</h2>
          <p className="text-gray-600 mt-1">Actual AI responses from GPT-4o-mini</p>
        </div>
        <div className="text-sm text-gray-500">
          {queriesData?.summary?.total_analyzed || 0} real queries analyzed
        </div>
      </div>

      {/* Query Stats using REAL data */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-100">
          <div className="text-sm text-gray-600">Total Queries</div>
          <div className="text-2xl font-bold text-gray-900">{queriesData?.summary?.total_analyzed || 0}</div>
        </div>
        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
          <div className="text-sm text-green-600">Mentioned</div>
          <div className="text-2xl font-bold text-green-700">{queriesData?.summary?.with_mentions || 0}</div>
        </div>
        <div className="bg-red-50 p-4 rounded-lg border border-red-200">
          <div className="text-sm text-red-600">Not Mentioned</div>
          <div className="text-2xl font-bold text-red-700">{queriesData?.summary?.without_mentions || 0}</div>
        </div>
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <div className="text-sm text-blue-600">Avg Position</div>
          <div className="text-2xl font-bold text-blue-700">
            {queriesData?.summary?.average_position ? `#${queriesData.summary.average_position.toFixed(1)}` : 'N/A'}
          </div>
        </div>
      </div>

      {/* Real Query Results */}
      <div className="space-y-4">
        {queriesData?.queries?.length > 0 ? queriesData.queries.map((query) => (
          <div key={query.id} className={`bg-white p-6 rounded-xl border-2 ${
            query.brand_mentioned ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
          }`}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-3">
                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                  query.brand_mentioned 
                    ? 'bg-green-200 text-green-800' 
                    : 'bg-red-200 text-red-800'
                }`}>
                  {query.brand_mentioned ? 'MENTIONED' : 'NOT MENTIONED'}
                </span>
                <span className="text-sm text-gray-600">{query.platform}</span>
                <span className="text-xs text-blue-600">{query.model}</span>
                {query.position && (
                  <span className="text-sm font-semibold text-blue-600">Position #{query.position}</span>
                )}
              </div>
              <span className="text-sm text-gray-500">{new Date(query.date).toLocaleDateString()}</span>
            </div>
            
            <h4 className="text-lg font-semibold text-gray-900 mb-3">{query.query}</h4>
            <div className="bg-white p-4 rounded border mb-4">
              <p className="text-gray-700 text-sm">
                <strong>Real ChatGPT Response:</strong><br />
                {query.response}
              </p>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600">Competitors mentioned:</span>
                {query.competitors && query.competitors.length > 0 ? query.competitors.map((competitor, index) => (
                  <span key={index} className="px-2 py-1 bg-gray-200 text-gray-700 text-xs rounded">
                    {competitor}
                  </span>
                )) : (
                  <span className="text-xs text-gray-400">None detected</span>
                )}
              </div>
              {query.mentioned_brand && (
                <span className="text-sm font-medium text-green-600">
                  ✓ {query.mentioned_brand} mentioned
                </span>
              )}
            </div>
          </div>
        )) : (
          <div className="bg-white p-8 rounded-xl border border-gray-100 text-center">
            <div className="text-4xl mb-4">❓</div>
            <p className="text-lg font-medium text-gray-900 mb-2">No query data yet</p>
            <p className="text-gray-600 mb-6">Run your first scan to see real ChatGPT responses!</p>
            <button
              onClick={() => brands.length > 0 && runScan(brands[0]._id, 'quick')}
              disabled={scanLoading || brands.length === 0}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              Run Quick Scan
            </button>
          </div>
        )}
      </div>
    </div>
  );

  // Real Recommendations Tab
  const renderRecommendations = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">AI-Powered Recommendations</h2>
          <p className="text-gray-600 mt-1">Based on real scan data and AI analysis</p>
        </div>
        <div className="text-sm text-gray-500">
          {recommendationsData?.data_points || 0} data points analyzed
        </div>
      </div>

      {/* Recommendation Stats using REAL data */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-red-50 p-4 rounded-lg border border-red-200">
          <div className="text-sm text-red-600">High Priority</div>
          <div className="text-2xl font-bold text-red-700">{recommendationsData?.high_priority || 0}</div>
          <div className="text-xs text-red-600">Action needed</div>
        </div>
        <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
          <div className="text-sm text-yellow-600">Medium Priority</div>
          <div className="text-2xl font-bold text-yellow-700">{recommendationsData?.medium_priority || 0}</div>
          <div className="text-xs text-yellow-600">Consider soon</div>
        </div>
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <div className="text-sm text-blue-600">Total Recommendations</div>
          <div className="text-2xl font-bold text-blue-700">{recommendationsData?.total_recommendations || 0}</div>
          <div className="text-xs text-blue-600">AI-generated</div>
        </div>
      </div>

      {/* Real Recommendations List */}
      <div className="space-y-6">
        {recommendationsData?.recommendations?.length > 0 ? recommendationsData.recommendations.map((rec) => (
          <div key={rec.id} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <h3 className="text-lg font-semibold text-gray-900">{rec.title}</h3>
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                    rec.priority === 'High' ? 'bg-red-100 text-red-800' :
                    rec.priority === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {rec.priority} Priority
                  </span>
                  <span className="px-3 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                    {rec.category}
                  </span>
                </div>
                <p className="text-gray-700 mb-4">{rec.description}</p>
              </div>
              <div className="text-right ml-4">
                <div className="text-lg font-bold text-green-600">{rec.impact}</div>
                <div className="text-sm text-gray-500">{rec.time_estimate}</div>
              </div>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-semibold text-gray-900 mb-3">📋 Action Items:</h4>
              <ul className="space-y-2">
                {rec.action_items?.map((item, index) => (
                  <li key={index} className="flex items-start space-x-3">
                    <input type="checkbox" className="mt-1 rounded border-gray-300" />
                    <span className="text-gray-700">{item}</span>
                  </li>
                ))}
              </ul>
              <div className="mt-4 flex space-x-3">
                <button className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
                  Start Working
                </button>
                <button className="border border-gray-300 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors">
                  Mark Complete
                </button>
              </div>
            </div>
          </div>
        )) : (
          <div className="bg-white p-8 rounded-xl border border-gray-100 text-center">
            <div className="text-4xl mb-4">💡</div>
            <p className="text-lg font-medium text-gray-900 mb-2">No recommendations yet</p>
            <p className="text-gray-600 mb-6">Run more scans to get AI-powered recommendations based on your data!</p>
            <button
              onClick={() => brands.length > 0 && runScan(brands[0]._id, 'standard')}
              disabled={scanLoading || brands.length === 0}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              Run Standard Scan
            </button>
          </div>
        )}
      </div>
    </div>
  );

  const renderBrands = () => (
    <div className="space-y-6">
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

  // Plans/Pricing Tab
  const renderPlans = () => {
    const [plans, setPlans] = useState([]);
    const [loadingPlans, setLoadingPlans] = useState(true);
    const [upgradingPlan, setUpgradingPlan] = useState(false);

    useEffect(() => {
      fetchPlans();
    }, []);

    const fetchPlans = async () => {
      try {
        const response = await fetch(`${backendUrl}/api/plans`);
        const data = await response.json();
        setPlans(data.plans);
      } catch (error) {
        console.error('Error fetching plans:', error);
      } finally {
        setLoadingPlans(false);
      }
    };

    const handleUpgrade = async (planId) => {
      setUpgradingPlan(true);
      try {
        // For demo purposes, directly upgrade the user
        const response = await fetch(`${backendUrl}/api/admin/upgrade-user?user_email=${user.email}&new_plan=${planId}`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          alert(`Successfully upgraded to ${planId} plan!`);
          // Refresh user data
          window.location.reload();
        } else {
          const error = await response.json();
          alert(`Error: ${error.detail}`);
        }
      } catch (error) {
        console.error('Error upgrading plan:', error);
        alert('Error upgrading plan. Please try again.');
      } finally {
        setUpgradingPlan(false);
      }
    };

    if (loadingPlans) {
      return <div className="text-center py-8">Loading plans...</div>;
    }

    return (
      <div className="space-y-6">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-900">Choose Your Plan</h2>
          <p className="text-gray-600 mt-2">Select the perfect plan for your AI visibility tracking needs</p>
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-blue-800 font-medium">🎉 Current Plan: {user?.plan?.toUpperCase() || 'TRIAL'}</p>
            <p className="text-blue-600 text-sm">Domain: futureseo.io (Ready for deployment!)</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-7xl mx-auto">
          {plans.map((plan) => (
            <div
              key={plan.id}
              className={`relative bg-white p-8 rounded-2xl shadow-lg border-2 ${
                plan.popular ? 'border-blue-500 transform scale-105' : 'border-gray-200'
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <span className="bg-blue-500 text-white px-4 py-2 rounded-full text-sm font-medium">
                    Most Popular
                  </span>
                </div>
              )}

              <div className="text-center">
                <h3 className="text-2xl font-bold text-gray-900">{plan.name}</h3>
                <div className="mt-4 flex items-baseline justify-center">
                  <span className="text-5xl font-extrabold text-gray-900">${plan.price}</span>
                  <span className="ml-1 text-xl text-gray-500">/{plan.interval}</span>
                </div>
                <p className="mt-2 text-gray-500">{plan.scans} AI scans per month</p>
              </div>

              <ul className="mt-8 space-y-4">
                {plan.features.map((feature, index) => (
                  <li key={index} className="flex items-center">
                    <svg className="h-5 w-5 text-green-500 mr-3" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    <span className="text-gray-600">{feature}</span>
                  </li>
                ))}
              </ul>

              <div className="mt-8">
                {user?.plan === plan.id ? (
                  <button className="w-full bg-green-100 text-green-700 py-3 px-4 rounded-lg font-medium cursor-not-allowed">
                    Current Plan
                  </button>
                ) : (
                  <button
                    onClick={() => handleUpgrade(plan.id)}
                    disabled={upgradingPlan}
                    className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
                      plan.popular
                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                        : 'bg-gray-900 text-white hover:bg-gray-800'
                    } disabled:opacity-50`}
                  >
                    {upgradingPlan ? 'Upgrading...' : 'Upgrade to ' + plan.name}
                  </button>
                )}
              </div>

              {plan.id === 'enterprise' && (
                <div className="mt-4 p-3 bg-purple-50 border border-purple-200 rounded-lg">
                  <p className="text-purple-800 text-sm font-medium">🚀 Perfect for futureseo.io!</p>
                  <p className="text-purple-600 text-xs">Full feature testing + enterprise capabilities</p>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Feature Comparison */}
        <div className="mt-12 bg-white p-8 rounded-xl border border-gray-200">
          <h3 className="text-xl font-bold text-gray-900 mb-6">Feature Comparison</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 text-gray-900 font-medium">Feature</th>
                  <th className="text-center py-3 text-gray-900 font-medium">Basic</th>
                  <th className="text-center py-3 text-gray-900 font-medium">Pro</th>
                  <th className="text-center py-3 text-gray-900 font-medium">Enterprise</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                <tr>
                  <td className="py-4 text-gray-600">AI Platforms</td>
                  <td className="py-4 text-center text-gray-600">ChatGPT only</td>
                  <td className="py-4 text-center text-green-600">✓ All platforms</td>
                  <td className="py-4 text-center text-green-600">✓ All platforms</td>
                </tr>
                <tr>
                  <td className="py-4 text-gray-600">Brands</td>
                  <td className="py-4 text-center text-gray-600">1</td>
                  <td className="py-4 text-center text-gray-600">3</td>
                  <td className="py-4 text-center text-gray-600">10</td>
                </tr>
                <tr>
                  <td className="py-4 text-gray-600">Monthly Scans</td>
                  <td className="py-4 text-center text-gray-600">50</td>
                  <td className="py-4 text-center text-gray-600">300</td>
                  <td className="py-4 text-center text-gray-600">1,500</td>
                </tr>
                <tr>
                  <td className="py-4 text-gray-600">Competitor Analysis</td>
                  <td className="py-4 text-center text-gray-400">✗</td>
                  <td className="py-4 text-center text-green-600">✓</td>
                  <td className="py-4 text-center text-green-600">✓ Advanced</td>
                </tr>
                <tr>
                  <td className="py-4 text-gray-600">Weekly Recommendations</td>
                  <td className="py-4 text-center text-gray-400">✗</td>
                  <td className="py-4 text-center text-green-600">✓</td>
                  <td className="py-4 text-center text-green-600">✓ Custom</td>
                </tr>
                <tr>
                  <td className="py-4 text-gray-600">Team Collaboration</td>
                  <td className="py-4 text-center text-gray-400">✗</td>
                  <td className="py-4 text-center text-gray-400">✗</td>
                  <td className="py-4 text-center text-green-600">✓</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Domain Info */}
        <div className="mt-8 p-6 bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-xl">
          <div className="flex items-center space-x-4">
            <div className="text-4xl">🌐</div>
            <div>
              <h4 className="font-bold text-gray-900">Ready for futureseo.io Deployment!</h4>
              <p className="text-gray-600">Your domain is ready. Choose Enterprise plan to test all features before going live.</p>
            </div>
          </div>
        </div>
      </div>
    );
  };
    <div className="space-y-6">
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
            <span className="font-medium capitalize">{user?.plan}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Scans Used:</span>
            <span className="font-medium">{user?.scans_used}/{user?.scans_limit}</span>
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
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
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
            <div className="flex items-center space-x-8">
              <h1 className="text-xl font-bold text-gray-900">AI Brand Visibility</h1>
              <nav className="flex space-x-6">
                {[
                  { id: 'overview', name: 'Overview', icon: '📊' },
                  { id: 'competitors', name: 'Competitors', icon: '🏆' },
                  { id: 'queries', name: 'Queries', icon: '❓' },
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
                    <span>{tab.name}</span>
                  </button>
                ))}
              </nav>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <div className="text-sm font-medium text-gray-900">{user?.full_name}</div>
                <div className="text-xs text-gray-500 capitalize">{user?.plan} Plan</div>
              </div>
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold">
                {user?.full_name?.charAt(0).toUpperCase()}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'competitors' && renderCompetitors()}
        {activeTab === 'queries' && renderQueries()}
        {activeTab === 'recommendations' && renderRecommendations()}
        {activeTab === 'brands' && renderBrands()}
        {activeTab === 'add-brand' && renderAddBrand()}
        {activeTab === 'plans' && <PlansPage />}
        {activeTab === 'settings' && renderSettings()}
      </div>
    </div>
  );
};

// Plans Page Component
const PlansPage = () => {
  const { user, backendUrl, token } = useAuth();
  const [plans, setPlans] = useState([]);
  const [loadingPlans, setLoadingPlans] = useState(true);
  const [upgradingPlan, setUpgradingPlan] = useState(false);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/plans`);
      const data = await response.json();
      setPlans(data.plans);
    } catch (error) {
      console.error('Error fetching plans:', error);
    } finally {
      setLoadingPlans(false);
    }
  };

  const handleUpgrade = async (planId) => {
    setUpgradingPlan(true);
    try {
      // For demo purposes, directly upgrade the user
      const response = await fetch(`${backendUrl}/api/admin/upgrade-user?user_email=${user.email}&new_plan=${planId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        alert(`Successfully upgraded to ${planId} plan!`);
        // Refresh user data
        window.location.reload();
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error upgrading plan:', error);
      alert('Error upgrading plan. Please try again.');
    } finally {
      setUpgradingPlan(false);
    }
  };

  if (loadingPlans) {
    return <div className="text-center py-8">Loading plans...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900">Choose Your Plan</h2>
        <p className="text-gray-600 mt-2">Select the perfect plan for your AI visibility tracking needs</p>
        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-blue-800 font-medium">🎉 Current Plan: {user?.plan?.toUpperCase() || 'TRIAL'}</p>
          <p className="text-blue-600 text-sm">Domain: futureseo.io (Ready for deployment!)</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-7xl mx-auto">
        {plans.map((plan) => (
          <div
            key={plan.id}
            className={`relative bg-white p-8 rounded-2xl shadow-lg border-2 ${
              plan.popular ? 'border-blue-500 transform scale-105' : 'border-gray-200'
            }`}
          >
            {plan.popular && (
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                <span className="bg-blue-500 text-white px-4 py-2 rounded-full text-sm font-medium">
                  Most Popular
                </span>
              </div>
            )}

            <div className="text-center">
              <h3 className="text-2xl font-bold text-gray-900">{plan.name}</h3>
              <div className="mt-4 flex items-baseline justify-center">
                <span className="text-5xl font-extrabold text-gray-900">${plan.price}</span>
                <span className="ml-1 text-xl text-gray-500">/{plan.interval}</span>
              </div>
              <p className="mt-2 text-gray-500">{plan.scans} AI scans per month</p>
            </div>

            <ul className="mt-8 space-y-4">
              {plan.features.map((feature, index) => (
                <li key={index} className="flex items-center">
                  <svg className="h-5 w-5 text-green-500 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  <span className="text-gray-600">{feature}</span>
                </li>
              ))}
            </ul>

            <div className="mt-8">
              {user?.plan === plan.id ? (
                <button className="w-full bg-green-100 text-green-700 py-3 px-4 rounded-lg font-medium cursor-not-allowed">
                  Current Plan
                </button>
              ) : (
                <button
                  onClick={() => handleUpgrade(plan.id)}
                  disabled={upgradingPlan}
                  className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
                    plan.popular
                      ? 'bg-blue-600 text-white hover:bg-blue-700'
                      : 'bg-gray-900 text-white hover:bg-gray-800'
                  } disabled:opacity-50`}
                >
                  {upgradingPlan ? 'Upgrading...' : 'Upgrade to ' + plan.name}
                </button>
              )}
            </div>

            {plan.id === 'enterprise' && (
              <div className="mt-4 p-3 bg-purple-50 border border-purple-200 rounded-lg">
                <p className="text-purple-800 text-sm font-medium">🚀 Perfect for futureseo.io!</p>
                <p className="text-purple-600 text-xs">Full feature testing + enterprise capabilities</p>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Feature Comparison */}
      <div className="mt-12 bg-white p-8 rounded-xl border border-gray-200">
        <h3 className="text-xl font-bold text-gray-900 mb-6">Feature Comparison</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 text-gray-900 font-medium">Feature</th>
                <th className="text-center py-3 text-gray-900 font-medium">Basic</th>
                <th className="text-center py-3 text-gray-900 font-medium">Pro</th>
                <th className="text-center py-3 text-gray-900 font-medium">Enterprise</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              <tr>
                <td className="py-4 text-gray-600">AI Platforms</td>
                <td className="py-4 text-center text-gray-600">ChatGPT only</td>
                <td className="py-4 text-center text-green-600">✓ All platforms</td>
                <td className="py-4 text-center text-green-600">✓ All platforms</td>
              </tr>
              <tr>
                <td className="py-4 text-gray-600">Brands</td>
                <td className="py-4 text-center text-gray-600">1</td>
                <td className="py-4 text-center text-gray-600">3</td>
                <td className="py-4 text-center text-gray-600">10</td>
              </tr>
              <tr>
                <td className="py-4 text-gray-600">Monthly Scans</td>
                <td className="py-4 text-center text-gray-600">50</td>
                <td className="py-4 text-center text-gray-600">300</td>
                <td className="py-4 text-center text-gray-600">1,500</td>
              </tr>
              <tr>
                <td className="py-4 text-gray-600">Competitor Analysis</td>
                <td className="py-4 text-center text-gray-400">✗</td>
                <td className="py-4 text-center text-green-600">✓</td>
                <td className="py-4 text-center text-green-600">✓ Advanced</td>
              </tr>
              <tr>
                <td className="py-4 text-gray-600">Weekly Recommendations</td>
                <td className="py-4 text-center text-gray-400">✗</td>
                <td className="py-4 text-center text-green-600">✓</td>
                <td className="py-4 text-center text-green-600">✓ Custom</td>
              </tr>
              <tr>
                <td className="py-4 text-gray-600">Team Collaboration</td>
                <td className="py-4 text-center text-gray-400">✗</td>
                <td className="py-4 text-center text-gray-400">✗</td>
                <td className="py-4 text-center text-green-600">✓</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Domain Info */}
      <div className="mt-8 p-6 bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-xl">
        <div className="flex items-center space-x-4">
          <div className="text-4xl">🌐</div>
          <div>
            <h4 className="font-bold text-gray-900">Ready for futureseo.io Deployment!</h4>
            <p className="text-gray-600">Your domain is ready. Choose Enterprise plan to test all features before going live.</p>
          </div>
        </div>
      </div>
    </div>
  );
};
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
              placeholder="e.g., project management, team collaboration, productivity"
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
          
          <div className="flex space-x-4">
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