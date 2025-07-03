import React, { useState, useEffect } from 'react';
import './App.css';

const App = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [dashboardData, setDashboardData] = useState(null);
  const [competitorData, setCompetitorData] = useState(null);
  const [questionsData, setQuestionsData] = useState(null);
  const [recommendationsData, setRecommendationsData] = useState(null);
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(true);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      const [dashboard, competitors, questions, recommendations, analytics] = await Promise.all([
        fetch(`${backendUrl}/api/dashboard`).then(res => res.json()),
        fetch(`${backendUrl}/api/competitors`).then(res => res.json()),
        fetch(`${backendUrl}/api/questions`).then(res => res.json()),
        fetch(`${backendUrl}/api/recommendations`).then(res => res.json()),
        fetch(`${backendUrl}/api/analytics`).then(res => res.json())
      ]);

      setDashboardData(dashboard);
      setCompetitorData(competitors);
      setQuestionsData(questions);
      setRecommendationsData(recommendations);
      setAnalyticsData(analytics);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const ScoreCard = ({ title, value, change, icon, color = "blue" }) => (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className={`text-2xl font-bold text-${color}-600`}>{value}</p>
          {change && (
            <p className={`text-sm ${change > 0 ? 'text-green-600' : 'text-red-600'} flex items-center`}>
              {change > 0 ? '↗' : '↘'} {Math.abs(change).toFixed(1)}%
            </p>
          )}
        </div>
        <div className={`text-${color}-600 text-3xl`}>{icon}</div>
      </div>
    </div>
  );

  const renderDashboard = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">AI Brand Visibility Dashboard</h1>
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <span>Last updated: {dashboardData?.last_updated ? new Date(dashboardData.last_updated).toLocaleDateString() : 'N/A'}</span>
          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <ScoreCard
          title="Visibility Score"
          value={`${dashboardData?.visibility_score?.toFixed(1)}%`}
          change={dashboardData?.score_change}
          icon="📊"
          color="blue"
        />
        <ScoreCard
          title="Questions Analyzed"
          value={dashboardData?.total_questions_analyzed}
          icon="❓"
          color="green"
        />
        <ScoreCard
          title="Mentioned In"
          value={dashboardData?.questions_with_mentions}
          icon="✅"
          color="purple"
        />
        <ScoreCard
          title="Missing From"
          value={dashboardData?.questions_without_mentions}
          icon="❌"
          color="red"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Weekly Trend</h3>
          <div className="h-48 flex items-end justify-between space-x-2">
            {dashboardData?.weekly_trend?.map((score, index) => (
              <div key={index} className="flex-1 flex flex-col items-center">
                <div
                  className="w-full bg-blue-500 rounded-t"
                  style={{ height: `${(score / 100) * 100}%` }}
                ></div>
                <span className="text-xs text-gray-500 mt-1">{score.toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">AI Platform Breakdown</h3>
          <div className="space-y-4">
            {analyticsData?.platform_breakdown && Object.entries(analyticsData.platform_breakdown).map(([platform, data]) => (
              <div key={platform} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-4 h-4 bg-blue-500 rounded-full"></div>
                  <span className="font-medium">{platform}</span>
                </div>
                <div className="text-right">
                  <div className="text-sm font-semibold">{data.visibility_rate.toFixed(1)}%</div>
                  <div className="text-xs text-gray-500">{data.mentions}/{data.total_questions}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  const renderCompetitors = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Competitive Analysis</h2>
        <div className="text-sm text-gray-500">
          Market Position: #{competitorData?.market_position} of {competitorData?.total_competitors}
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Brand Visibility Rankings</h3>
          <div className="space-y-4">
            {competitorData?.competitors?.map((competitor, index) => (
              <div key={competitor.brand_name} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold ${
                    competitor.brand_name === 'Wholesale Helper' ? 'bg-blue-600' : 'bg-gray-400'
                  }`}>
                    {index + 1}
                  </div>
                  <div>
                    <div className="font-semibold text-gray-900">{competitor.brand_name}</div>
                    <div className="text-sm text-gray-500">{competitor.total_mentions} mentions</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-gray-900">{competitor.visibility_score.toFixed(1)}%</div>
                  <div className="text-sm text-gray-500">{competitor.market_share.toFixed(1)}% market share</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  const renderQuestions = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Question Analysis</h2>
        <div className="text-sm text-gray-500">
          {questionsData?.summary?.with_mentions}/{questionsData?.summary?.total_analyzed} questions mention your brand
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
          <div className="text-green-800 font-semibold">Questions with Mentions</div>
          <div className="text-2xl font-bold text-green-900">{questionsData?.summary?.with_mentions}</div>
        </div>
        <div className="bg-red-50 p-4 rounded-lg border border-red-200">
          <div className="text-red-800 font-semibold">Questions without Mentions</div>
          <div className="text-2xl font-bold text-red-900">{questionsData?.summary?.without_mentions}</div>
        </div>
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <div className="text-blue-800 font-semibold">Average Position</div>
          <div className="text-2xl font-bold text-blue-900">#{questionsData?.summary?.average_position?.toFixed(1)}</div>
        </div>
      </div>

      <div className="space-y-4">
        {questionsData?.questions?.map((question, index) => (
          <div key={index} className={`p-6 rounded-xl border-2 ${
            question.mentions_brand ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
          }`}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-3">
                <span className={`px-2 py-1 rounded text-xs font-semibold ${
                  question.mentions_brand ? 'bg-green-200 text-green-800' : 'bg-red-200 text-red-800'
                }`}>
                  {question.mentions_brand ? 'MENTIONED' : 'NOT MENTIONED'}
                </span>
                <span className="text-sm text-gray-600">{question.ai_platform}</span>
                {question.ranking_position && (
                  <span className="text-sm font-semibold text-blue-600">Position #{question.ranking_position}</span>
                )}
              </div>
            </div>
            
            <h4 className="text-lg font-semibold text-gray-900 mb-2">{question.question}</h4>
            <p className="text-gray-700 mb-3">{question.response_snippet}</p>
            
            {question.competitors_mentioned.length > 0 && (
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600">Competitors mentioned:</span>
                {question.competitors_mentioned.map((competitor, i) => (
                  <span key={i} className="px-2 py-1 bg-gray-200 text-gray-700 text-xs rounded">
                    {competitor}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );

  const renderRecommendations = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Weekly Recommendations</h2>
        <div className="text-sm text-gray-500">
          {recommendationsData?.high_priority} High Priority • {recommendationsData?.medium_priority} Medium Priority
        </div>
      </div>

      <div className="space-y-4">
        {recommendationsData?.recommendations?.map((recommendation, index) => (
          <div key={index} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">{recommendation.title}</h3>
              <div className="flex items-center space-x-2">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  recommendation.priority === 'High' ? 'bg-red-100 text-red-800' :
                  recommendation.priority === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-green-100 text-green-800'
                }`}>
                  {recommendation.priority} Priority
                </span>
                <span className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-full">
                  {recommendation.category}
                </span>
              </div>
            </div>
            
            <p className="text-gray-700 mb-4">{recommendation.description}</p>
            
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-semibold text-gray-900 mb-2">Action Items:</h4>
              <ul className="space-y-1">
                {recommendation.action_items.map((item, i) => (
                  <li key={i} className="text-gray-700 flex items-center space-x-2">
                    <span className="text-blue-600">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading AI Brand Visibility Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-8">
              <div className="flex-shrink-0">
                <h1 className="text-xl font-bold text-gray-900">AI Brand Visibility</h1>
              </div>
              <div className="flex space-x-4">
                {[
                  { id: 'dashboard', name: 'Dashboard', icon: '📊' },
                  { id: 'competitors', name: 'Competitors', icon: '🏆' },
                  { id: 'questions', name: 'Questions', icon: '❓' },
                  { id: 'recommendations', name: 'Recommendations', icon: '💡' }
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
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">Tracking: <strong>Wholesale Helper</strong></span>
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-xs text-gray-500">Live</span>
              </div>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && renderDashboard()}
        {activeTab === 'competitors' && renderCompetitors()}
        {activeTab === 'questions' && renderQuestions()}
        {activeTab === 'recommendations' && renderRecommendations()}
      </main>
    </div>
  );
};

export default App;