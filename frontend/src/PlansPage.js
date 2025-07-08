import React, { useState, useEffect } from 'react';

const PlansPage = ({ backendUrl, user, token }) => {
  const [plans, setPlans] = useState([]);
  const [earlyAccess, setEarlyAccess] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/plans`);
      const data = await response.json();
      setPlans(data.plans || []);
      setEarlyAccess(data.early_access || null);
    } catch (error) {
      console.error('Error fetching plans:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-8">Loading plans...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900">Choose Your Plan</h2>
        <p className="text-gray-600 mt-2">Weekly AI visibility scans with comprehensive insights</p>
        
        {/* Early Access Banner */}
        {earlyAccess?.available && (
          <div className="mt-4 p-4 bg-gradient-to-r from-orange-50 to-red-50 border border-orange-200 rounded-lg">
            <p className="text-orange-800 font-bold">🔥 LIMITED EARLY ACCESS PRICING</p>
            <p className="text-orange-700 text-sm">
              Only {earlyAccess.remaining_seats} of {earlyAccess.total_seats} early access seats remaining!
            </p>
            <p className="text-orange-600 text-xs mt-1">
              Lock in these prices for 6 months, then pricing increases
            </p>
          </div>
        )}
        
        {/* Current Status */}
        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-green-800 font-medium">✅ Currently on ENTERPRISE Preview</p>
          <p className="text-green-600 text-sm">Full access to test all features</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
        {plans.map((plan) => (
          <div
            key={plan.id}
            className={`relative bg-white p-8 rounded-2xl shadow-lg border-2 ${
              plan.popular ? 'border-blue-500 transform scale-105' : 'border-gray-200'
            } ${plan.id === 'pro' ? 'bg-gradient-to-br from-blue-50 to-purple-50' : ''}`}
          >
            {plan.popular && (
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                <span className="bg-blue-500 text-white px-4 py-2 rounded-full text-sm font-medium">
                  Most Popular
                </span>
              </div>
            )}

            {/* Early Access Badge */}
            {plan.is_early_access && earlyAccess?.available && (
              <div className="absolute -top-2 -right-2">
                <span className="bg-orange-500 text-white px-2 py-1 rounded-full text-xs font-bold">
                  Early Access
                </span>
              </div>
            )}

            <div className="text-center mb-6">
              <h3 className="text-2xl font-bold text-gray-900">{plan.name}</h3>
              <p className="text-gray-600 text-sm mt-1">{plan.description}</p>
              
              {/* Pricing */}
              <div className="mt-4">
                <div className="flex items-center justify-center">
                  <span className="text-4xl font-bold text-gray-900">
                    ${plan.price}
                  </span>
                  <span className="text-gray-500 ml-2">/month</span>
                </div>
                
                {/* Early Access Price Comparison */}
                {plan.is_early_access && plan.regular_price > plan.price && (
                  <div className="mt-2">
                    <span className="text-gray-500 line-through text-sm">
                      Regular: ${plan.regular_price}/month
                    </span>
                    <div className="text-green-600 text-sm font-medium">
                      Save ${plan.regular_price - plan.price}/month for 6 months!
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Features */}
            <div className="space-y-4 mb-8">
              {/* Main Features */}
              <div className="space-y-2">
                <div className="flex items-center">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-700">
                    {plan.brands} brand{plan.brands > 1 ? 's' : ''} tracking
                  </span>
                </div>
                
                {plan.weekly_scans > 0 ? (
                  <div className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    <span className="text-gray-700">
                      {plan.weekly_scans} full scan{plan.weekly_scans > 1 ? 's' : ''} per week
                    </span>
                  </div>
                ) : (
                  <div className="flex items-center">
                    <span className="text-red-500 mr-2">✗</span>
                    <span className="text-gray-500">No scan access</span>
                  </div>
                )}

                {/* Feature List */}
                {plan.features.map((feature, index) => (
                  <div key={index} className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    <span className="text-gray-700 text-sm capitalize">
                      {feature.replace('_', ' ').replace('chatgpt', 'ChatGPT')}
                    </span>
                  </div>
                ))}
                
                {/* Limitations for Free Plan */}
                {plan.limitations && plan.limitations.map((limitation, index) => (
                  <div key={index} className="flex items-center">
                    <span className="text-red-500 mr-2">✗</span>
                    <span className="text-gray-500 text-sm">{limitation}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* CTA Button */}
            <button
              className={`w-full py-3 px-6 rounded-lg font-medium transition-colors ${
                plan.id === 'free'
                  ? 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                  : plan.popular
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-900 text-white hover:bg-gray-800'
              }`}
              onClick={() => {
                if (plan.id === 'free') {
                  alert('Free plan: Dashboard preview only. Upgrade to start scanning!');
                } else {
                  alert(`${plan.name} plan selected! Integration with Paddle coming soon.`);
                }
              }}
            >
              {plan.id === 'free' ? 'Current Plan' : `Choose ${plan.name}`}
            </button>

            {/* Weekly Scan Highlight */}
            {plan.weekly_scans > 0 && (
              <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="text-blue-800 text-xs font-medium text-center">
                  🗓️ Every Monday 11 AM PST
                </div>
                <div className="text-blue-700 text-xs text-center mt-1">
                  Comprehensive weekly insights with 25 AI queries per scan
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* FAQ */}
      <div className="mt-12 bg-white p-8 rounded-xl border border-gray-200">
        <h3 className="text-xl font-bold text-gray-900 mb-6 text-center">Frequently Asked Questions</h3>
        <div className="space-y-4">
          <div>
            <h4 className="font-semibold text-gray-900">When do scans run?</h4>
            <p className="text-gray-600 text-sm mt-1">
              Every Monday at 11 AM PST. You'll receive comprehensive weekly insights with actionable recommendations.
            </p>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900">What's included in early access pricing?</h4>
            <p className="text-gray-600 text-sm mt-1">
              Lock in current pricing for 6 months. After that, Starter becomes $89/month and Pro becomes $149/month.
            </p>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900">Can I upgrade or downgrade anytime?</h4>
            <p className="text-gray-600 text-sm mt-1">
              Yes! Changes take effect at your next billing cycle. Early access pricing will be honored for your 6-month period.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PlansPage;